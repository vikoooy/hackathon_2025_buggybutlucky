#!/usr/bin/env python3
"""
Matrix Wargame OnePager Generator

Liest round1_report.json und round2_report.json ein und erstellt
einen strukturierten OnePager mit den wichtigsten Spielinformationen.
"""

import json
import sys
from pathlib import Path
from datetime import datetime


class OnePagerGenerator:
    """Generiert OnePager aus Game Reports."""
    
    def __init__(self, report_dir: str):
        """
        Initialisiert Generator.
        
        Args:
            report_dir: Verzeichnis mit den round*_report.json Dateien
        """
        self.report_dir = Path(report_dir)
        self.reports = []
        
    def load_reports(self):
        """Lädt alle round*_report.json Dateien."""
        print("Lade Game Reports...")
        
        # Finde alle round*_report.json Dateien
        report_files = sorted(self.report_dir.glob("round*_report.json"))
        
        if not report_files:
            print(f"Keine Report-Dateien in {self.report_dir} gefunden!")
            sys.exit(1)
        
        for report_file in report_files:
            with open(report_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.reports.append(data)
                print(f"  ✓ {report_file.name} geladen")
        
        print(f"\n✅ {len(self.reports)} Reports geladen\n")
    
    def extract_participants(self):
        """Extrahiert Teilnehmer aus dem ersten Report."""
        if not self.reports:
            return "Unbekannt", "Unbekannt"
        
        metadata = self.reports[0].get("game_metadata", {})
        participants = metadata.get("participants", {})
        
        # Team Rot
        red_team = participants.get("team_red", {})
        red_players = red_team.get("players", [])
        red_name = red_players[0] if red_players else "Unbekannt"
        
        # Team Blau
        blue_team = participants.get("team_blue", {})
        blue_players = blue_team.get("players", [])
        blue_name = blue_players[0] if blue_players else "Unbekannt"
        
        return red_name, blue_name
    
    def extract_attack_results(self):
        """Extrahiert Angriffsergebnisse aller Runden."""
        results = []
        
        for i, report in enumerate(self.reports, start=1):
            rounds = report.get("rounds", [])
            if not rounds:
                continue
            
            round_data = rounds[0]  # Jeder Report enthält nur eine Runde
            phase_2 = round_data.get("phase_2_angriff", {})
            
            # Angriffskategorie und Ziel
            attack_ann = phase_2.get("attack_announcement", {})
            category = attack_ann.get("category_revealed", "Unbekannt")
            target = attack_ann.get("target", "Unbekannt")
            
            # Erfolgswurf
            success_roll = phase_2.get("success_roll", {})
            success = success_roll.get("success", False)
            result_type = success_roll.get("result_type", "Unbekannt")
            
            results.append({
                "round": i,
                "category": category,
                "target": target,
                "success": success,
                "result_type": result_type
            })
        
        return results
    
    def extract_defense_measures(self):
        """Extrahiert Verteidigungsmaßnahmen von Blau."""
        summary = self.reports[0].get("game_summary", {}) if self.reports else {}
        defense = summary.get("defense_measures", {})
        
        strengths = defense.get("blue_strengths", [])
        weaknesses = defense.get("blue_weaknesses", [])
        most_effective = defense.get("most_effective_defense", "Keine Angabe")
        
        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "most_effective": most_effective
        }
    
    def extract_attack_progression(self):
        """Extrahiert Angriffsverlauf und Strategieentwicklung."""
        summary = self.reports[0].get("game_summary", {}) if self.reports else {}
        progression = summary.get("attack_progression", {})
        
        evolution = progression.get("red_strategy_evolution", "Keine Angabe")
        most_effective = progression.get("most_effective_attack", "Keine Angabe")
        weaknesses = progression.get("red_weaknesses_exposed", [])
        
        return {
            "evolution": evolution,
            "most_effective": most_effective,
            "weaknesses": weaknesses
        }
    
    def extract_vulnerabilities(self):
        """Extrahiert identifizierte Schwachstellen."""
        summary = self.reports[0].get("game_summary", {}) if self.reports else {}
        vulns = summary.get("vulnerabilities_identified", [])
        
        return vulns
    
    def extract_round_details(self, round_number: int):
        """
        Extrahiert detaillierte Informationen einer Runde.
        
        Args:
            round_number: Rundennummer (1-basiert)
        
        Returns:
            Dictionary mit Runden-Details
        """
        if round_number > len(self.reports):
            return None
        
        report = self.reports[round_number - 1]
        rounds = report.get("rounds", [])
        if not rounds:
            return None
        
        round_data = rounds[0]
        
        # Phase 1: Aufklärung
        phase_1 = round_data.get("phase_1_aufklaerung", {})
        blue_counter = phase_1.get("blue_counter_intelligence", {})
        red_espionage = phase_1.get("red_espionage", {})
        
        blue_total = blue_counter.get("total", 0)
        blue_success = blue_counter.get("success", False)
        
        red_dice = red_espionage.get("dice_results", [])
        intel_gained = red_espionage.get("intelligence_gained", {})
        
        # Analysiere Rot's Intel (vereinfacht)
        intel_description = "Kein Intelvorteil"
        if red_dice:
            # Beispiel-Logik: Wenn erste Würfel >= 4, dann Intel-Vorteil
            dice_1 = int(red_dice[0]) if len(red_dice) > 0 else 0
            dice_2 = int(red_dice[1]) if len(red_dice) > 1 else 0
            
            if dice_1 >= 4:
                bonus = dice_1 - 3  # Vereinfachte Berechnung
                target_type = "unbekannt"
                
                # Versuche aus intelligence_gained zu extrahieren
                vulns = intel_gained.get("vulnerabilities_identified", [])
                if vulns:
                    # Extrahiere Art des Ziels aus Schwachstellen-Beschreibung
                    vuln_text = str(vulns).lower()
                    if "personal" in vuln_text or "mitarbeiter" in vuln_text:
                        target_type = "Personal"
                    elif "system" in vuln_text or "infrastruktur" in vuln_text:
                        target_type = "Systeme"
                    elif "prozess" in vuln_text:
                        target_type = "Prozesse"
                
                intel_description = f"Intelvorteil von +{bonus} auf Angriffe gegen {target_type} (da {dice_1} gewürfelt)"
            else:
                intel_description = f"Kein Intelvorteil (da {dice_1} gewürfelt)"
        
        # Phase 2: Angriff
        phase_2 = round_data.get("phase_2_angriff", {})
        
        # Dimensionen
        dim_resources = phase_2.get("dimension_1_resources", {})
        dim_defense = phase_2.get("dimension_2_defense", {})
        dim_complexity = phase_2.get("dimension_3_complexity", {})
        dim_impact = phase_2.get("dimension_4_impact", {})
        
        resources_rating = dim_resources.get("game_master_rating", "?")
        resources_points = dim_resources.get("points_for_red", 0)
        
        defense_rating = dim_defense.get("game_master_rating", "?")
        defense_points = dim_defense.get("points_for_red", 0)
        
        complexity_rating = dim_complexity.get("game_master_rating", "?")
        complexity_points = dim_complexity.get("points_for_red", 0)
        
        impact_rating = dim_impact.get("game_master_rating", "?")
        impact_points = dim_impact.get("points_for_red", 0)
        
        table_sum = resources_points + defense_points + complexity_points + impact_points
        
        # Erfolgswurf
        success_roll = phase_2.get("success_roll", {})
        dice_results = success_roll.get("dice_results", [])
        dice_total = success_roll.get("dice_total", 0)
        success = success_roll.get("success", False)
        result_type = success_roll.get("result_type", "Unbekannt")
        what_happened = success_roll.get("what_happened", "Keine Beschreibung vorhanden")
        
        return {
            "phase_1": {
                "blue_total": blue_total,
                "blue_success": blue_success,
                "intel_description": intel_description
            },
            "phase_2": {
                "resources": {"rating": resources_rating, "points": resources_points},
                "defense": {"rating": defense_rating, "points": defense_points},
                "complexity": {"rating": complexity_rating, "points": complexity_points},
                "impact": {"rating": impact_rating, "points": impact_points},
                "table_sum": table_sum,
                "dice_results": dice_results,
                "dice_total": dice_total,
                "success": success,
                "result_type": result_type,
                "what_happened": what_happened
            }
        }
    
    def generate_combined_json(self, output_path: str):
        """
        Erstellt eine finale JSON-Datei mit allen Runden kombiniert.
        
        Args:
            output_path: Pfad zur kombinierten JSON-Datei
        """
        print("Kombiniere Reports zu finaler JSON...\n")
        
        if not self.reports:
            print("Keine Reports zum Kombinieren vorhanden!")
            return
        
        # Basis: Erster Report als Vorlage
        combined_report = self.reports[0].copy()
        
        # Sammle alle Runden aus allen Reports
        all_rounds = []
        for i, report in enumerate(self.reports, start=1):
            rounds = report.get("rounds", [])
            if rounds:
                # Setze korrekte round_number
                round_data = rounds[0].copy()
                round_data["round_number"] = i
                all_rounds.append(round_data)
                print(f"  ✓ Runde {i} hinzugefügt")
        
        # Ersetze rounds Array mit allen Runden
        combined_report["rounds"] = all_rounds
        
        # Aktualisiere game_summary falls vorhanden
        # (Nehme Summary vom letzten Report, da dieser alle Runden berücksichtigt)
        if len(self.reports) > 1 and "game_summary" in self.reports[-1]:
            combined_report["game_summary"] = self.reports[-1]["game_summary"]
        
        # Speichere kombinierte JSON
        output_file = Path(output_path)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(combined_report, f, indent=2, ensure_ascii=False)
        
        print(f"\nFinale JSON erstellt: {output_file}")
        print(f"   Enthält {len(all_rounds)} Runden")
    
    def generate_onepager(self, output_path: str):
        """
        Generiert den OnePager als Text-Datei.
        
        Args:
            output_path: Pfad zur Output-Datei
        """
        print("Generiere OnePager...\n")
        
        # Extrahiere Daten
        red_name, blue_name = self.extract_participants()
        attack_results = self.extract_attack_results()
        defense = self.extract_defense_measures()
        progression = self.extract_attack_progression()
        vulnerabilities = self.extract_vulnerabilities()
        
        # Erstelle OnePager-Text
        lines = []
        lines.append("=" * 80)
        lines.append("MATRIX WARGAME - ONE PAGER")
        lines.append("=" * 80)
        lines.append(f"Generiert am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")
        
        # Teilnehmer
        lines.append("TEILNEHMER")
        lines.append("-" * 80)
        lines.append(f"• {red_name} = Rot (Angreifer)")
        lines.append(f"• {blue_name} = Blau (Verteidiger)")
        lines.append("")
        
        # Angriffsergebnisse
        lines.append("ANGRIFFSERGEBNISSE")
        lines.append("-" * 80)
        for result in attack_results:
            status = "Erfolgreich" if result["success"] else "Fehlgeschlagen"
            lines.append(f"• Runde {result['round']}: {result['category']}-Angriff auf {result['target']}")
            lines.append(f"  Status: {status} ({result['result_type']})")
        lines.append("")
        
        # Verteidigungsmaßnahmen
        lines.append("VERTEIDIGUNGSMASSNAHMEN DER BWI")
        lines.append("-" * 80)
        lines.append("Stärken:")
        for strength in defense["strengths"]:
            lines.append(f"  • {strength}")
        if not defense["strengths"]:
            lines.append("  • Keine dokumentiert")
        lines.append("")
        lines.append("Schwächen:")
        for weakness in defense["weaknesses"]:
            lines.append(f"  • {weakness}")
        if not defense["weaknesses"]:
            lines.append("  • Keine dokumentiert")
        lines.append("")
        lines.append(f"Effektivste Verteidigung: {defense['most_effective']}")
        lines.append("")
        
        # Angriffsverläufe
        lines.append("ANGRIFFSVERLÄUFE")
        lines.append("-" * 80)
        lines.append(f"Strategieentwicklung: {progression['evolution']}")
        lines.append(f"Effektivster Angriff: {progression['most_effective']}")
        if progression["weaknesses"]:
            lines.append("Aufgedeckte Schwächen von Rot:")
            for weakness in progression["weaknesses"]:
                lines.append(f"  • {weakness}")
        lines.append("")
        
        # Schwachstellen
        lines.append("SCHWACHSTELLEN DIE DEN ANGRIFF ERMÖGLICHT HABEN")
        lines.append("-" * 80)
        if vulnerabilities:
            for vuln in vulnerabilities:
                vuln_text = vuln.get("vulnerability", "Unbekannt")
                round_num = vuln.get("exploited_in_round", "?")
                effectiveness = vuln.get("effectiveness", "unbekannt")
                lines.append(f"• {vuln_text}")
                lines.append(f"  Ausgenutzt in Runde {round_num} (Effektivität: {effectiveness})")
        else:
            lines.append("• Keine spezifischen Schwachstellen dokumentiert")
        lines.append("")
        
        # Detaillierte Runden-Informationen
        lines.append("=" * 80)
        lines.append("DETAILLIERTE RUNDENÜBERSICHT")
        lines.append("=" * 80)
        lines.append("")
        
        for round_num in range(1, len(self.reports) + 1):
            details = self.extract_round_details(round_num)
            if not details:
                continue
            
            lines.append(f"RUNDE {round_num}")
            lines.append("-" * 80)
            
            # Phase 1
            lines.append("Phase 1: Aufklärung")
            p1 = details["phase_1"]
            
            if p1["blue_success"]:
                lines.append(f"  • Blau hat die 12 erreicht (Summe: {p1['blue_total']})")
                lines.append(f"    → Intelvorteil von Rot ist OFFENGELEGT")
            else:
                lines.append(f"  • Blau hat die 12 nicht erreicht (Summe: {p1['blue_total']})")
                lines.append(f"    → Intelvorteil von Rot ist GEHEIM")
            
            lines.append(f"  • Rot: {p1['intel_description']}")
            lines.append("")
            
            # Phase 2
            lines.append("Phase 2: Angriff")
            p2 = details["phase_2"]
            
            lines.append(f"  • Ressourcen: {p2['resources']['rating']} ({p2['resources']['points']})")
            lines.append(f"  • Komplexität: {p2['complexity']['rating']} ({p2['complexity']['points']})")
            lines.append(f"  • Verteidigung: {p2['defense']['rating']} ({p2['defense']['points']})")
            lines.append(f"  • Auswirkung: {p2['impact']['rating']} ({p2['impact']['points']})")
            lines.append(f"  • Tabellensumme: {p2['table_sum']}")
            lines.append("")
            
            # Erfolgswurf
            success_text = "erfolgreich" if p2["success"] else "nicht ausreichend"
            lines.append(f"  • Erfolgswurf von Rot: {success_text}")
            lines.append(f"    Würfelergebnisse: {p2['dice_results']} (Summe: {p2['dice_total']})")
            lines.append(f"  • Ergebnis: {p2['result_type']}")
            lines.append("")
            lines.append(f"  • Auswirkungen:")
            # Formatiere Beschreibung (max 70 Zeichen pro Zeile)
            description = p2["what_happened"]
            import textwrap
            wrapped_lines = textwrap.wrap(description, width=70)
            for wrapped_line in wrapped_lines:
                lines.append(f"    {wrapped_line}")
            lines.append("")
        
        lines.append("=" * 80)
        lines.append("ENDE DES REPORTS")
        lines.append("=" * 80)
        
        # Schreibe in Datei
        output_file = Path(output_path)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        
        print(f"✅ OnePager erstellt: {output_file}")
        print(f"   Anzahl Zeilen: {len(lines)}")


