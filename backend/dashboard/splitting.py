
# ====== Konfiguration ======
client = OpenAI(
    api_key="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",
    base_url="https://openrouter.ai/api/v1"
)

# ====== Dateien einlesen ======
def read_text_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

def read_docx_file(filepath):
    doc = Document(filepath)
    return "\n".join([p.text for p in doc.paragraphs])

# ====== GPT-basiertes Phasen-Splitting ======
def split_into_phases(text):
    prompt = f"""
Du bist ein KI-Assistent, der eine Audiotranskription eines Op4C-Wargames strukturiert.
Deine wichtigste Aufgabe ist es, Spielrunden sauber zu erkennen, ohne Vermutungen oder Interpretationen.
Du darfst dich NUR auf explizite Fakten im Transkript stützen.

IGNORIERE ALLES RAUSCHEN:
- “X verlässt den Raum”
- “jemand kommt zurück”
- Hintergrundgespräche
- Nebenbemerkungen
Diese Events kennzeichnen KEINE neue Runde.

==============================
ERKENNUNG EINER NEUEN RUNDE – HARTE FAKTEN
==============================

Eine neue Runde beginnt NUR, wenn die folgenden drei Signale IN DIESER REIHENFOLGE im Transkript auftreten:

1. Die vorherige Runde ist vollständig abgeschlossen:
   a) Alle vier Dimensionen wurden besprochen:
      - Ressourcen
      - Komplexität
      - Verteidigung
      - Angriffszeitfenster
   b) Rot hat den Erfolgswurf (3W6) durchgeführt und das Ergebnis wurde ausgesprochen.
   c) Es wurde eine Auswirkung beschrieben (z. B. Erfolg, Teilerfolg, Konsequenzen).

2. Danach startet eine NEUE Intelphase:
   ZWINGEND ERKENNBAR AN:
   - Blau würfelt erneut 3W6, um eine 12 zu erreichen
   - Rot würfelt erneut X-Achse + Y-Achse

   → Diese Würfelabfolge ist ein eindeutiges Spielsignal, das NICHT zufällig vorkommt.

3. Rot beschreibt anschließend einen NEUEN Angriff:
   Beispiele:
   - “mein nächster Angriff…”
   - “diesmal mache ich…”
   - “die zweite Attacke…”

Nur wenn alle 3 Bedingungen erfüllt sind, beginnt eine neue Runde.

==============================
ERKENNUNG DER PHASEN
==============================

PHASE 1 — Intelphase:
- Blau würfelt 3W6
- Rot würfelt X und Y
- Vorteil wird bestimmt

PHASE 2 — Diskussionsgefecht:
- Rot beschreibt einen Angriff
- Vier Dimensionen werden diskutiert
- Jede Dimension erhält S/M/L/XL
- Rot würfelt 3W6 Erfolgswurf
- Auswirkungen werden beschrieben

==============================
AUSGABEFORMAT (WICHTIG!)
==============================

GIB DEIN ERGEBNIS AUSSCHLIESSLICH ALS FOLGENDES JSON AUS:

{{
  "1": {{
    "phase1": "Text der Intelphase Runde 1",
    "phase2": "Text des Diskussionsgefechts Runde 1"
  }},
  "2": {{
    "phase1": "Text der Intelphase Runde 2",
    "phase2": "Text des Diskussionsgefechts Runde 2"
  }}
}}

- Nutze NUR gültiges JSON
- Keine Kommentare
- Keine Erklärungen
- Keine Einleitung
- Keine Markdown-Formatierung
- Keine weiteren Texte außerhalb des JSON

==============================
TRANSKRIPT:
{text}
"""
    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    answer = response.choices[0].message.content

    # JSON extrahieren
    match = re.search(r'\{.*\}', answer, re.DOTALL)
    if match:
        phases_json = json.loads(match.group())
        return {int(k): v for k, v in phases_json.items()}
    else:
        # Fallback: alles als Phase 1
        return {1: text}
