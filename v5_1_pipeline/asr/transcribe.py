import torch
from dataclasses import dataclass
from typing import List
from faster_whisper import WhisperModel
from .whisper_config import WHISPER_CONFIG


@dataclass
class Word:
    start: float
    end: float
    word: str


def run_transcription_words(audio_path: str, model_name: str = "large-v3") -> List[Word]:
    """
    Run Whisper (faster-whisper) with optimized configuration.
    Produces stable, high-quality word-level timestamps.
    """

    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "float32"

    model = WhisperModel(
        model_name,
        device=device,
        compute_type=compute_type
    )

    segments, _ = model.transcribe(
        audio_path,
        **WHISPER_CONFIG
    )

    words: List[Word] = []

    for seg in segments:
        if seg.words is None:
            continue
        for w in seg.words:
            # faster-whisper liefert bereits präzise Start/End-Zeiten
            words.append(
                Word(
                    start=float(w.start),
                    end=float(w.end),
                    word=w.word.strip()
                )
            )

    return words
