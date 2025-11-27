import asyncio
import os
import uuid
from pathlib import Path
from typing import Dict

import httpx
from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from ..services.pipeline_service import PipelineService

# Transcript-Speicherort
TRANSCRIPTS_DIR = Path(__file__).parent.parent.parent / "data" / "transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

router = APIRouter(
    prefix="/audio",
    tags=["audio"],
    responses={400: {"description": "Invalid audio upload"}},
)

# Transcription Service URL (containerized service)
TRANSCRIPTION_SERVICE_URL = os.environ.get("TRANSCRIPTION_SERVICE_URL", "http://localhost:8001")

JOBS: Dict[str, Dict] = {}
JOBS_LOCK = asyncio.Lock()


async def _set_job(job_id: str, **fields) -> Dict:
    async with JOBS_LOCK:
        record = JOBS.get(job_id, {
            "status": "created",
            "progress": 0,
            "phase": "transcription",
            "transcript": None,
            "reports": None,
            "pipeline_error": None
        })
        record.update(fields)
        JOBS[job_id] = record
        return record


async def _get_job(job_id: str) -> Dict | None:
    async with JOBS_LOCK:
        return JOBS.get(job_id)


async def process_audio_bytes(job_id: str, file_name: str, payload: bytes) -> None:
    """Verarbeitet Audio via Transcription Service (HTTP), dann Analysis Pipeline."""

    try:
        # === TRANSKRIPTION VIA HTTP (0-70%) ===
        async with httpx.AsyncClient(timeout=httpx.Timeout(600.0, connect=30.0)) as client:
            # 1. Job beim Transcription Service starten
            await _set_job(
                job_id,
                status="processing",
                progress=2,
                step="upload",
                step_name="Sende an Transcription Service...",
                phase="transcription"
            )

            files = {"file": (file_name, payload, "audio/wav")}
            try:
                response = await client.post(
                    f"{TRANSCRIPTION_SERVICE_URL}/transcribe",
                    files=files
                )
                response.raise_for_status()
            except httpx.ConnectError:
                raise Exception(f"Transcription Service nicht erreichbar: {TRANSCRIPTION_SERVICE_URL}")
            except httpx.HTTPStatusError as e:
                raise Exception(f"Transcription Service Fehler: {e.response.text}")

            transcription_job_id = response.json()["job_id"]

            await _set_job(
                job_id,
                progress=5,
                step="transcription_started",
                step_name="Transcription gestartet..."
            )

            # 2. Status pollen bis fertig
            while True:
                await asyncio.sleep(2)

                try:
                    status_response = await client.get(
                        f"{TRANSCRIPTION_SERVICE_URL}/status/{transcription_job_id}"
                    )
                    status_response.raise_for_status()
                except httpx.HTTPStatusError:
                    raise Exception("Fehler beim Abrufen des Transcription-Status")

                status_data = status_response.json()

                # Progress weiterleiten (0-70% für Transcription)
                transcription_progress = status_data.get("progress", 0)
                overall_progress = int(transcription_progress * 0.7)

                step_name_map = {
                    "load": "Audio wird geladen...",
                    "transcription": "Whisper Transkription läuft...",
                    "diarization": "Speaker Diarization...",
                    "alignment": "Alignment...",
                    "roles": "Erkenne Rollen...",
                    "format": "Formatiere Transkript...",
                    "done": "Transkription abgeschlossen",
                }
                current_step = status_data.get("step", "processing")
                step_name = step_name_map.get(current_step, f"Verarbeite... ({current_step})")

                await _set_job(
                    job_id,
                    progress=overall_progress,
                    step=f"transcription_{current_step}",
                    step_name=step_name
                )

                if status_data["status"] == "completed":
                    break
                elif status_data["status"] == "failed":
                    error_msg = status_data.get("error", "Transcription fehlgeschlagen")
                    raise Exception(error_msg)

            # 3. Ergebnis holen
            try:
                result_response = await client.get(
                    f"{TRANSCRIPTION_SERVICE_URL}/result/{transcription_job_id}"
                )
                result_response.raise_for_status()
            except httpx.HTTPStatusError as e:
                raise Exception(f"Fehler beim Abrufen des Transkripts: {e.response.text}")

            transcript = result_response.json()["transcript"]

        # Transcript als Datei speichern
        transcript_path = TRANSCRIPTS_DIR / f"{job_id}.txt"
        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write(transcript)

        await _set_job(
            job_id,
            progress=70,
            step="transcription_done",
            step_name="Transkription abgeschlossen",
            phase="analysis",
            transcript=transcript,
            transcript_path=str(transcript_path)
        )

        # === DATA PROCESSING PIPELINE (70-100%) ===
        try:
            pipeline = PipelineService()

            async def progress_update(pct: int, step: str, name: str):
                await _set_job(job_id, progress=pct, step=step, step_name=name)

            reports = await pipeline.run_pipeline(transcript, progress_update)

            # Check for partial failures
            has_errors = bool(reports.get("errors"))
            status = "partial_success" if has_errors else "completed"

            await _set_job(
                job_id,
                status=status,
                progress=100,
                step="done",
                step_name="Fertig",
                result=transcript,
                reports=reports,
                pipeline_error="; ".join(reports.get("errors", [])) if has_errors else None
            )

        except Exception as pipeline_exc:
            # Pipeline failed but transcript succeeded
            await _set_job(
                job_id,
                status="partial_success",
                progress=100,
                step="pipeline_failed",
                step_name="Pipeline fehlgeschlagen",
                result=transcript,
                pipeline_error=str(pipeline_exc)
            )

    except Exception as exc:
        await _set_job(job_id, status="failed", error=str(exc))


@router.post("/upload")
async def upload_audio(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")
    if file.content_type and not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="File must be an audio type")

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    job_id = str(uuid.uuid4())
    await _set_job(job_id, status="queued", progress=0, filename=file.filename)
    background_tasks.add_task(process_audio_bytes, job_id, file.filename, payload)
    return {"status": "accepted", "job_id": job_id, "filename": file.filename}


@router.get("/progress/{job_id}")
async def get_audio_progress(job_id: str):
    job = await _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.get("/report/{job_id}")
async def get_report(job_id: str):
    """Get the generated reports for a completed job."""
    job = await _get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] not in ["completed", "partial_success"]:
        raise HTTPException(
            status_code=400,
            detail=f"Job not ready. Current status: {job['status']}"
        )

    return {
        "job_id": job_id,
        "status": job["status"],
        "transcript": job.get("result"),
        "transcript_path": job.get("transcript_path"),
        "reports": job.get("reports"),
        "pipeline_error": job.get("pipeline_error")
    }


@router.get("/transcript/{job_id}")
async def download_transcript(job_id: str):
    """Download transcript as .txt file."""
    transcript_path = TRANSCRIPTS_DIR / f"{job_id}.txt"
    if not transcript_path.exists():
        raise HTTPException(status_code=404, detail="Transcript not found")
    return FileResponse(
        transcript_path,
        media_type="text/plain",
        filename=f"transcript_{job_id}.txt"
    )
