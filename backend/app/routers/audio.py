import asyncio
import os
import tempfile
import uuid
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile

# v5_1_pipeline imports
from v5_1_pipeline.asr.transcribe import run_transcription_words
from v5_1_pipeline.diarization.vad import run_vad
from v5_1_pipeline.diarization.coarse import run_coarse_diarization
from v5_1_pipeline.diarization.embeddings import compute_word_embeddings
from v5_1_pipeline.diarization.clustering import cluster_embeddings_ahc
from v5_1_pipeline.diarization.smoothing import smooth_labels_combined
from v5_1_pipeline.diarization.merge import merge_words_to_utterances
from v5_1_pipeline.text.normalize import normalize_utterances
from v5_1_pipeline.roles.infer import infer_roles
from v5_1_pipeline.utils import fmt_time

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


def _format_output(utts, roles):
    """Formatiert die Utterances als lesbaren Text mit Timestamps und Rollen."""
    lines = []
    for u in utts:
        ts = fmt_time(u.start)
        role = roles.get(u.speaker_id, "Unknown")
        lines.append(f"{ts} Speaker {u.speaker_id} ({role}): \"{u.text}\"")
    return "\n".join(lines)


async def process_audio_bytes(job_id: str, file_name: str, payload: bytes) -> None:
    """Verarbeitet Audio-Bytes durch die v5_1_pipeline mit Progress-Updates."""
    tmp_path = None
    hf_token = os.environ.get("HF_TOKEN")

    try:
        # Temporäre Datei erstellen
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(payload)
            tmp_path = tmp.name

        # Step 1: ASR (Whisper Transkription)
        await _set_job(job_id, status="processing", progress=10, step="asr", step_name="Transkription läuft...")
        words = run_transcription_words(tmp_path, model_name="large-v3")

        # Step 2: VAD (Voice Activity Detection)
        await _set_job(job_id, progress=20, step="vad", step_name="Voice Activity Detection...")
        vad_segments = run_vad(tmp_path, hf_token=hf_token)

        # Step 3: Coarse Speaker Diarization
        await _set_job(job_id, progress=30, step="diarization", step_name="Speaker Diarization...")
        coarse_segments = run_coarse_diarization(tmp_path, hf_token=hf_token)

        # Step 4: Word Embeddings berechnen
        await _set_job(job_id, progress=45, step="embeddings", step_name="Berechne Speaker Embeddings...")
        embeddings = compute_word_embeddings(words, tmp_path)

        # Step 5: Clustering
        await _set_job(job_id, progress=55, step="clustering", step_name="Clustering Sprecher...")
        raw_labels = cluster_embeddings_ahc(embeddings, coarse_segments, words)

        # Step 6: Label Smoothing
        await _set_job(job_id, progress=65, step="smoothing", step_name="Label Smoothing...")
        labels = smooth_labels_combined(words, raw_labels)

        # Step 7: Merge Words to Utterances
        await _set_job(job_id, progress=75, step="merge", step_name="Erstelle Utterances...")
        utterances = merge_words_to_utterances(words, labels)

        # Step 8: Text Normalization
        await _set_job(job_id, progress=85, step="normalize", step_name="Normalisiere Text...")
        normalized_utterances = normalize_utterances(utterances)

        # Step 9: Role Inference
        await _set_job(job_id, progress=95, step="roles", step_name="Erkenne Rollen...")
        roles = infer_roles(normalized_utterances)

        # Step 10: Format Output
        result = _format_output(normalized_utterances, roles)

        await _set_job(
            job_id,
            status="completed",
            progress=100,
            step="done",
            step_name="Fertig",
            result=result
        )

    except Exception as exc:
        await _set_job(job_id, status="failed", error=str(exc))
    finally:
        # Temporäre Datei löschen
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        # Payload freigeben
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
