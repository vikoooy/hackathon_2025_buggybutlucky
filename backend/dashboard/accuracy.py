import openai
import re
import json
from docx import Document
from collections import defaultdict
from openai import OpenAI


# ====== Konfiguration ======
client = OpenAI(
    api_key="XXX",
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

# ====== GPT-basiertes Phase-Comparison ======
def compare_phases(phase_text1, phase_text2):
    """
    Vergleicht zwei Phasen semantisch.
    Gibt eine Score (0-1) und ein Vergleichs-Dikt zurück.
    """

    prompt = f"""
    
Du bist ein Evaluations-Assistent für Op4C-Wargaming-Daten.


Aufgabe: Vergleiche zwei Texte auf faktische Spielinhalte.

WICHTIG: Extrahiere ZUERST die Fakten aus BEIDEN Texten getrennt, DANN vergleiche sie.

SCHRITT 1: Faktextraktion für Text 1
Lies Text 1 und liste ALLE vorhandenen Fakten auf:

Intelphase:
- Blau_12_erreicht: [ja/nein/nicht erwähnt]
- Rot_Vorteil_Höhe: [0/+1/+2/nicht erwähnt]
- Rot_Vorteil_Typ: [Cyber/Personal/Sabotage/nicht erwähnt]

Diskussionsgefecht:
- Ressourcen_Wert: [1/2/3/4/nicht erwähnt]
- Komplexität: [1/2/3/4/nicht erwähnt]
- Verteidigung: [1/2/3/4/nicht erwähnt]
- Angriffszeitfenster: [1/2/3/4/nicht erwähnt]
- Tabellensumme: [Zahl oder nicht erwähnt]

Erfolgswurf:
- Mindestwert: [Zahl oder nicht erwähnt]
- Gewürfelter_Wert: [Zahl oder nicht erwähnt]
- Ergebnis: [Erfolg/Fehlschlag/Teilerfolg/nicht erwähnt]

Auswirkung:
- Endergebnis: [Erfolg/Teilerfolg/Fehlschlag/nicht erwähnt]

SCHRITT 2: Faktextraktion für Text 2
[Wiederhole die gleiche Struktur]

SCHRITT 3: SEMANTISCHE ÄQUIVALENZEN beachten!

Folgende Formulierungen bedeuten das GLEICHE:
- "Erfolg" = "voller Erfolg" = "erfolgreich" = "Der Angriff war erfolgreich" = "gelungen"
- "Teilerfolg" = "teilweise erfolgreich" = "teilweise gelungen"
- "Fehlschlag" = "gescheitert" = "nicht erfolgreich" = "Misserfolg"

SCHRITT 4: Vergleich-Regeln

Zähle für JEDEN der 12 Aspekte:

A) IDENTISCH: 
   - Beide Texte haben den gleichen Wert (semantisch, nicht wörtlich!)
   - ODER beide haben "nicht erwähnt"
   
B) UNTERSCHIEDLICH:
   - Text 1 und Text 2 haben verschiedene Werte (außer "nicht erwähnt")
   
C) NUR_IN_EINEM_TEXT:
   - Ein Text hat einen Wert, der andere hat "nicht erwähnt"
   - Diese zählen NICHT als Unterschied für die Similarity-Berechnung!

BERECHNUNG der Similarity:

Schritt 1: Zähle alle Aspekte, die in MINDESTENS einem Text erwähnt werden (nicht "nicht erwähnt")
         = relevante_fakten


Schritt 2: Zähle davon, wie viele in BEIDEN Texten identisch sind
         = identische_fakten

Schritt 3: similarity_percent = (identische_fakten / relevante_fakten) × 100



SPEZIALFALL: Wenn KEINE Unterschiede gefunden werden UND different_aspects leer ist, 
             MUSS similarity_percent = 100 sein!


---

Text 1:
{phase_text1}

---

Text 2:
{phase_text2}

---

Antworte NUR mit diesem JSON (keine Erklärungen davor oder danach):
{{
    "text1_facts": {{
        "Blau_12_erreicht": "wert oder null",
        "Rot_Vorteil_Höhe": "wert oder null",
        "Rot_Vorteil_Typ": "wert oder null",
        "Ressourcen_Wert": "wert oder null",
        "Komplexität": "wert oder null",
        "Verteidigung": "wert oder null",
        "Angriffszeitfenster": "wert oder null",
        "Tabellensumme": "wert oder null",
        "Mindestwert": "wert oder null",
        "Gewürfelter_Wert": "wert oder null",
        "Erfolgswurf_Ergebnis": "wert oder null",
        "Endergebnis": "wert oder null"
    }},
    "text2_facts": {{
        "Blau_12_erreicht": "wert oder null",
        "Rot_Vorteil_Höhe": "wert oder null",
        "Rot_Vorteil_Typ": "wert oder null",
        "Ressourcen_Wert": "wert oder null",
        "Komplexität": "wert oder null",
        "Verteidigung": "wert oder null",
        "Angriffszeitfenster": "wert oder null",
        "Tabellensumme": "wert oder null",
        "Mindestwert": "wert oder null",
        "Gewürfelter_Wert": "wert oder null",
        "Erfolgswurf_Ergebnis": "wert oder null",
        "Endergebnis": "wert oder null"
    }},
    "similarity_percent": 0,
    "same_aspects": ["Liste mit identischen Fakten im Format 'Aspekt: Wert'"],
    "different_aspects": ["Liste mit unterschiedlichen Fakten im Format 'Aspekt: Text1=X, Text2=Y'"],
    "only_in_text1": ["Liste von Aspekten die nur in Text 1 erwähnt sind"],
    "only_in_text2": ["Liste von Aspekten die nur in Text 2 erwähnt sind"]
}}

KRITISCH: 
- Wenn different_aspects leer ist, MUSS similarity_percent = 100 sein!
- Aspekte in only_in_text1 oder only_in_text2 reduzieren die Similarity NICHT!
"""

    response = client.chat.completions.create(
        model="openai/gpt-4o",
        messages=[{"role":"user","content":prompt}],
        temperature=0
    )
    answer = response.choices[0].message.content
    try:
        match = re.search(r'\{.*\}', answer, re.DOTALL)
        if match:
            return json.loads(match.group())
    except json.JSONDecodeError:
        pass
    return {"similarity_percent":0, "same_aspects":[], "different_aspects":[]}

# ====== Gesamtdokument vergleichen ======
def compare_documents(file1_path, file2_path):
    print("Lese Dokumente ein...")
    text1 = read_text_file(file1_path)
    text2 = read_docx_file(file2_path)

    print("Teile Dokumente in Phasen...")
    phases1 = split_into_phases(text1)
    phases2 = split_into_phases(text2)

    # Phasen vergleichen (matched by phase number)
    comparison_results = {}
    all_phase_numbers = set(phases1.keys()) | set(phases2.keys())

    for phase_num in sorted(all_phase_numbers):
        phase_text1 = phases1.get(phase_num, "")
        phase_text2 = phases2.get(phase_num, "")
        result = compare_phases(phase_text1, phase_text2)
        comparison_results[phase_num] = result

    # Durchschnittliche Ähnlichkeit berechnen
    avg_similarity = sum([r['similarity_percent'] for r in comparison_results.values()]) / len(comparison_results)

    return comparison_results, avg_similarity, phases1, phases2

# ====== Ergebnisse ausgeben ======
def print_results(comparison_results, avg_similarity, phases1, phases2):
    print("\n" + "="*60)
    print("INHALTLICHE ÄHNLICHKEIT ANALYSE")
    print("="*60)
    print(f"\n📊 Gesamt-Ähnlichkeit: {avg_similarity:.1f}%\n")
    
    for phase_num, result in comparison_results.items():
        print(f"🎯 Phase {phase_num}:")
        print(f"   Ähnlichkeit: {result['similarity_percent']:.1f}%")
        print(f"   Übereinstimmende Aspekte: {result['same_aspects']}")
        print(f"   Unterschiedliche Aspekte: {result['different_aspects']}\n")

    print("="*60)
    print("Gefundene Phasen in Dokument 1:")
    for k, v in phases1.items():
        print(f"  Runde {k}:")
        if isinstance(v, dict):
            for phase_name, phase_text in v.items():
                preview = phase_text[:100].replace("\n", " ")
                print(f"    {phase_name}: {preview}...")
        else:
            print(f"    {v[:100]}...")

    print("Gefundene Phasen in Dokument 2:")
    for k, v in phases2.items():
        print(f"  Runde {k}:")
        if isinstance(v, dict):
            for phase_name, phase_text in v.items():
                preview = phase_text[:100].replace("\n", " ")
                print(f"    {phase_name}: {preview}...")
        else:
            print(f"    {v[:100]}...")
    print("="*60)

# ====== Hauptprogramm ======
if __name__ == "__main__":
    file1 = "transcript.txt"
    file2 = "Op4C Hackathon - Korrekte Ergebnisse.docx"

    comparison_results, avg_similarity, phases1, phases2 = compare_documents(file1, file2)
    print_results(comparison_results, avg_similarity, phases1, phases2)
