from typing import List
import numpy as np
from sklearn.cluster import AgglomerativeClustering

from .coarse import SpeakerSegment
from ..asr.transcribe import Word


def estimate_num_speakers(
    coarse_segments: List[SpeakerSegment],
    max_speakers: int = 8,
) -> int:
    if not coarse_segments:
        return 1
    ids = {s.speaker_id for s in coarse_segments}
    n = len(ids)
    n = max(1, min(max_speakers, n))
    return n


def cluster_embeddings_ahc(
    embs: np.ndarray,
    coarse_segments: List[SpeakerSegment],
    words: List[Word],
    max_speakers: int = 8,
) -> np.ndarray:
    """
    Agglomerative Clustering auf ECAPA-Embeddings.
    coarse_segments werden aktuell nur zur Schätzung der Sprecheranzahl genutzt.
    """
    n_spk = estimate_num_speakers(coarse_segments, max_speakers=max_speakers)

    if embs.shape[0] < n_spk:
        # mehr Cluster als Punkte ergibt keinen Sinn
        n_spk = max(1, embs.shape[0])

    model = AgglomerativeClustering(
        n_clusters=n_spk,
        metric="cosine",
        linkage="average",
    )
    labels = model.fit_predict(embs)
    return labels
