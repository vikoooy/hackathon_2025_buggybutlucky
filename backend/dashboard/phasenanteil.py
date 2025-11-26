import json

filepath = "/shared/hackathon_2025_buggybutlucky/backend/dashboard/message.txt"


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
    
    phase_times = {}  # Phase Name -> Gesamtzeit in Sekunden
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
                
                # Gruppiere nach Phase (ohne Rundennummer)
                if phase_name not in phase_times:
                    phase_times[phase_name] = 0
                phase_times[phase_name] += duration
                total_time += duration
                
                print(f"Runde {round_num} - {phase_name}: {timestamp_start} bis {timestamp_end} = {duration}s")
    
    if total_time == 0:
        print("\nKeine gültigen Phasen-Zeiten gefunden!")
        return
    
    # Sortiere Phasen nach Zeit (absteigend)
    sorted_phases = sorted(phase_times.items(), key=lambda x: x[1], reverse=True)
    

    print(f"\nGesamtzeit aller Phasen: {total_time // 60} Min {total_time % 60} Sek\n")
    
    for phase_name, time_sec in sorted_phases:
        percentage = (time_sec / total_time) * 100
        minutes = time_sec // 60
        seconds = time_sec % 60
        
        print(f"{phase_name:35}{percentage:5.1f}% ({minutes}:{seconds:02d})")
    
    
    # JSON-Output für weitere Verarbeitung
    print("\nJSON-Format:")
    result = {
        "total_seconds": total_time,
        "total_formatted": f"{total_time // 60}:{total_time % 60:02d}",
        "phases": {
            phase_name: {
                "seconds": time_sec,
                "formatted": f"{time_sec // 60}:{time_sec % 60:02d}",
                "percentage": round((time_sec / total_time) * 100, 2)
            }
            for phase_name, time_sec in sorted_phases
        }
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    analyze_phases(filepath)