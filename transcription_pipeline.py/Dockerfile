FROM pytorch/pytorch:2.5.1-cuda12.1-cudnn9-runtime

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY pip_requirements.txt .
RUN pip install --no-cache-dir -r pip_requirements.txt
RUN pip install --no-cache-dir fastapi uvicorn python-multipart

# Application code
COPY transcript_diarization_v2.py .
COPY app.py .

# Port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
