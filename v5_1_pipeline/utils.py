import torchaudio
import torch

def fmt_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def load_audio(path: str):
    wav, sr = torchaudio.load(path)

    # Stereo → Mono
    if wav.size(0) > 1:
        wav = torch.mean(wav, dim=0, keepdim=True)

    # Resample falls nötig
    if sr != 16000:
        wav = torchaudio.functional.resample(wav, sr, 16000)
        sr = 16000

    return wav, sr
