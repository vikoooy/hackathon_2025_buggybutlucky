"""
Whisper configuration for v5.1 pipeline.
Contains all recommended parameters for stable word-level timestamps.
"""

WHISPER_CONFIG = {
    "beam_size": 10,
    "best_of": 5,

    # Whisper-VAD ist deaktiviert; wir benutzen stattdessen pyannote-VAD.
    "vad_filter": False,

    # exakteste Wortgrenzen: "end" ist deutlich stabiler als True
    "word_timestamps": "end",

    # die 3-Phasen-Temperatur erzeugt hohe Stabilität
    "temperature": [0.0, 0.2, 0.4],

    # verhindert Wiederholungen ("ja ja", "ich ich")
    "repetition_penalty": 1.2,

    # weniger falsch-negative Silence-Erkennung
    "no_speech_threshold": 0.5,

    # verhindert initialen Zeitstempel-Drift
    "max_initial_timestamp": 0.0,
}
