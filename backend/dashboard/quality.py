import json
from collections import Counter

filepath = "/shared/hackathon_2025_buggybutlucky/backend/dashboard/message.txt"

def analyze_quality(filepath):
    """
    Analysiert die message.txt und berechnet Verteilung von Quality für red und blue arguments.
    """
    red_qualities = []
    blue_qualities = []
    
    # Lade und parse die Datei
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        data = json.loads(content)
    
    # Durchsuche alle Einträge
    def extract_qualities(obj, current_key=""):
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "red_arguments" and isinstance(value, list):
                    for arg in value:
                        if 'quality' in arg:
                            red_qualities.append(arg['quality'])
                elif key == "blue_arguments" and isinstance(value, list):
                    for arg in value:
                        if 'quality' in arg:
                            blue_qualities.append(arg['quality'])
                else:
                    extract_qualities(value, key)
        elif isinstance(obj, list):
            for item in obj:
                extract_qualities(item, current_key)
    
    extract_qualities(data)
    
    # Zähle Häufigkeiten
    red_quality_counts = Counter(red_qualities) if len(red_qualities) > 0 else {}
    blue_quality_counts = Counter(blue_qualities) if len(blue_qualities) > 0 else {}
    
    sorted_red_qualities = sorted(red_quality_counts.items(), key=lambda x: x[1], reverse=True) if red_quality_counts else []
    sorted_blue_qualities = sorted(blue_quality_counts.items(), key=lambda x: x[1], reverse=True) if blue_quality_counts else []
    
    # Analysiere Red Arguments
    print("\n" + "=" * 60)
    print("RED ARGUMENTS - Quality Verteilung:")
    print("=" * 60)
    
    if len(red_qualities) == 0:
        print("Keine Red Quality-Werte gefunden!")
    else:
        for quality, count in sorted_red_qualities:
            percentage = (count / len(red_qualities)) * 100
            print(f"{quality:15} {count:3} ({percentage:5.2f}%)")
        
        print(f"\nGesamt: {len(red_qualities)} Argumente")
    
    # Analysiere Blue Arguments
    print("\n" + "=" * 60)
    print("BLUE ARGUMENTS - Quality Verteilung:")
    print("=" * 60)
    
    if len(blue_qualities) == 0:
        print("Keine Blue Quality-Werte gefunden!")
    else:
        for quality, count in sorted_blue_qualities:
            percentage = (count / len(blue_qualities)) * 100
            print(f"{quality:15} {count:3} ({percentage:5.2f}%)")
        
        print(f"\nGesamt: {len(blue_qualities)} Argumente")
    
    print("\n" + "=" * 60)
    
    # JSON-Output für weitere Verarbeitung
    result = {
        "red_arguments": {
            "total": len(red_qualities),
            "quality": {
                quality: {
                    "count": count,
                    "percentage": round((count / len(red_qualities)) * 100, 2)
                }
                for quality, count in sorted_red_qualities
            } if len(red_qualities) > 0 else {}
        },
        "blue_arguments": {
            "total": len(blue_qualities),
            "quality": {
                quality: {
                    "count": count,
                    "percentage": round((count / len(blue_qualities)) * 100, 2)
                }
                for quality, count in sorted_blue_qualities
            } if len(blue_qualities) > 0 else {}
        }
    }
    
    print("\nJSON-Format:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Speichere JSON in Datei
    output_path = "/shared/hackathon_2025_buggybutlucky/frontend/public/quality_results.json"
    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(result, outfile, indent=2, ensure_ascii=False)
    
    print(f"\nErgebnisse gespeichert in: {output_path}")
    
    return result

if __name__ == "__main__":
    analyze_quality(filepath)