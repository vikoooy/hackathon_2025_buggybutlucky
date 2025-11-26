import json
import requests
import re
from pathlib import Path


class WargameAnalyzer:
    """Analyzer für Matrix-Wargame Transkripte mit OpenRouter API."""

    def __init__(self, config_path: str = None, api_key: str = None):
        """
        Initialisiere Analyzer mit API Key aus Config oder direkt.

        Args:
            config_path: Pfad zur config.json mit openrouter_api_key
            api_key: Direkter API Key (hat Vorrang vor config_path)
        """
        if api_key:
            self.api_key = api_key
        elif config_path:
            with open(config_path, "r") as f:
                config = json.load(f)
                self.api_key = config["openrouter_api_key"]
        else:
            raise ValueError("Either config_path or api_key required")

        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/wargame-analyzer",
            "X-Title": "Matrix Wargame Analyzer"
        }
    
    def split_rounds(
        self, 
        round_splitter_prompt_path: str, 
        transcript_path: str, 
        model: str,
        max_retries: int = 3
    ) -> dict:
        """
        Analysiert Transkript und gibt JSON mit Runden-Zeitstempeln zurück.
        
        Args:
            round_splitter_prompt_path: Pfad zum Round-Splitter System-Prompt
            transcript_path: Pfad zum vollständigen Transkript
            model: OpenRouter Model-ID (z.B. "anthropic/claude-3.5-sonnet")
            max_retries: Maximale Anzahl an Versuchen bei JSON-Fehlern
        
        Returns:
            Dictionary mit Runden-Info inkl. Zeitstempeln
            Beispiel: {
                "runde_1": "00:00–04:35 [Beschreibung]",
                "runde_2": "19:03–32:50 [Beschreibung]",
                "cut_reasoning": "..."
            }
        """
        # Lade Dateien
        with open(round_splitter_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
        with open(transcript_path, "r", encoding="utf-8") as f:
            transcript = f.read().strip()
        
        # Bereite API-Request vor
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": transcript}
        ]
        
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": 150000,
                    "temperature": 0.0
                }
                
                # API Call
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=300
                )
                
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                
                # Extrahiere und parse JSON
                json_content = self._extract_json_from_text(content)
                data = self._parse_json_robust(json_content)
                
                return data
                
            except json.JSONDecodeError as e:
                print(f"JSON-Parse-Fehler (Versuch {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    print("   Versuche erneut mit Fehlerkorrektur-Hinweis...")
                    messages.append({
                        "role": "assistant",
                        "content": content
                    })
                    messages.append({
                        "role": "user",
                        "content": f"Das JSON war nicht valide. Fehler: {str(e)}\n\nBitte gib NUR valides JSON zurück, KEINE Markdown-Blöcke, KEINE Erklärungen. Beginne direkt mit {{ und ende mit }}."
                    })
                else:
                    print("Maximale Versuche erreicht.")
                    raise
        
        return {}
    
    def split_transcript_by_rounds(
        self,
        rounds_json: dict,
        transcript_path: str,
        output_directory: str
    ) -> list:
        """
        Teilt das Transkript physisch in separate .txt Dateien pro Runde auf.
        
        Args:
            rounds_json: Dictionary aus split_rounds() mit Zeitstempeln
                Beispiel: {
                    "runde_1": "00:00–04:35 [...]",
                    "runde_2": "19:03–32:50 [...]"
                }
            transcript_path: Pfad zum Original-Transkript
            output_directory: Verzeichnis für die Runden-Dateien
        
        Returns:
            Liste von Pfaden zu den erstellten Runden-Dateien
        """
        # Lade Original-Transkript
        with open(transcript_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # Extrahiere Zeitstempel aus rounds_json
        round_timestamps = []
        for key in sorted(rounds_json.keys()):
            if key.startswith("runde_"):
                # Extrahiere den Start-Zeitstempel (z.B. "19:03" aus "19:03–32:50 [...]")
                time_range = rounds_json[key].split("[")[0].strip()
                start_time = time_range.split("–")[0].strip() if "–" in time_range else time_range.split("—")[0].strip()
                round_timestamps.append(start_time)
        
        print(f"\nExtrahierte Zeitstempel: {round_timestamps}")
        
        # Sortiere Zeitstempel (konvertiere zu Sekunden für korrekte Sortierung)
        round_timestamps_sorted = sorted(round_timestamps, key=self._parse_timestamp)
        
        # Erstelle Output-Verzeichnis
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        
        # Teile Transkript auf
        round_files = []
        current_round = 0
        current_round_lines = []
        
        for line in lines:
            line_timestamp = self._extract_timestamp_from_line(line)
            
            if line_timestamp is not None:
                line_seconds = self._parse_timestamp(line_timestamp)
                
                # Prüfe ob wir eine neue Runde erreicht haben
                if current_round < len(round_timestamps_sorted) - 1:
                    next_round_start = self._parse_timestamp(round_timestamps_sorted[current_round + 1])
                    
                    if line_seconds >= next_round_start:
                        # Speichere aktuelle Runde
                        if current_round_lines:
                            round_file = self._save_round_file(
                                current_round + 1, 
                                current_round_lines, 
                                output_directory
                            )
                            round_files.append(round_file)
                            print(f"✓ Runde {current_round + 1} gespeichert: {len(current_round_lines)} Zeilen")
                        
                        # Starte neue Runde
                        current_round += 1
                        current_round_lines = []
            
            current_round_lines.append(line)
        
        # Speichere letzte Runde
        if current_round_lines:
            round_file = self._save_round_file(
                current_round + 1, 
                current_round_lines, 
                output_directory
            )
            round_files.append(round_file)
            print(f"✓ Runde {current_round + 1} gespeichert: {len(current_round_lines)} Zeilen")
        
        return round_files
    
    def _parse_timestamp(self, timestamp: str) -> int:
        """
        Konvertiert Zeitstempel von 'MM:SS' zu Sekunden.
        
        Args:
            timestamp: Zeitstempel als String (z.B. "19:03")
        
        Returns:
            Sekunden als Integer
        """
        parts = timestamp.split(":")
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        return 0
    
    def _extract_timestamp_from_line(self, line: str) -> str:
        """
        Extrahiert Zeitstempel aus einer Transkript-Zeile.
        
        Args:
            line: Zeile aus dem Transkript (z.B. "00:00–00:16 Speaker 0: ...")
        
        Returns:
            Start-Zeitstempel oder None wenn nicht gefunden
        """
        # Suche nach Muster "MM:SS–MM:SS" oder "MM:SS—MM:SS"
        match = re.match(r'(\d{1,2}:\d{2})[–—]', line)
        if match:
            return match.group(1)
        return None
    
    def _save_round_file(self, round_number: int, lines: list, output_directory: str) -> str:
        """
        Speichert eine Runde als .txt Datei.
        
        Args:
            round_number: Nummer der Runde
            lines: Liste von Zeilen
            output_directory: Verzeichnis für die Datei
        
        Returns:
            Pfad zur gespeicherten Datei
        """
        output_path = Path(output_directory) / f"round{round_number}.txt"
        with open(output_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return str(output_path)
    
    def generate_report_for_round(
        self,
        round_number: int,
        round_text_path: str,
        system_prompt_path: str,
        model: str,
        output_directory: str,
        max_retries: int = 2
    ) -> str:
        """
        Generiert einen Game Report für eine einzelne Runde.
        
        Args:
            round_number: Nummer der Runde
            round_text_path: Pfad zur .txt Datei der Runde
            system_prompt_path: Pfad zum Game-Report System-Prompt
            model: OpenRouter Model-ID
            output_directory: Verzeichnis für Output-JSONs
            max_retries: Maximale Anzahl an Versuchen bei JSON-Fehlern
        
        Returns:
            Pfad zur gespeicherten JSON-Datei
        """
        # Lade System-Prompt
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            system_prompt = f.read().strip()
        
        # Lade Runden-Text
        with open(round_text_path, "r", encoding="utf-8") as f:
            round_text = f.read().strip()
        
        # Bereite API-Request vor
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analysiere NUR diese Runde:\n\n{round_text}"}
        ]
        
        json_content = None
        
        for attempt in range(max_retries):
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": 150000,
                    "temperature": 0.1
                }
                
                # API Call
                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=300
                )
                
                result = response.json()

                finish_reason = result["choices"][0].get("finish_reason")
                print(f"  Finish Reason: {finish_reason}")
                print(f"  Usage: {result.get('usage', {})}")

                if finish_reason == "length":
                    print("PROBLEM: Response wurde wegen Token-Limit abgeschnitten!")

                content = result["choices"][0]["message"]["content"]
                
                # Extrahiere JSON
                json_content = self._extract_json_from_text(content)
                
                # Validiere JSON
                parsed = self._parse_json_robust(json_content)
                
                # Erfolgreich geparst
                break
                
            except json.JSONDecodeError as e:
                print(f"JSON-Parse-Fehler (Versuch {attempt + 1}/{max_retries}): {e}")
                
                if attempt < max_retries - 1:
                    # Retry mit Fehlerkorrektur
                    messages.append({
                        "role": "assistant",
                        "content": content
                    })
                    messages.append({
                        "role": "user",
                        "content": f"Das JSON war nicht valide. Fehler: {str(e)}\n\nBitte gib NUR valides JSON zurück."
                    })
                else:
                    print("Speichere trotzdem (manuell korrigieren)")
        
        # Erstelle Output-Verzeichnis
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        output_path = Path(output_directory) / f"round{round_number}_report.json"
        
        # Speichere JSON
        try:
            parsed = json.loads(json_content)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2, ensure_ascii=False)
            print(f"Runde {round_number} Report gespeichert: {output_path}")
        except:
            # Fallback: Speichere als Text
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(json_content)
            print(f"Runde {round_number} als Text gespeichert (JSON invalid): {output_path}")
        
        return str(output_path)
    
    def _extract_json_from_text(self, text: str) -> str:
        """
        Extrahiert JSON aus Text und entfernt Markdown-Code-Blöcke.
        
        Args:
            text: Rohtext der API-Response
        
        Returns:
            Bereinigter JSON-String
        """
        # Entferne Markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                return text[start:end].strip()
        
        # Fallback: Suche nach erstem {
        start = text.find("{")
        if start != -1:
            return text[start:].strip()
        
        return text.strip()
    
    def _parse_json_robust(self, json_str: str) -> dict:
        """
        Robustes JSON-Parsing mit automatischen Korrekturen.
        
        Args:
            json_str: JSON-String
        
        Returns:
            Geparste Dictionary
        
        Raises:
            json.JSONDecodeError: Wenn auch nach Korrekturen nicht parsbar
        """
        # Versuch 1: Direktes Parsing
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
        
        # Versuch 2: Entferne trailing content nach letztem }
        try:
            last_brace = json_str.rfind("}")
            if last_brace != -1:
                cleaned = json_str[:last_brace + 1]
                return json.loads(cleaned)
        except json.JSONDecodeError:
            pass
        
        # Versuch 3: Escape unescaped quotes in strings
        try:
            # Einfache Heuristik für häufige Fehler
            fixed = json_str.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass
        
        # Wenn alles fehlschlägt, raise original error
        return json.loads(json_str)

    # ==================== TEXT-BASIERTE METHODEN ====================

    def split_rounds_from_text(
        self,
        transcript_text: str,
        round_splitter_prompt: str,
        model: str,
        max_retries: int = 3
    ) -> dict:
        """
        Analysiert Transkript-Text und gibt JSON mit Runden-Zeitstempeln zurück.

        Args:
            transcript_text: Das vollständige Transkript als String
            round_splitter_prompt: System-Prompt Inhalt (nicht Pfad)
            model: OpenRouter Model-ID
            max_retries: Maximale Anzahl an Versuchen bei JSON-Fehlern

        Returns:
            Dictionary mit Runden-Info inkl. Zeitstempeln
        """
        messages = [
            {"role": "system", "content": round_splitter_prompt},
            {"role": "user", "content": transcript_text}
        ]

        for attempt in range(max_retries):
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": 150000,
                    "temperature": 0.0
                }

                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=300
                )

                result = response.json()
                content = result["choices"][0]["message"]["content"]

                json_content = self._extract_json_from_text(content)
                data = self._parse_json_robust(json_content)

                return data

            except json.JSONDecodeError as e:
                print(f"JSON-Parse-Fehler (Versuch {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": f"Das JSON war nicht valide. Fehler: {str(e)}\n\nBitte gib NUR valides JSON zurück."
                    })
                else:
                    raise

        return {}

    def split_transcript_by_rounds_from_text(
        self,
        rounds_json: dict,
        transcript_text: str
    ) -> list:
        """
        Teilt Transkript-Text in separate Runden-Texte auf (in-memory).

        Args:
            rounds_json: Dictionary aus split_rounds() mit Zeitstempeln
            transcript_text: Das vollständige Transkript als String

        Returns:
            Liste von Strings, je einer pro Runde
        """
        lines = transcript_text.split('\n')

        # Extrahiere Zeitstempel aus rounds_json
        round_timestamps = []
        for key in sorted(rounds_json.keys()):
            if key.startswith("runde_"):
                time_range = rounds_json[key].split("[")[0].strip()
                start_time = time_range.split("–")[0].strip() if "–" in time_range else time_range.split("—")[0].strip()
                round_timestamps.append(start_time)

        round_timestamps_sorted = sorted(round_timestamps, key=self._parse_timestamp)

        # Teile Transkript auf
        round_texts = []
        current_round = 0
        current_round_lines = []

        for line in lines:
            line_timestamp = self._extract_timestamp_from_line(line)

            if line_timestamp is not None:
                line_seconds = self._parse_timestamp(line_timestamp)

                if current_round < len(round_timestamps_sorted) - 1:
                    next_round_start = self._parse_timestamp(round_timestamps_sorted[current_round + 1])

                    if line_seconds >= next_round_start:
                        if current_round_lines:
                            round_texts.append('\n'.join(current_round_lines))
                        current_round += 1
                        current_round_lines = []

            current_round_lines.append(line)

        if current_round_lines:
            round_texts.append('\n'.join(current_round_lines))

        return round_texts

    def generate_report_for_round_from_text(
        self,
        round_number: int,
        round_text: str,
        system_prompt: str,
        model: str,
        max_retries: int = 2
    ) -> dict:
        """
        Generiert einen Game Report für eine Runde aus Text.

        Args:
            round_number: Nummer der Runde
            round_text: Der Runden-Text als String
            system_prompt: System-Prompt Inhalt (nicht Pfad)
            model: OpenRouter Model-ID
            max_retries: Maximale Anzahl an Versuchen bei JSON-Fehlern

        Returns:
            Dictionary mit dem Report
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Analysiere NUR diese Runde:\n\n{round_text}"}
        ]

        for attempt in range(max_retries):
            try:
                payload = {
                    "model": model,
                    "messages": messages,
                    "max_tokens": 150000,
                    "temperature": 0.1
                }

                response = requests.post(
                    self.base_url,
                    headers=self.headers,
                    json=payload,
                    timeout=300
                )

                result = response.json()
                content = result["choices"][0]["message"]["content"]
                json_content = self._extract_json_from_text(content)
                parsed = self._parse_json_robust(json_content)

                return parsed

            except json.JSONDecodeError as e:
                print(f"JSON-Parse-Fehler (Versuch {attempt + 1}/{max_retries}): {e}")

                if attempt < max_retries - 1:
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": f"Das JSON war nicht valide. Fehler: {str(e)}"
                    })
                else:
                    raise

        return {}
