import re
from typing import List
from dataclasses import dataclass
from ..diarization.merge import Utterance


RE_DUP_WORD = re.compile(r"\b(\w+)\s+\1\b", re.IGNORECASE)


@dataclass
class NormalizeConfig:
    remove_filler: bool = True
    add_punctuation: bool = True
    fix_case: bool = True


FILLER_WORDS = {
    "äh", "ähm", "hm", "hmm", "ööhm", "mhm", "em"
}


def _remove_duplicate_words(text: str) -> str:
    """
    Entfernt direkte Wortwiederholungen wie:
    'ich ich habe' → 'ich habe'
    """
    last = None
    out = []
    for w in text.split():
        if w.lower() != last:
            out.append(w)
        last = w.lower()
    return " ".join(out).strip()


def _remove_fillers(text: str) -> str:
    out = [w for w in text.split() if w.lower() not in FILLER_WORDS]
    return " ".join(out).strip()


def _add_simple_punctuation(text: str) -> str:
    """
    Sehr simple Pseudo-Satzzeichen:
    Falls kein Satzzeichen am Ende → '.'
    Falls '?' Wörter enthalten → '?'
    """
    t = text.strip()

    # Frageerkennung
    question_signals = ["wer", "wie", "was", "wieso", "warum", "kannst", "kannst du", "?"]
    if any(q in t.lower() for q in question_signals):
        if not t.endswith("?"):
            t += "?"
        return t

    # sonst Punkt
    if not t.endswith(".") and not t.endswith("!"):
        t += "."

    return t


def _fix_case(text: str) -> str:
    if not text:
        return text
    text = text.strip()
    return text[0].upper() + text[1:]


def normalize_utterances(
    utts: List[Utterance],
    config: NormalizeConfig = NormalizeConfig()
) -> List[Utterance]:

    out = []

    for u in utts:
        txt = u.text.strip()

        # 1. Doppelte Wörter entfernen
        txt = _remove_duplicate_words(txt)

        # 2. Füllwörter raus
        if config.remove_filler:
            txt = _remove_fillers(txt)

        # 3. Satzzeichen ergänzen
        if config.add_punctuation:
            txt = _add_simple_punctuation(txt)

        # 4. Case fixen
        if config.fix_case:
            txt = _fix_case(txt)

        out.append(
            Utterance(
                start=u.start,
                end=u.end,
                speaker_id=u.speaker_id,
                text=txt,
            )
        )

    return out
