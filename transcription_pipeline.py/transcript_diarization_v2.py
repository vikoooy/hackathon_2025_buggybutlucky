#!/usr/bin/env python3
"""
transcript_diarization_community1.py

End-to-end script for:
1. Transcribing a long multi-speaker audio file with Whisper.
2. Performing speaker diarization with pyannote `community-1`.
3. Inferring roles: Moderator, Team Red, Team Blue, Unknown.
4. Emitting a structured, time-stamped transcript (one utterance per line).

USAGE (stdout):
    python transcript_diarization_community1.py input.mp3 --num-speakers 3 > transcript.txt

USAGE (output file):
    python transcript_diarization_community1.py input.mp3 --num-speakers 3 -o transcript.txt

Environment:
    - Requires a Hugging Face access token with access to
      `pyannote/speaker-diarization-community-1`, stored in one of:
        HUGGINGFACE_TOKEN, HF_TOKEN, or PYANNOTE_AUDIO_TOKEN.
    - Requires ffmpeg on the system PATH.

License notes:
    - Whisper: MIT (code + weights).
    - pyannote.audio: MIT (library).
    - pyannote/speaker-diarization-community-1: CC BY 4.0 (attribution required).
"""

import argparse
import logging
import math
import os
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np  # pyannote.audio 4.x expects NumPy >= 1.23; NumPy 2.x is fine.

# ASR (Whisper)
try:
    import whisper
except ImportError as exc:  # pragma: no cover
    print(
        "Error: The 'openai-whisper' package is not installed.\n"
        "Install it with:\n"
        "    pip install openai-whisper\n",
        file=sys.stderr,
    )
    raise

# Diarization (pyannote.audio 4.x + community-1)
try:
    from pyannote.audio import Pipeline
except ImportError as exc:  # pragma: no cover
    print(
        "Error: The 'pyannote.audio' package is not installed.\n"
        "Install it with:\n"
        "    pip install pyannote.audio\n",
        file=sys.stderr,
    )
    raise

# Audio-Loading für community-1
try:
    import torchaudio
except ImportError:
    print(
        "Error: 'torchaudio' ist nicht installiert.\n"
        "Installiere es im aktuellen Environment z.B. mit:\n"
        "    pip install torchaudio\n",
        file=sys.stderr,
    )
    raise


# -------------------------------------------------------------------------
# Data classes
# -------------------------------------------------------------------------
@dataclass
class SpeakerSegment:
    start: float
    end: float
    speaker_id: int


@dataclass
class TranscriptSegment:
    start: float
    end: float
    text: str


@dataclass
class Utterance:
    start: float
    end: Optional[float]
    speaker_id: int
    text: str


# -------------------------------------------------------------------------
# Utility functions
# -------------------------------------------------------------------------
def format_time(seconds: float, force_hours: bool) -> str:
    total_seconds = int(round(seconds))
    if total_seconds < 0:
        total_seconds = 0
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    if force_hours or hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def compute_overlap(a_start: float, a_end: float, b_start: float, b_end: float) -> float:
    start = max(a_start, b_start)
    end = min(a_end, b_end)
    return max(0.0, end - start)


# -------------------------------------------------------------------------
# 1. load_audio
# -------------------------------------------------------------------------
def load_audio(path: str) -> str:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Audio file not found: {path}")
    supported_ext = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".opus"}
    ext = os.path.splitext(path)[1].lower()
    if ext not in supported_ext:
        logging.warning(
            "Extension '%s' not in typical supported set %s. "
            "If ffmpeg supports it, Whisper/pyannote will likely work anyway.",
            ext,
            supported_ext,
        )
    return path


# -------------------------------------------------------------------------
# 2. run_diarization — community-1 with optional num_speakers
# -------------------------------------------------------------------------
def _get_hf_token() -> str:
    token = (
        os.getenv("HUGGINGFACE_TOKEN")
        or os.getenv("HF_TOKEN")
        or os.getenv("PYANNOTE_AUDIO_TOKEN")
    )
    if not token:
        raise RuntimeError(
            "No Hugging Face token found. Set one of HUGGINGFACE_TOKEN, HF_TOKEN, "
            "or PYANNOTE_AUDIO_TOKEN.\n"
            "Steps:\n"
            "  1) Accept conditions for pyannote/speaker-diarization-community-1 on Hugging Face.\n"
            "  2) Create an access token at https://huggingface.co/settings/tokens (scopes: read).\n"
            "  3) Export it, e.g.:\n"
            "       export HUGGINGFACE_TOKEN=hf_xxx\n"
        )
    return token


