import sys
from pathlib import Path
from wargame_analyzer import WargameAnalyzer


def main():
    """Matrix Wargame Analyzer Pipeline - OpenRouter Edition."""
    
    print("=" * 60)
    print("MATRIX WARGAME ANALYZER - OpenRouter Edition")
    print("=" * 60)
    
    # Konfiguration
    CONFIG_PATH = "../config.json"
    ROUND_SPLITTER_PROMPT = "systemprompt_split_rounds.txt"
    GAME_REPORT_PROMPT = "systemprompt_json.txt"
    TRANSCRIPT_PATH = "data/transcript.txt"
    OUTPUT_DIR = "data/reports"
    
    # Model-Auswahl
    MODEL_OPTIONS = {
        "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
        "gpt-4o": "openai/gpt-4o"
    }
    SELECTED_MODEL = MODEL_OPTIONS["claude-3.5-sonnet"]
    
    print(f"\nKonfiguration:")
    print(f"  Model: {SELECTED_MODEL}")
    print(f"  Transcript: {TRANSCRIPT_PATH}")
    print(f"  Output: {OUTPUT_DIR}")
    
    # Initialisiere Analyzer
    try:
        analyzer = WargameAnalyzer(CONFIG_PATH)
    except FileNotFoundError:
        print(f"\nConfig nicht gefunden: {CONFIG_PATH}")
        sys.exit(1)
    except KeyError:
        print(f"\n'openrouter_api_key' fehlt in {CONFIG_PATH}")
        sys.exit(1)
    
    # ========================================================================
    # SCHRITT 1: Analysiere wo die Runden beginnen (Zeitstempel-Erkennung)
    # ========================================================================
    print("\nSchritt 1: Runden-Zeitstempel ermitteln...")
    
    rounds_json = analyzer.split_rounds(
        round_splitter_prompt_path=ROUND_SPLITTER_PROMPT,
        transcript_path=TRANSCRIPT_PATH,
        model=SELECTED_MODEL
    )
    
    if not rounds_json:
        print("Keine Runden-Informationen gefunden.")
        sys.exit(1)
    
    print(f"\nRunden-JSON erhalten:")
    for key, value in rounds_json.items():
        if key.startswith("runde_"):
            print(f"  {key}: {value}")
    
    # Speichere Runden-Übersicht
    with open(Path(OUTPUT_DIR) / "rounds_overview.json", "w", encoding="utf-8") as f:
        import json
        json.dump(rounds_json, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Übersicht gespeichert: {OUTPUT_DIR}/rounds_overview.json")
    
    # ========================================================================
    # SCHRITT 2: Teile Transkript physisch in separate .txt Dateien auf
    # ========================================================================
    print("\nSchritt 2: Transkript in separate Dateien aufteilen...")
    
    round_files = analyzer.split_transcript_by_rounds(
        rounds_json=rounds_json,
        transcript_path=TRANSCRIPT_PATH,
        output_directory=OUTPUT_DIR
    )
    
    if not round_files:
        print("Keine Runden-Dateien erstellt.")
        sys.exit(1)
    
    print(f"\n{len(round_files)} Runden-Dateien erstellt")

    # ========================================================================
    # SCHRITT 3: Generiere Game Reports für jede Runde
    # ========================================================================
    print("\nSchritt 3: Game Reports pro Runde generieren...")
    
    for i, round_file_path in enumerate(round_files, start=1):
        print(f"\n  Verarbeite Runde {i} (Datei: {Path(round_file_path).name})...")
        
        analyzer.generate_report_for_round(
            round_number=i,
            round_text_path=round_file_path,
            system_prompt_path=GAME_REPORT_PROMPT,
            model=SELECTED_MODEL,
            output_directory=OUTPUT_DIR
        )
    
    # ========================================================================
    # ABSCHLUSS
    # ========================================================================
    print("\n" + "=" * 60)
    print("PIPELINE ERFOLGREICH ABGESCHLOSSEN!")
    print("=" * 60)
    print(f"\nGenerierte Dateien in: {OUTPUT_DIR}")
    print(f"  - {len(round_files)} Runden-Transkripte (round1.txt, round2.txt, ...)")
    print(f"  - {len(round_files)} Game Reports (round1_report.json, round2_report.json, ...)")
    print(f"  - 1 Runden-Übersicht (rounds_overview.json)")


if __name__ == "__main__":
    main()
