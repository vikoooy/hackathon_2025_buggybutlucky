import re
from collections import defaultdict
from datetime import datetime
import json


filepath = "/shared/hackathon_2025_buggybutlucky/backend/dashboard/transcript_v2.txt"


def parse_timestamp(timestamp_str):
    """Konvertiert Timestamp-String (HH:MM:SS oder MM:SS) zu Sekunden."""
    parts = timestamp_str.split(':')
    if len(parts) == 3:  # HH:MM:SS
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    elif len(parts) == 2:  # MM:SS
        return int(parts[0]) * 60 + int(parts[1])
    return 0

def analyze_speakers(filepath):
    """
    Analysiert die Transkript-Datei und berechnet Redeanteile.
    """
    speaker_times = defaultdict(int)  # Speaker -> Gesamtzeit in Sekunden
    
    # Pattern für Zeilen wie: "00:00–00:16 Speaker 0 (Moderator): ..." oder "00:00–00:16 Clara: ..."
    # Format: TIMESTAMP–TIMESTAMP SPEAKER_NAME: TEXT
    pattern = r'(\d{1,2}:\d{2})(?::(\d{2}))?–(\d{1,2}:\d{2})(?::(\d{2}))?\s+([^:]+):'
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Finde alle Zeitstempel und Speaker
    matches = re.finditer(pattern, content, re.MULTILINE)
    
    for match in matches:
        # Extrahiere Start und End Timestamps
        start_str = match.group(1)
        if match.group(2):  # Hat Sekunden
            start_str += f":{match.group(2)}"
        
        end_str = match.group(3)
        if match.group(4):  # Hat Sekunden
            end_str += f":{match.group(4)}"
        
        # Speaker Name (z.B. "Speaker 0 (Moderator)" oder "Speaker 1")
        speaker = match.group(5).strip()
        
        # Berechne Redezeit
        start_sec = parse_timestamp(start_str)
        end_sec = parse_timestamp(end_str)
        duration = end_sec - start_sec
        
        if duration > 0:
            speaker_times[speaker] += duration
    
    # Berechne Gesamtzeit
    total_time = sum(speaker_times.values())
    
    if total_time == 0:
        print("Keine gültigen Timestamps gefunden!")
        return
    
    # Sortiere Speaker nach Redezeit (absteigend)
    sorted_speakers = sorted(speaker_times.items(), key=lambda x: x[1], reverse=True)
    
    print(f"\nGesamte Aufnahmezeit: {total_time // 60} Min {total_time % 60} Sek\n")
    
    for speaker, time_sec in sorted_speakers:
        percentage = (time_sec / total_time) * 100
        minutes = time_sec // 60
        seconds = time_sec % 60
        
        
        print(f"{speaker:10} {percentage:5.1f}% ({minutes}:{seconds:02d})")
    
    print("\n" + "="*60)
    
    # JSON-Output für weitere Verarbeitung
    print("\nJSON-Format:")
    result = {
        "total_seconds": total_time,
        "speakers": {
            speaker: {
                "seconds": time_sec,
                "percentage": round((time_sec / total_time) * 100, 2)
            }
            for speaker, time_sec in sorted_speakers
        }
    }
    
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    analyze_speakers(filepath)