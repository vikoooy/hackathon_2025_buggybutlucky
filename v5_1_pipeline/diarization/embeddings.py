from dataclasses import dataclass
from typing import List

import numpy as np
import torch
from speechbrain.pretrained import EncoderClassifier

from ..utils import load_audio
from ..asr.transcribe import Word


@dataclass
class EmbeddingConfig:
    pad_seconds: float = 0.15
    min_duration: float = 0.05  # Sekunden


def _extract_word_audio(
    wav: torch.Tensor,
    sr: int,
    w: Word,
    pad: float,
    min_duration: float,
) -> torch.Tensor:
    start = max(w.start - pad, 0.0)
    end = w.end + pad

    i0 = int(start * sr)
    i1 = int(end * sr)
    chunk = wav[:, i0:i1]

    min_samples = int(min_duration * sr)
    if chunk.size(1) < min_samples:
        # bei extrem kurzen Stücken etwas "auffüllen"
        repeat_factor = int(np.ceil(min_samples / max(1, chunk.size(1))))
        chunk = chunk.repeat(1, repeat_factor)
        chunk = chunk[:, :min_samples]

    return chunk


def compute_word_embeddings(
    words: List[Word],
    audio_path: str,
    config: EmbeddingConfig = EmbeddingConfig(),
) -> np.ndarray:
    """
    ECAPA-TDNN-Embeddings pro Wort.
    Rückgabe: (N_words, emb_dim)
    """
    wav, sr = load_audio(audio_path)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        run_opts={"device": device},
        savedir="ecapa_voxceleb_cache",
    )

    embs = []
    for w in words:
        chunk = _extract_word_audio(
            wav=wav,
            sr=sr,
            w=w,
            pad=config.pad_seconds,
            min_duration=config.min_duration,
        )
        with torch.no_grad():
            emb = classifier.encode_batch(chunk).squeeze().cpu().numpy()
        embs.append(emb)

    return np.vstack(embs)
