from typing import List, Dict
from ..diarization.merge import Utterance


def infer_roles(utts: List[Utterance]) -> Dict[int, str]:
    """
    Heuristische Rollenerkennung.
    """

    texts_by_spk = {}
    for u in utts:
        texts_by_spk.setdefault(u.speaker_id, []).append(u.text.lower())

    # 1. Moderator erkennen
    moderator_keywords = {
        "hallo", "willkommen", "guten morgen", "guten tag",
        "als nächstes", "weiter gehts", "jetzt machen wir"
    }

    moderator_id = None
    for spk, lines in texts_by_spk.items():
        merged = " ".join(lines)
        if any(k in merged for k in moderator_keywords):
            moderator_id = spk
            break

    roles = {}

    if moderator_id is not None:
        roles[moderator_id] = "Moderator"

    # 2. Teams erkennen (Rot vs Blau)
    red_keywords = {"rot", "angreifer", "wir greifen an", "gegner", "sabotieren"}
    blue_keywords = {"blau", "verteidiger", "wir verteidigen", "abwehren", "abzuwehren"}

    for spk, lines in texts_by_spk.items():
        if spk == moderator_id:
            continue
        merged = " ".join(lines)
        if any(k in merged for k in red_keywords):
            roles[spk] = "Team Rot"
        elif any(k in merged for k in blue_keywords):
            roles[spk] = "Team Blau"
        else:
            roles[spk] = "Unknown"

    return roles
