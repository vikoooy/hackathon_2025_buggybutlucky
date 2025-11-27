from typing import List
import numpy as np

from ..asr.transcribe import Word


def smooth_labels_majority(labels: np.ndarray, window: int = 5) -> np.ndarray:
    """
    Mehrheitsfilter über ein gleitendes Fenster.
    """
    out = labels.copy()
    n = len(labels)
    for i in range(n):
        lo = max(0, i - window)
        hi = min(n, i + window + 1)
        vals = labels[lo:hi]
        out[i] = np.bincount(vals).argmax()
    return out


def smooth_labels_isolated(words: List[Word], labels: np.ndarray) -> np.ndarray:
    """
    Entfernt isolierte Fehl-Labels:
    Wenn prev == next != current, setze current auf prev.
    """
    out = labels.copy()
    n = len(labels)

    for i in range(1, n - 1):
        prev_label = labels[i - 1]
        curr_label = labels[i]
        next_label = labels[i + 1]

        if prev_label == next_label != curr_label:
            out[i] = prev_label

    return out


def smooth_labels_combined(
    words: List[Word],
    labels: np.ndarray,
    majority_window: int = 5,
) -> np.ndarray:
    lab = smooth_labels_majority(labels, window=majority_window)
    lab = smooth_labels_isolated(words, lab)
    return lab
