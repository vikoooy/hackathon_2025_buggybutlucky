import json
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

filepath = os.path.abspath(
    os.path.join(base_dir, "..", "..", "data_processing", "data", "reports", "game_report_combined.json")
)


def parse_timestamp(timestamp_str):
    """Konvertiert Timestamp-String (HH:MM:SS oder MM:SS) zu Sekunden."""
    parts = timestamp_str.split(':')
    if len(parts) == 3:  # HH:MM:SS
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:  # MM:SS
        return int(parts[0]) * 60 + int(parts[1])
    return 0

def calculate_duration(start_str, end_str):
    """Berechnet Dauer in Sekunden zwischen zwei Timestamps."""
    start_sec = parse_timestamp(start_str)
    end_sec = parse_timestamp(end_str)
    return end_sec - start_sec

def analyze_phases(filepath):
    """
    Analysiert die JSON-Datei und berechnet zeitliche Anteile der Phasen.
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    phases_list = []  # Liste aller einzelnen Phasen
    total_time = 0
    
    # Durchlaufe alle Runden
    for round_data in data.get('rounds', []):
        round_num = round_data.get('round_number', '?')
        
        # Durchlaufe alle Phasen in der Runde
        for key, phase_data in round_data.items():
            if isinstance(phase_data, dict) and 'phase_name' in phase_data:
                phase_name = phase_data['phase_name']
                timestamp_start = phase_data.get('timestamp_start', '00:00')
                timestamp_end = phase_data.get('timestamp_end', '00:00')
                
                duration = calculate_duration(timestamp_start, timestamp_end)
                
                # Füge jede Phase einzeln hinzu mit Rundennummer
                phase_key = f"Runde {round_num} - {phase_name}"
                phases_list.append({
                    'key': phase_key,
                    'round': round_num,
                    'name': phase_name,
                    'start': timestamp_start,
                    'end': timestamp_end,
                    'duration': duration
                })
                total_time += duration
                
                print(f"Runde {round_num} - {phase_name}: {timestamp_start} bis {timestamp_end} = {duration}s")
    
    if total_time == 0:
        print("\nKeine gültigen Phasen-Zeiten gefunden!")
        return
    
    # Sortiere Phasen nach Zeit (absteigend)
    sorted_phases = sorted(phases_list, key=lambda x: x['duration'], reverse=True)
    
    print(f"\nGesamtzeit aller Phasen: {total_time // 60} Min {total_time % 60} Sek\n")
    
    for phase in sorted_phases:
        percentage = (phase['duration'] / total_time) * 100
        minutes = phase['duration'] // 60
        seconds = phase['duration'] % 60
        
        print(f"{phase['key']:45}{percentage:5.1f}% ({minutes}:{seconds:02d})")
    
    # JSON-Output für weitere Verarbeitung
    result = {
        "total_seconds": total_time,
        "total_formatted": f"{total_time // 60}:{total_time % 60:02d}",
        "phases": {
            phase['key']: {
                "round": phase['round'],
                "phase_name": phase['name'],
                "seconds": phase['duration'],
                "formatted": f"{phase['duration'] // 60}:{phase['duration'] % 60:02d}",
                "percentage": round((phase['duration'] / total_time) * 100, 2),
                "timestamp_start": phase['start'],
                "timestamp_end": phase['end']
            }
            for phase in sorted_phases
        }
    }
    
    print("\nJSON-Format:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # Speichere JSON in Datei

    # Basisverzeichnis des Skripts
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Relativer Pfad zur phases_results.json im Frontend
    output_path = os.path.abspath(
        os.path.join(base_dir, "..", "..", "frontend", "public", "phases_results.json")
    )

    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(result, outfile, indent=2, ensure_ascii=False)
    
    print(f"\nErgebnisse gespeichert in: {output_path}")
    
    return result

if __name__ == "__main__":
    analyze_phases(filepath)