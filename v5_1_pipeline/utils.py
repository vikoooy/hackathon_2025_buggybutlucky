import torchaudio
import torch

def fmt_time(t: float) -> str:
    h = int(t // 3600)
    m = int((t % 3600) // 60)
    s = int(t % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def load_audio(path: str):
    wav, sr = torchaudio.load(path)
    if wav.size(0) > 1:
        wav = torch.mean(wav, dim=0, keepdim=True)
    return wav, sr