def run_diarization(
    audio_path: str,
    num_speakers: Optional[int] = None,
    min_speakers: Optional[int] = None,
    max_speakers: Optional[int] = None,
    use_exclusive: bool = True,
) -> List[SpeakerSegment]:
    """
    Run speaker diarization using pyannote `community-1`.

    Parameters
    ----------
    audio_path : str
    num_speakers : Optional[int]
        If set, fix the number of speakers.
    min_speakers, max_speakers : Optional[int]
        If set, constrain the number of speakers.
    use_exclusive : bool
        If True, use `output.exclusive_speaker_diarization` when available.

    Returns
    -------
    List[SpeakerSegment]
    """
    logging.info("Running Community-1 speaker diarization on '%s'...", audio_path)

    token = _get_hf_token()
    pipeline = Pipeline.from_pretrained(
        "pyannote/speaker-diarization-community-1", token=token
    )

    kwargs = {}
    if num_speakers is not None:
        kwargs["num_speakers"] = num_speakers
    if min_speakers is not None:
        kwargs["min_speakers"] = min_speakers
    if max_speakers is not None:
        kwargs["max_speakers"] = max_speakers

    # Audio einmal komplett laden (Community-1 Model-Card zeigt dieses Muster)
    waveform, sample_rate = torchaudio.load(audio_path)

    # An Pipeline übergeben
    file_dict = {"waveform": waveform, "sample_rate": sample_rate}
    output = pipeline(file_dict, **kwargs)

    # Exclusive diarization bevorzugen
    if use_exclusive and hasattr(output, "exclusive_speaker_diarization"):
        annotation = output.exclusive_speaker_diarization
    else:
        annotation = output.speaker_diarization

    speaker_label_to_id: Dict[str, int] = {}
    segments: List[SpeakerSegment] = []

    # Annotation.itertracks(yield_label=True) -> (segment, track, label)
    for segment, _, speaker_label in annotation.itertracks(yield_label=True):
        if speaker_label not in speaker_label_to_id:
            speaker_label_to_id[speaker_label] = len(speaker_label_to_id)
        speaker_id = speaker_label_to_id[speaker_label]
        segments.append(
            SpeakerSegment(start=float(segment.start), end=float(segment.end), speaker_id=speaker_id)
        )

    segments.sort(key=lambda s: s.start)
    logging.info(
        "Diarization produced %d segments, %d unique speakers (after mapping).",
        len(segments),
        len(speaker_label_to_id),
    )
    return segments


# -------------------------------------------------------------------------
# 3. run_transcription — Whisper (default: large-v3 if available)
# -------------------------------------------------------------------------
def run_transcription(
    audio_path: str,
    model_name: str = "large-v3",
) -> List[TranscriptSegment]:
    """
    Run Whisper transcription.

    Parameters
    ----------
    audio_path : str
    model_name : str
        Whisper model name: tiny, base, small, medium, large, large-v2, large-v3, ...

    Returns
    -------
    List[TranscriptSegment]
    """
    logging.info("Loading Whisper model '%s'...", model_name)
    model = whisper.load_model(model_name)

    logging.info("Running transcription on '%s'...", audio_path)
    # fp16=False ensures CPU compatibility; set True manually for GPU with float16.
    result = model.transcribe(audio_path, verbose=False, fp16=False)

    segments: List[TranscriptSegment] = []
    for seg in result.get("segments", []):
        segments.append(
            TranscriptSegment(
                start=float(seg["start"]),
                end=float(seg["end"]),
                text=str(seg["text"]).strip(),
            )
        )

    logging.info("Transcription produced %d segments.", len(segments))
    return segments


