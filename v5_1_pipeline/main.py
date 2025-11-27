import argparse
import logging
import os

from .asr.transcribe import run_transcription_words
from .diarization.vad import run_vad
from .diarization.coarse import run_coarse_diarization
from .diarization.embeddings import compute_word_embeddings
from .diarization.clustering import cluster_embeddings_ahc
from .diarization.smoothing import smooth_labels_combined
from .diarization.merge import merge_words_to_utterances
from .text.normalize import normalize_utterances
from .roles.infer import infer_roles
from .utils import fmt_time


def format_output(utts, roles):
    lines = []
    for u in utts:
        ts = fmt_time(u.start)
        role = roles.get(u.speaker_id, "Unknown")
        lines.append(f"{ts} Speaker {u.speaker_id} ({role}): \"{u.text}\"")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="v5.1 transcription + diarization pipeline")
    parser.add_argument("audio", type=str)
    parser.add_argument("-o", "--output", type=str, default=None)
    parser.add_argument("--hf-token", type=str, default="INSERT TOKEN HERE")
    parser.add_argument("--whisper-model", type=str, default="large-v3")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logging.info("Starte v5.1 Pipeline")

    # 1. ASR
    words = run_transcription_words(args.audio, model_name=args.whisper_model)
    logging.info("ASR erzeugte %d Wörter.", len(words))

    # 2. VAD
    vad = run_vad(args.audio, hf_token=args.hf_token)
    logging.info("VAD erzeugte %d Segmente.", len(vad))

    # 3. Coarse diarization
    coarse = run_coarse_diarization(args.audio, hf_token=args.hf_token)
    logging.info("Coarse Diarization -> %d Segmente.", len(coarse))

    # 4. Embeddings
    embs = compute_word_embeddings(words, args.audio)
    logging.info("Embeddings erzeugt: %s", embs.shape)

    # 5. Clustering
    raw_labels = cluster_embeddings_ahc(embs, coarse, words)
    logging.info("Clustering erzeugte %d Labels.", len(raw_labels))

    # 6. Smoothing
    labels = smooth_labels_combined(words, raw_labels)
    logging.info("Labels nach Smoothing stabilisiert.")

    # 7. Merge
    utts = merge_words_to_utterances(words, labels)
    logging.info("Erzeugte %d Utterances.", len(utts))

    # # 8. Normalize
    # utts_norm = normalize_utterances(utts)
    # logging.info("Normalisierung abgeschlossen.")

    # 9. Roles
    # roles = infer_roles(utts_norm)
    roles = infer_roles(utts)
    logging.info("Rollen erkannt: %s", roles)

    # 10. Format Output
    # txt = format_output(utts_norm, roles)
    txt = format_output(utts, roles)

    if args.output:
        with open(args.output, "w", encoding="utf8") as f:
            f.write(txt)
    else:
        print(txt)


if __name__ == "__main__":
    main()