def main():
    """Hauptfunktion."""
    
    print("=" * 80)
    print("MATRIX WARGAME - ONEPAGER GENERATOR")
    print("=" * 80)
    print()
    
    # Konfiguration
    REPORT_DIR = "data/reports"
    OUTPUT_FILE = "data/reports/game_onepager.txt"
    
    # Bei Bedarf Pfade aus Kommandozeile übernehmen
    if len(sys.argv) >= 2:
        REPORT_DIR = sys.argv[1]
    if len(sys.argv) >= 3:
        OUTPUT_FILE = sys.argv[2]
    
    print(f"Report-Verzeichnis: {REPORT_DIR}")
    print(f"Output-Datei: {OUTPUT_FILE}")
    print()
    
    # Generiere OnePager und kombinierte JSON
    generator = OnePagerGenerator(REPORT_DIR)
    generator.load_reports()
    
    # Erstelle kombinierte JSON mit allen Runden
    combined_json_path = f"{REPORT_DIR}/game_report_combined.json"
    generator.generate_combined_json(combined_json_path)
    
    print()
    
    # Erstelle OnePager
    generator.generate_onepager(OUTPUT_FILE)
    
    print()
    print("=" * 80)
    print("✅ ONEPAGER ERFOLGREICH GENERIERT!")
    print("=" * 80)
    print(f"\nGenerierte Dateien:")
    print(f"  • OnePager: {OUTPUT_FILE}")
    print(f"  • Kombinierte JSON: {REPORT_DIR}/game_report_combined.json")


if __name__ == "__main__":
    main()