# -------------------------------------------------------------------------
# 4. align_transcript_with_speakers
# -------------------------------------------------------------------------
def align_transcript_with_speakers(
    diarization_segments: List[SpeakerSegment],
    transcription_segments: List[TranscriptSegment],
) -> List[Utterance]:
    """
    Assign each transcription segment to a speaker using overlap with diarization.

    Strategy:
        For each ASR segment, compute overlap with diarization segments
        and pick the speaker with maximum overlap. If no overlap, fall back
        to previous speaker, else speaker 0.

    Returns
    -------
    List[Utterance]
    """
    logging.info("Aligning ASR segments with diarization...")

    utterances: List[Utterance] = []

    if not transcription_segments:
        logging.warning("No transcription segments found.")
        return utterances

    if not diarization_segments:
        logging.warning("No diarization segments; assigning all text to Speaker 0.")
        for ts in transcription_segments:
            utterances.append(
                Utterance(
                    start=ts.start,
                    end=ts.end,
                    speaker_id=0,
                    text=ts.text,
                )
            )
        return utterances

    diar = diarization_segments
    diar_index = 0
    previous_speaker: Optional[int] = None

    for ts in transcription_segments:
        best_speaker: Optional[int] = None
        best_overlap = 0.0

        while diar_index < len(diar) and diar[diar_index].end <= ts.start:
            diar_index += 1

        j = diar_index
        while j < len(diar) and diar[j].start < ts.end:
            overlap = compute_overlap(ts.start, ts.end, diar[j].start, diar[j].end)
            if overlap > best_overlap:
                best_overlap = overlap
                best_speaker = diar[j].speaker_id
            j += 1

        if best_speaker is None:
            best_speaker = previous_speaker if previous_speaker is not None else 0

        previous_speaker = best_speaker

        utterances.append(
            Utterance(
                start=ts.start,
                end=ts.end,
                speaker_id=best_speaker,
                text=ts.text,
            )
        )

    logging.info("Alignment produced %d utterances.", len(utterances))
    return utterances


# -------------------------------------------------------------------------
# 4b. Optional cleanup: merge tiny speakers
# -------------------------------------------------------------------------
def merge_tiny_speakers(
    utterances: List[Utterance],
    min_total_duration: float = 8.0,
) -> List[Utterance]:
    """
    Heuristic: speakers with total talking time < min_total_duration
    are likely spurious clusters. Merge them into neighbors.

    Returns
    -------
    List[Utterance]
        New utterance list with tiny speakers merged.
    """
    if not utterances:
        return utterances

    from collections import defaultdict

    durations = defaultdict(float)
    for u in utterances:
        if u.end is not None:
            durations[u.speaker_id] += max(0.0, u.end - u.start)

    tiny_speakers = {sid for sid, d in durations.items() if d < min_total_duration}
    if not tiny_speakers:
        return utterances

    logging.info(
        "Merging %d tiny speaker(s) with total duration < %.1fs.",
        len(tiny_speakers),
        min_total_duration,
    )

    merged: List[Utterance] = []
    for i, u in enumerate(utterances):
        if u.speaker_id in tiny_speakers:
            prev_spk = utterances[i - 1].speaker_id if i > 0 else None
            next_spk = utterances[i + 1].speaker_id if i + 1 < len(utterances) else None
            new_spk = None
            if prev_spk is not None and prev_spk == next_spk:
                new_spk = prev_spk
            else:
                new_spk = prev_spk if prev_spk is not None else next_spk
            if new_spk is not None:
                u = Utterance(u.start, u.end, new_spk, u.text)
        merged.append(u)
    return merged


