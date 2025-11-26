from dataclasses import dataclass
from typing import List

import numpy as np

from ..asr.transcribe import Word


@dataclass
class Utterance:
    start: float
    end: float
    speaker_id: int
    text: str


SHORT_WORDS = {"ja", "nein", "okay", "ok", "gut", "sehr"}


def merge_words_to_utterances(
    words: List[Word],
    labels: np.ndarray,
    base_pause: float = 0.8,
) -> List[Utterance]:
    """
    Merged wortweise Speakerlabels in sinnvolle Sprecher-Turns.
    Dynamische Pause: kurze Turns schließen schneller, lange langsamer.
    """
    if not words:
        return []

    utts: List[Utterance] = []
    cur = Utterance(
        start=words[0].start,
        end=words[0].end,
        speaker_id=int(labels[0]),
        text=words[0].word,
    )

    for i in range(1, len(words)):
        w = words[i]
        spk = int(labels[i])

        pause = w.start - cur.end
        cur_word_count = len(cur.text.split())

        # dynamische Pause anpassen
        dynamic_pause = base_pause
        if cur_word_count <= 3:
            dynamic_pause = 0.4
        if cur_word_count <= 1:
            dynamic_pause = 0.25

        same_speaker = (spk == cur.speaker_id)

        # Regeln für neuen Turn
        new_turn = False

        if not same_speaker and pause > 0.05:
            new_turn = True
        elif pause > dynamic_pause:
            new_turn = True
        elif cur.text.lower() in SHORT_WORDS and not same_speaker:
            new_turn = True

        if new_turn:
            utts.append(cur)
            cur = Utterance(
                start=w.start,
                end=w.end,
                speaker_id=spk,
                text=w.word,
            )
        else:
            cur.end = w.end
            cur.text += " " + w.word

    utts.append(cur)
    return utts
