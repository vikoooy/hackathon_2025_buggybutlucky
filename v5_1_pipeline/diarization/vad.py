from dataclasses import dataclass
from typing import List, Optional

from pyannote.audio import Pipeline
from ..utils import load_audio


@dataclass
class VadSegment:
    start: float
    end: float


def run_vad(audio_path: str, hf_token: Optional[str] = None) -> List[VadSegment]:
    """
    Hochpräziser VAD mit pyannote.
    Dient dazu, reine Sprachbereiche zu markieren.
    """
    token = hf_token or None
    if token is None:
        token = None  # pyannote nutzt ggf. globales HF-Login

    pipeline = Pipeline.from_pretrained("pyannote/voice-activity-detection")

    wav, sr = load_audio(audio_path)
    print(wav)
    print(sr)
    file_dict = {"waveform": wav, "sample_rate": sr}
    print(file_dict)

    vad = pipeline(file_dict)
    segs: List[VadSegment] = []
    for seg in vad.get_timeline():
        segs.append(VadSegment(start=float(seg.start), end=float(seg.end)))
    return segs