# -------------------------------------------------------------------------
# 5. infer_roles
# -------------------------------------------------------------------------
def infer_roles(utterances: List[Utterance]) -> Dict[int, str]:
    """
    Infer Moderator / Team Red / Team Blue / Unknown for each speaker.
    """
    roles: Dict[int, str] = {}
    if not utterances:
        return roles

    speaker_texts: Dict[int, List[str]] = {}
    speaker_first_start: Dict[int, float] = {}
    speaker_durations: Dict[int, float] = {}

    for u in utterances:
        speaker_texts.setdefault(u.speaker_id, []).append(u.text)
        if u.speaker_id not in speaker_first_start:
            speaker_first_start[u.speaker_id] = u.start
        if u.end is not None:
            speaker_durations[u.speaker_id] = speaker_durations.get(u.speaker_id, 0.0) + max(
                0.0, u.end - u.start
            )

    team_red_keywords = ["Gegner", "red team"]
    team_blue_keywords = ["abzuwehren", "abwehren", "blue team"]
    speaker_team_votes: Dict[int, Dict[str, int]] = {}

    for sid, texts in speaker_texts.items():
        votes = {"Team Red": 0, "Team Blue": 0}
        for txt in texts:
            t = txt.lower()
            if any(kw in t for kw in team_red_keywords):
                votes["Team Red"] += 1
            if any(kw in t for kw in team_blue_keywords):
                votes["Team Blue"] += 1
        speaker_team_votes[sid] = votes

    for sid, votes in speaker_team_votes.items():
        red_votes = votes["Team Red"]
        blue_votes = votes["Team Blue"]
        if red_votes > 0 or blue_votes > 0:
            if red_votes > blue_votes:
                roles[sid] = "Team Red"
            elif blue_votes > red_votes:
                roles[sid] = "Team Blue"
            else:
                roles[sid] = "Unknown"

    greeting_keywords = [
        # Allgemeine Begrüßungen
        "hallo",
        "guten morgen",
        "guten abend",
        "guten tag",
        "guten nachmittag",
        "herzlich willkommen",
        "willkommen",

        # Moderator-Signale
        "ich werde heute moderieren",
        "ich bin heute ihr moderator",
        "ich bin heute eure moderatorin",
        "ich moderiere heute",
        "als moderator",
        "als moderatorin",
        "ich werde sie durch die sendung führen",
        "ich führe durch die diskussion",
        "ich leite die diskussion",

        # Sitzungseröffnung
        "heute sprechen wir über",
        "heute diskutieren wir",
        "in dieser runde",
        "in der heutigen diskussion",
        "in unserem heutigen gespräch",

        # Einführung / Agenda
        "bevor wir anfangen",
        "lassen sie uns beginnen",
        "starten wir",
    ]

    candidate_speakers = [
        s for s in speaker_texts.keys() if roles.get(s, "Unknown") not in ("Team Red", "Team Blue")
    ]
    moderator_candidate_scores: Dict[int, float] = {}

    early_utterances = sorted(utterances, key=lambda u: u.start)[:20]
    for u in early_utterances:
        if u.speaker_id not in candidate_speakers:
            continue
        t = u.text.lower()
        score = 0.0
        if any(kw in t for kw in greeting_keywords):
            score += 2.0
        score += max(0.0, 1.0 - (u.start / 600.0))
        moderator_candidate_scores[u.speaker_id] = (
            moderator_candidate_scores.get(u.speaker_id, 0.0) + score
        )

    moderator_id: Optional[int] = None
    if moderator_candidate_scores:
        moderator_id = max(moderator_candidate_scores.items(), key=lambda kv: kv[1])[0]
    elif candidate_speakers:
        candidate_speakers.sort(key=lambda s: speaker_first_start.get(s, math.inf))
        moderator_id = candidate_speakers[0]

    if moderator_id is not None:
        roles[moderator_id] = "Moderator"

    for sid in speaker_texts.keys():
        if sid not in roles:
            roles[sid] = "Unknown"

    return roles


# -------------------------------------------------------------------------
# 6. format_transcript
# -------------------------------------------------------------------------
def format_transcript(utterances: List[Utterance], speaker_roles: Dict[int, str]) -> str:
    if not utterances:
        return ""

    utterances_sorted = sorted(utterances, key=lambda u: u.start)
    max_time = max(
        (u.end if u.end is not None else u.start) for u in utterances_sorted
    )
    use_hours = max_time >= 3600.0

    lines: List[str] = []
    for u in utterances_sorted:
        start_str = format_time(u.start, force_hours=use_hours)
        if u.end is not None and u.end > u.start + 0.01:
            end_str = format_time(u.end, force_hours=use_hours)
            time_part = f"{start_str}–{end_str} "
        else:
            time_part = f"{start_str} "

        speaker_label = f"Speaker {u.speaker_id}"
        role = speaker_roles.get(u.speaker_id)
        if role and role != "Unknown":
            speaker_str = f"{speaker_label} ({role})"
        else:
            speaker_str = speaker_label

        text_escaped = u.text.replace('"', '\\"')
        lines.append(f"{time_part}{speaker_str}: \"{text_escaped}\"")

    return "\n".join(lines)


