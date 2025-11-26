from dataclasses import dataclass
from typing import List, Optional, Dict

import torch
from pyannote.audio import Pipeline
from ..utils import load_audio


@dataclass
class SpeakerSegment:
    start: float
    end: float
    speaker_id: int


def run_coarse_diarization(
    audio_path: str,
    hf_token: Optional[str] = None,
) -> List[SpeakerSegment]:
    """
    Coarse-Diarization mit community-1.
    Dient primär zur Abschätzung der Sprecheranzahl und groben Struktur.
    """
    token = hf_token or None

    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-community-1",
        use_auth_token=token,
    )

    if torch.cuda.is_available():
        pipeline.to(torch.device("cuda"))

    wav, sr = load_audio(audio_path)
    file_dict = {"waveform": wav, "sample_rate": sr}

    result = pipeline(file_dict)
    ann = result.speaker_diarization

    label_to_id: Dict[str, int] = {}
    next_id = 0
    segments: List[SpeakerSegment] = []

    for seg, _, lab in ann.itertracks(yield_label=True):
        if lab not in label_to_id:
            label_to_id[lab] = next_id
            next_id += 1

        segments.append(
            SpeakerSegment(
                start=float(seg.start),
                end=float(seg.end),
                speaker_id=label_to_id[lab],
            )
        )

    segments.sort(key=lambda s: s.start)
    return segments
