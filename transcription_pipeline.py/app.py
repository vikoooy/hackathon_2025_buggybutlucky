"""
FastAPI API Layer for the Transcription Pipeline Service.

Endpoints:
- POST /transcribe: Start a transcription job
- GET /status/{job_id}: Get job status and progress
- GET /result/{job_id}: Get transcription result
"""

import asyncio
import os
import tempfile
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict

from fastapi import FastAPI, File, HTTPException, UploadFile

from transcript_diarization_v2 import (
    align_transcript_with_speakers,
    format_transcript,
    infer_roles,
    load_audio,
    merge_tiny_speakers,
    run_diarization,
    run_transcription,
)

app = FastAPI(
    title="Transcription Pipeline Service",
    description="Speaker diarization and transcription service using Whisper and pyannote",
    version="1.0.0",
)

# In-memory job storage
JOBS: Dict[str, Dict] = {}
JOBS_LOCK = asyncio.Lock()

# Thread pool for CPU-bound transcription work
executor = ThreadPoolExecutor(max_workers=2)


async def _set_job(job_id: str, **fields) -> None:
    """Update job state."""
    async with JOBS_LOCK:
        if job_id in JOBS:
            JOBS[job_id].update(fields)


def _run_pipeline_sync(job_id: str, tmp_path: str) -> None:
    """Synchronous pipeline execution (runs in thread pool)."""
    try:
        # Step 1: Load audio - 10%
        JOBS[job_id]["progress"] = 10
        JOBS[job_id]["step"] = "load"
        audio_path = load_audio(tmp_path)

        # Step 2: Whisper transcription - 20-40%
        JOBS[job_id]["progress"] = 20
        JOBS[job_id]["step"] = "transcription"
        transcription_segments = run_transcription(audio_path, model_name="large-v3")
        JOBS[job_id]["progress"] = 40

        # Step 3: Speaker diarization - 40-70%
        JOBS[job_id]["progress"] = 45
        JOBS[job_id]["step"] = "diarization"
        diarization_segments = run_diarization(audio_path)
        JOBS[job_id]["progress"] = 70

        # Step 4: Alignment - 70-80%
        JOBS[job_id]["progress"] = 75
        JOBS[job_id]["step"] = "alignment"
        utterances = align_transcript_with_speakers(diarization_segments, transcription_segments)
        utterances = merge_tiny_speakers(utterances, min_total_duration=8.0)
        JOBS[job_id]["progress"] = 80

        # Step 5: Role inference - 80-90%
        JOBS[job_id]["progress"] = 85
        JOBS[job_id]["step"] = "roles"
        speaker_roles = infer_roles(utterances)
        JOBS[job_id]["progress"] = 90

        # Step 6: Format output - 90-100%
        JOBS[job_id]["progress"] = 95
        JOBS[job_id]["step"] = "format"
        transcript = format_transcript(utterances, speaker_roles)

        JOBS[job_id]["status"] = "completed"
        JOBS[job_id]["progress"] = 100
        JOBS[job_id]["step"] = "done"
        JOBS[job_id]["result"] = transcript

    except Exception as e:
        JOBS[job_id]["status"] = "failed"
        JOBS[job_id]["error"] = str(e)
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


async def process_audio(job_id: str, tmp_path: str) -> None:
    """Run the transcription pipeline in a thread pool."""
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(executor, _run_pipeline_sync, job_id, tmp_path)


@app.post("/transcribe")
async def start_transcription(file: UploadFile = File(...)):
    """
    Start a transcription job.

    Upload an audio file and receive a job_id to track progress.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required")

    job_id = str(uuid.uuid4())

    # Save audio to temp file
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    async with JOBS_LOCK:
        JOBS[job_id] = {
            "status": "processing",
            "progress": 0,
            "step": "queued",
            "tmp_path": tmp_path,
            "result": None,
            "error": None,
        }

    # Start background processing
    asyncio.create_task(process_audio(job_id, tmp_path))

    return {"job_id": job_id, "status": "processing"}


@app.get("/status/{job_id}")
async def get_status(job_id: str):
    """
    Get the status of a transcription job.

    Returns status, progress percentage, and current step.
    """
    async with JOBS_LOCK:
        if job_id not in JOBS:
            raise HTTPException(status_code=404, detail="Job not found")
        job = JOBS[job_id]

    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job["progress"],
        "step": job.get("step"),
        "error": job.get("error"),
    }


@app.get("/result/{job_id}")
async def get_result(job_id: str):
    """
    Get the transcription result.

    Only available when job status is 'completed'.
    """
    async with JOBS_LOCK:
        if job_id not in JOBS:
            raise HTTPException(status_code=404, detail="Job not found")
        job = JOBS[job_id]

    if job["status"] == "failed":
        raise HTTPException(
            status_code=500,
            detail=f"Job failed: {job.get('error', 'Unknown error')}",
        )

    if job["status"] != "completed":
        raise HTTPException(
            status_code=400,
            detail=f"Job not ready. Current status: {job['status']}, progress: {job['progress']}%",
        )

    return {"job_id": job_id, "transcript": job["result"]}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