# -------------------------------------------------------------------------
# 7. CLI
# -------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Transcription + Community-1 speaker diarization + role inference."
    )
    parser.add_argument(
        "audio_path",
        type=str,
        help="Path to input audio file (e.g., input.mp3).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        help="Optional path to output text file. If omitted, prints to stdout.",
    )
    parser.add_argument(
        "--whisper-model",
        type=str,
        default="large-v3",
        help="Whisper model name (e.g. tiny, base, small, medium, large, large-v2, large-v3).",
    )
    parser.add_argument(
        "--num-speakers",
        type=int,
        default=None,
        help="Known total number of speakers (fixed). If unset, Community-1 will estimate.",
    )
    parser.add_argument(
        "--min-speakers",
        type=int,
        default=None,
        help="Lower bound on number of speakers.",
    )
    parser.add_argument(
        "--max-speakers",
        type=int,
        default=None,
        help="Upper bound on number of speakers.",
    )
    parser.add_argument(
        "--no-exclusive",
        action="store_true",
        help="Disable exclusive diarization; use regular speaker_diarization instead.",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Logging level (DEBUG, INFO, WARNING, ERROR). Default: INFO.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="[%(levelname)s] %(message)s",
    )

    try:
        audio_path = load_audio(args.audio_path)
    except Exception as exc:
        logging.error("Error loading audio: %s", exc)
        sys.exit(1)

    try:
        diarization_segments = run_diarization(
            audio_path,
            num_speakers=args.num_speakers,
            min_speakers=args.min_speakers,
            max_speakers=args.max_speakers,
            use_exclusive=not args.no_exclusive,
        )
    except Exception as exc:
        logging.error("Error during diarization: %s", exc)
        sys.exit(1)

    try:
        transcription_segments = run_transcription(
            audio_path, model_name=args.whisper_model
        )
    except Exception as exc:
        logging.error("Error during transcription: %s", exc)
        sys.exit(1)

    try:
        utterances = align_transcript_with_speakers(
            diarization_segments, transcription_segments
        )
        utterances = merge_tiny_speakers(utterances, min_total_duration=8.0)
    except Exception as exc:
        logging.error("Error aligning diarization with transcription: %s", exc)
        sys.exit(1)

    try:
        speaker_roles = infer_roles(utterances)
    except Exception as exc:
        logging.error("Error inferring roles: %s", exc)
        sys.exit(1)

    try:
        transcript_text = format_transcript(utterances, speaker_roles)
    except Exception as exc:
        logging.error("Error formatting transcript: %s", exc)
        sys.exit(1)

    if args.output:
        try:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(transcript_text)
            logging.info("Transcript written to '%s'.", args.output)
        except Exception as exc:
            logging.error("Failed to write output file '%s': %s", args.output, exc)
            sys.exit(1)
    else:
        print(transcript_text)


if __name__ == "__main__":
    main()


