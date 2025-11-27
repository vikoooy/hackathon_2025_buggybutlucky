import json
from collections import Counter
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

filepath = os.path.abspath(
    os.path.join(base_dir, "..", "..", "data_processing", "data", "reports", "game_report_combined.json")
)

def analyze_tone(filepath):
    """
    Analysiert die message.txt und berechnet Verteilung von Tone für red und blue arguments.
    """
    red_tones = []
    blue_tones = []
    
    # Lade und parse die Datei
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    
    # Durchsuche alle Einträge
    def extract_tones(obj, current_key=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "red_arguments" and isinstance(value, list):
                    for arg in value:
                        if 'tone' in arg:
                            red_tones.append(arg['tone'])
                elif key == "blue_arguments" and isinstance(value, list):
                    for arg in value:
                        if 'tone' in arg:
                            blue_tones.append(arg['tone'])
                else:
                    extract_tones(value, key)
        elif isinstance(obj, list):
            for item in obj:
                extract_tones(item, current_key)
    
    extract_tones(data)
    
    # Zähle Häufigkeiten
    red_tone_counts = Counter(red_tones) if len(red_tones) > 0 else {}
    blue_tone_counts = Counter(blue_tones) if len(blue_tones) > 0 else {}
    
    sorted_red_tones = sorted(red_tone_counts.items(), key=lambda x: x[1], reverse=True) if red_tone_counts else []
    sorted_blue_tones = sorted(blue_tone_counts.items(), key=lambda x: x[1], reverse=True) if blue_tone_counts else []
    
    # Analysiere Red Arguments
    print("\n" + "=" * 60)
    print("RED ARGUMENTS - Tone Verteilung:")
    print("=" * 60)
    
    if len(red_tones) == 0:
        print("Keine Red Tone-Werte gefunden!")
    else:
        for tone, count in sorted_red_tones:
            percentage = (count / len(red_tones)) * 100
            print(f"{tone:15} {count:3} ({percentage:5.2f}%)")
        
        print(f"\nGesamt: {len(red_tones)} Argumente")
    
    # Analysiere Blue Arguments
    print("\n" + "=" * 60)
    print("BLUE ARGUMENTS - Tone Verteilung:")
    print("=" * 60)
    
    if len(blue_tones) == 0:
        print("Keine Blue Tone-Werte gefunden!")
    else:
        for tone, count in sorted_blue_tones:
            percentage = (count / len(blue_tones)) * 100
            print(f"{tone:15} {count:3} ({percentage:5.2f}%)")
        
        print(f"\nGesamt: {len(blue_tones)} Argumente")
    
    print("\n" + "=" * 60)
    
    # JSON-Output für weitere Verarbeitung
    result = {
        "red_arguments": {
            "total": len(red_tones),
            "tone": {
                tone: {
                    "count": count,
                    "percentage": round((count / len(red_tones)) * 100, 2)
                }
                for tone, count in sorted_red_tones
            } if len(red_tones) > 0 else {}
        },
        "blue_arguments": {
            "total": len(blue_tones),
            "tone": {
                tone: {
                    "count": count,
                    "percentage": round((count / len(blue_tones)) * 100, 2)
                }
                for tone, count in sorted_blue_tones
            } if len(blue_tones) > 0 else {}
        }
    }
    
    print("\nJSON-Format:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Speichere JSON in Datei

    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Relativer Pfad zur phases_results.json im Frontend
    output_path = os.path.abspath(
        os.path.join(base_dir, "..", "..", "frontend", "public", "tone_results.json")
    )

    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(result, outfile, indent=2, ensure_ascii=False)
    
    print(f"\nErgebnisse gespeichert in: {output_path}")
    
    return result

if __name__ == "__main__":
    analyze_tone(filepath)