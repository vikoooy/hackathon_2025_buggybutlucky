import asyncio
import uuid
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

router = APIRouter(
    prefix="/audio",
    tags=["audio"],
    responses={400: {"description": "Invalid audio upload"}},
)

JOBS: Dict[str, Dict] = {}
JOBS_LOCK = asyncio.Lock()


async def _set_job(job_id: str, **fields) -> Dict:
    async with JOBS_LOCK:
        record = JOBS.get(job_id, {"status": "created", "progress": 0})
        record.update(fields)
        JOBS[job_id] = record
        return record


async def _get_job(job_id: str) -> Dict | None:
    async with JOBS_LOCK:
        return JOBS.get(job_id)


async def process_audio_bytes(job_id: str, file_name: str, payload: bytes) -> None:
    try:
        await _set_job(job_id, status="processing", progress=0, filename=file_name)
        # Simulate async processing steps with progress updates.
        for progress in (10, 30, 60, 90, 100):
            await asyncio.sleep(0.2)
            await _set_job(job_id, progress=progress)
        await _set_job(job_id, status="completed", progress=100)
    except Exception as exc:  # pragma: no cover - defensive logging placeholder
        await _set_job(job_id, status="failed", error=str(exc))
    finally:
        # Prevent keeping large payloads around; in real code you'd stream to storage/worker.
        del payload


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