# =============================================================================
# Installation / Environment (best-practice, Linux / macOS, Python 3.10+)
# =============================================================================
#
# 0) System dependencies (ffmpeg)
#    Debian/Ubuntu:
#        sudo apt-get update
#        sudo apt-get install -y ffmpeg
#    macOS (Homebrew):
#        brew install ffmpeg
#
# 1) Neue virtuelle Umgebung
#
#    python3 -m venv diar_env
#    source diar_env/bin/activate
#    python -m pip install --upgrade pip
#
# 2) Python-Pakete
#
#    pip install pyannote.audio openai-whisper
#
#    (pyannote.audio installiert automatisch eine kompatible PyTorch-Version.
#     Wenn du eine GPU-spezifische Torch-Build brauchst, folge stattdessen
#     der offiziellen PyTorch-Anleitung und installiere pyannote.audio danach.)
#
# 3) Hugging-Face-Token einrichten (für Community-1)
#
#    a) Auf Hugging Face einloggen.
#    b) Model Card lesen und Bedingungen akzeptieren:
#         https://huggingface.co/pyannote/speaker-diarization-community-1
#    c) Access Token erzeugen:
#         https://huggingface.co/settings/tokens
#       Scope: "read" reicht.
#    d) Token in der Shell setzen:
#
#         export HUGGINGFACE_TOKEN=hf_xxxxxxxxxxxxxxxxx
#
#       Alternativ: HF_TOKEN oder PYANNOTE_AUDIO_TOKEN verwenden.
#
# 4) Skript ausführen
#
#    a) Einfacher Lauf, automatische Sprecherzahl:
#
#         python transcript_diarization_community1.py input.mp3
#
#    b) Sprecherzahl ist bekannt (empfohlen in deinem Szenario mit 3 Personen):
#
#         python transcript_diarization_community1.py input.mp3 \
#             --num-speakers 3 \
#             -o transcript.txt
#
#    c) Anderes Whisper-Modell:
#
#         python transcript_diarization_community1.py input.mp3 \
#             --whisper-model medium
#
# =============================================================================
# Mittelfristig: Embedding-basiertes Merge ähnlicher Sprecher (Skizze)
# =============================================================================
#
# Ziel:
#   - Fälle reduzieren, in denen zwei reale Personen (z.B. die beiden Männer)
#     als unterschiedliche Speaker-IDs erscheinen oder gelegentlich vertauscht werden.
#
# Grundidee:
#   1. Für jede Utterance ein Speaker-Embedding extrahieren, z.B. mit
#      pyannote/wespeaker-voxceleb-resnet34-LM (CC BY 4.0, d.h. kompatibel). [1]
#   2. Für jeden Speaker-ID den Mittelwert der Embeddings bilden.
#   3. Kosinus-Ähnlichkeit zwischen allen Speaker-Mittelwerten berechnen.
#   4. Paare mit hoher Ähnlichkeit (z.B. cosine_sim > 0.9) als "gleicher Sprecher"
#      betrachten und deren IDs zusammenführen.
#
# Skizze (nicht angeschlossen, aber auf Basis pyannote.audio 4.x lauffähig
# nach Ergänzung der Imports und Fehlerbehandlung):
#
#    from pyannote.audio import Model, Inference
#    from pyannote.core import Segment
#    from scipy.spatial.distance import cdist
#
#    def merge_similar_speakers_by_embedding(
#        utterances: List[Utterance],
#        audio_path: str,
#        similarity_threshold: float = 0.9,
#    ) -> List[Utterance]:
#        # 1) Embedding-Modell laden
#        model = Model.from_pretrained("pyannote/wespeaker-voxceleb-resnet34-LM")
#        infer = Inference(model, window="whole")  # oder sliding window
#
#        # 2) Pro Utterance ein Embedding
#        emb_per_utt = []
#        for u in utterances:
#            seg = Segment(u.start, u.end if u.end is not None else u.start + 0.5)
#            emb = infer.crop(audio_path, seg)  # (1, D) numpy array
#            emb_per_utt.append(emb[0])
#
#        emb_per_utt = np.stack(emb_per_utt, axis=0)  # (N, D)
#
#        # 3) Mittel-Embedding pro Speaker
#        speaker_ids = sorted({u.speaker_id for u in utterances})
#        speaker_to_indices = {sid: [] for sid in speaker_ids}
#        for idx, u in enumerate(utterances):
#            speaker_to_indices[u.speaker_id].append(idx)
#
#        speaker_embs = []
#        for sid in speaker_ids:
#            idxs = speaker_to_indices[sid]
#            speaker_embs.append(np.mean(emb_per_utt[idxs], axis=0))
#        speaker_embs = np.stack(speaker_embs, axis=0)  # (S, D)
#
#        # 4) Kosinus-Ähnlichkeit
#        dist = cdist(speaker_embs, speaker_embs, metric="cosine")  # (S, S)
#        sim = 1.0 - dist
#
#        # 5) Sehr ähnliche Speaker mergen (Union-Find oder einfache Heuristik)
#        #    Beispiel: alle Paare (i, j) mit sim[i, j] > threshold in dieselbe Gruppe.
#
#        # 6) Mapping alter -> neuer Speaker-IDs erzeugen und Utterances updaten.
#
# Hinweis: Für produktiven Einsatz solltest du:
#   - Ein Union-Find / Connected-Components-Clustering benutzen, damit
#     auch transitive Ähnlichkeit sauber gehandhabt wird.
#   - Einen minimalen Gesprächsanteil pro Speaker erzwingen, damit der Moderator
#     nicht irrtümlich mit einem Gast zusammengelegt wird.
#
# [1] Wespeaker-Modell/Wrapper:
#     https://huggingface.co/pyannote/wespeaker-voxceleb-resnet34-LM
#
# =============================================================================
