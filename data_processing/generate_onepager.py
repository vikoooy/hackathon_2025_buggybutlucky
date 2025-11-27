#!/usr/bin/env python3
"""
Matrix Wargame OnePager Generator

Liest round1_report.json und round2_report.json ein und erstellt
einen strukturierten OnePager mit den wichtigsten Spielinformationen als PDF.
"""

import json
import sys
from pathlib import Path
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER


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
        
        # Dimensionen (unterstützt beide JSON-Strukturen)
        dim_resources = phase_2.get("dimension_1_resources", {})
        
        # Komplexität kann an Position 2 oder 3 sein
        dim_complexity = phase_2.get("dimension_2_complexity", phase_2.get("dimension_3_complexity", {}))
        
        # Verteidigung kann an Position 2 oder 3 sein  
        dim_defense = phase_2.get("dimension_3_defense", phase_2.get("dimension_2_defense", {}))
        
        # Auswirkung ist immer dimension_4_attack
        dim_impact = phase_2.get("dimension_4_attack", {})
        
        resources_rating = dim_resources.get("game_master_rating", "?")
        resources_points = dim_resources.get("points_for_red", 0)
        
        defense_rating = dim_defense.get("game_master_rating", "?")
        defense_points = dim_defense.get("points_for_red", 0)
        
        complexity_rating = dim_complexity.get("game_master_rating", "?")
        complexity_points = dim_complexity.get("points_for_red", 0)
        
        impact_rating = dim_impact.get("game_master_rating", "?")
        impact_points = dim_impact.get("points_for_red", 0)
        
        # Extrahiere Timestamps für Verlinkung (letztes timestamp aus arguments)
        def get_last_timestamp(dimension_dict):
            """Extrahiert das letzte timestamp aus red_arguments und blue_arguments"""
            timestamps = []
            for arg in dimension_dict.get("red_arguments", []):
                if "timestamp" in arg:
                    timestamps.append(arg["timestamp"])
            for arg in dimension_dict.get("blue_arguments", []):
                if "timestamp" in arg:
                    timestamps.append(arg["timestamp"])
            return timestamps[-1] if timestamps else None
        
        resources_timestamp = get_last_timestamp(dim_resources)
        complexity_timestamp = get_last_timestamp(dim_complexity)
        defense_timestamp = get_last_timestamp(dim_defense)
        impact_timestamp = get_last_timestamp(dim_impact)
        
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
                "resources": {"rating": resources_rating, "points": resources_points, "timestamp": resources_timestamp},
                "defense": {"rating": defense_rating, "points": defense_points, "timestamp": defense_timestamp},
                "complexity": {"rating": complexity_rating, "points": complexity_points, "timestamp": complexity_timestamp},
                "impact": {"rating": impact_rating, "points": impact_points, "timestamp": impact_timestamp},
                "table_sum": table_sum,
                "dice_results": dice_results,
                "dice_total": dice_total,
                "success": success,
                "result_type": result_type,
                "what_happened": what_happened
            }
        }
    
    def load_transcript(self, transcript_path: str):
        """
        Lädt und verarbeitet das Transkript.
        
        Args:
            transcript_path: Pfad zur Transkript-Datei
            
        Returns:
            Verarbeiteter Transkript-Text mit umbenannten Speakern
        """
        transcript_file = Path(transcript_path)
        if not transcript_file.exists():
            print(f"Warnung: Transkript-Datei nicht gefunden: {transcript_path}")
            return None
        
        with open(transcript_file, "r", encoding="utf-8") as f:
            transcript_text = f.read()
        
        # Ersetze Speaker-Namen
        transcript_text = transcript_text.replace("Speaker 1:", "Team Rot:")
        transcript_text = transcript_text.replace("Speaker 1 ", "Team Rot ")
        transcript_text = transcript_text.replace("Speaker 2:", "Team Blau:")
        transcript_text = transcript_text.replace("Speaker 2 ", "Team Blau ")
        transcript_text = transcript_text.replace("Speaker 0 (Moderator):", "Moderator:")
        transcript_text = transcript_text.replace("Speaker 0:", "Moderator:")
        
        return transcript_text
    
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
    
    def generate_onepager_pdf(self, output_path: str, transcript_path: str = None):
        """
        Generiert den OnePager als PDF-Datei.
        
        Args:
            output_path: Pfad zur Output-Datei
            transcript_path: Pfad zur Transkript-Datei (optional)
        """
        print("Generiere OnePager PDF...\n")
        
        # Lade Transkript falls vorhanden
        transcript_text = None
        if transcript_path:
            transcript_text = self.load_transcript(transcript_path)
            if transcript_text:
                print(f"  ✓ Transkript geladen: {transcript_path}\n")
        
        # Extrahiere Daten
        red_name, blue_name = self.extract_participants()
        attack_results = self.extract_attack_results()
        defense = self.extract_defense_measures()
        progression = self.extract_attack_progression()
        vulnerabilities = self.extract_vulnerabilities()
        
        # PDF Setup
        output_file = Path(output_path)
        doc = SimpleDocTemplate(
            str(output_file),
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Styles
        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor='black',
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor='black',
            spaceAfter=10,
            spaceBefore=10,
            fontName='Helvetica-Bold'
        )
        
        subheading_style = ParagraphStyle(
            'CustomSubHeading',
            parent=styles['Heading3'],
            fontSize=12,
            textColor='black',
            spaceAfter=8,
            spaceBefore=8,
            fontName='Helvetica-Bold'
        )
        
        normal_style = ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            textColor='black',
            spaceAfter=6,
            fontName='Helvetica'
        )
        
        bullet_style = ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontSize=10,
            textColor='black',
            leftIndent=20,
            spaceAfter=4,
            fontName='Helvetica'
        )
        
        # Story (Content)
        story = []
        
        # Titel
        story.append(Paragraph("MATRIX WARGAME - ONE PAGER", title_style))
        story.append(Paragraph(
            f"Generiert am: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            normal_style
        ))
        story.append(Spacer(1, 0.5*cm))
        
        # Teilnehmer
        story.append(Paragraph("TEILNEHMER", heading_style))
        story.append(Paragraph(f"• {red_name} = Rot (Angreifer)", bullet_style))
        story.append(Paragraph(f"• {blue_name} = Blau (Verteidiger)", bullet_style))
        story.append(Spacer(1, 0.3*cm))
        
        # Angriffsergebnisse
        story.append(Paragraph("ANGRIFFSERGEBNISSE", heading_style))
        for result in attack_results:
            status = "Erfolgreich" if result["success"] else "Fehlgeschlagen"
            story.append(Paragraph(
                f"• Runde {result['round']}: {result['category']}-Angriff auf {result['target']}",
                bullet_style
            ))
            story.append(Paragraph(
                f"  Status: {status} ({result['result_type']})",
                bullet_style
            ))
        story.append(Spacer(1, 0.3*cm))
        
        # Verteidigungsmaßnahmen
        story.append(Paragraph("VERTEIDIGUNGSMASSNAHMEN DER BWI", heading_style))
        story.append(Paragraph("Stärken:", subheading_style))
        if defense["strengths"]:
            for strength in defense["strengths"]:
                story.append(Paragraph(f"• {strength}", bullet_style))
        else:
            story.append(Paragraph("• Keine dokumentiert", bullet_style))
        
        story.append(Paragraph("Schwächen:", subheading_style))
        if defense["weaknesses"]:
            for weakness in defense["weaknesses"]:
                story.append(Paragraph(f"• {weakness}", bullet_style))
        else:
            story.append(Paragraph("• Keine dokumentiert", bullet_style))
        
        story.append(Paragraph(
            f"Effektivste Verteidigung: {defense['most_effective']}",
            normal_style
        ))
        story.append(Spacer(1, 0.3*cm))
        
        # Angriffsverläufe
        story.append(Paragraph("ANGRIFFSVERLÄUFE", heading_style))
        story.append(Paragraph(f"Strategieentwicklung: {progression['evolution']}", normal_style))
        story.append(Paragraph(f"Effektivster Angriff: {progression['most_effective']}", normal_style))
        if progression["weaknesses"]:
            story.append(Paragraph("Aufgedeckte Schwächen von Rot:", subheading_style))
            for weakness in progression["weaknesses"]:
                story.append(Paragraph(f"• {weakness}", bullet_style))
        story.append(Spacer(1, 0.3*cm))
        
        # Schwachstellen
        story.append(Paragraph("SCHWACHSTELLEN DIE DEN ANGRIFF ERMÖGLICHT HABEN", heading_style))
        if vulnerabilities:
            for vuln in vulnerabilities:
                vuln_text = vuln.get("vulnerability", "Unbekannt")
                round_num = vuln.get("exploited_in_round", "?")
                effectiveness = vuln.get("effectiveness", "unbekannt")
                story.append(Paragraph(f"• {vuln_text}", bullet_style))
                story.append(Paragraph(
                    f"  Ausgenutzt in Runde {round_num} (Effektivität: {effectiveness})",
                    bullet_style
                ))
        else:
            story.append(Paragraph("• Keine spezifischen Schwachstellen dokumentiert", bullet_style))
        
        # Neue Seite für detaillierte Runden
        story.append(PageBreak())
        
        # Detaillierte Runden-Informationen
        story.append(Paragraph("DETAILLIERTE RUNDENÜBERSICHT", title_style))
        story.append(Spacer(1, 0.5*cm))
        
        for round_num in range(1, len(self.reports) + 1):
            details = self.extract_round_details(round_num)
            if not details:
                continue
            
            story.append(Paragraph(f"RUNDE {round_num}", heading_style))
            
            # Phase 1
            story.append(Paragraph("Phase 1: Aufklärung", subheading_style))
            p1 = details["phase_1"]
            
            if p1["blue_success"]:
                story.append(Paragraph(
                    f"• Blau hat die 12 erreicht (Summe: {p1['blue_total']})",
                    bullet_style
                ))
                story.append(Paragraph(
                    "  → Intelvorteil von Rot ist OFFENGELEGT",
                    bullet_style
                ))
            else:
                story.append(Paragraph(
                    f"• Blau hat die 12 nicht erreicht (Summe: {p1['blue_total']})",
                    bullet_style
                ))
                story.append(Paragraph(
                    "  → Intelvorteil von Rot ist GEHEIM",
                    bullet_style
                ))
            
            story.append(Paragraph(f"• Rot: {p1['intel_description']}", bullet_style))
            story.append(Spacer(1, 0.2*cm))
            
            # Phase 2
            story.append(Paragraph("Phase 2: Angriff", subheading_style))
            p2 = details["phase_2"]
            
            # Funktion zum Erstellen verlinkter Dimension-Texte
            def create_dimension_text(label, rating, points, timestamp):
                if timestamp and transcript_text:
                    # Erstelle Anker-Name aus Timestamp
                    anchor = f"ts_{timestamp.replace(':', '_')}"
                    return f'• {label}: <link href="#{anchor}" color="blue">{rating} ({points})</link>'
                else:
                    return f'• {label}: {rating} ({points})'
            
            story.append(Paragraph(
                create_dimension_text("Ressourcen", p2['resources']['rating'], 
                                    p2['resources']['points'], p2['resources'].get('timestamp')),
                bullet_style
            ))
            story.append(Paragraph(
                create_dimension_text("Komplexität", p2['complexity']['rating'], 
                                    p2['complexity']['points'], p2['complexity'].get('timestamp')),
                bullet_style
            ))
            story.append(Paragraph(
                create_dimension_text("Verteidigung", p2['defense']['rating'], 
                                    p2['defense']['points'], p2['defense'].get('timestamp')),
                bullet_style
            ))
            story.append(Paragraph(
                create_dimension_text("Auswirkung", p2['impact']['rating'], 
                                    p2['impact']['points'], p2['impact'].get('timestamp')),
                bullet_style
            ))
            story.append(Paragraph(f"• Tabellensumme: {p2['table_sum']}", bullet_style))
            story.append(Spacer(1, 0.2*cm))
            
            # Erfolgswurf
            success_text = "erfolgreich" if p2["success"] else "nicht ausreichend"
            story.append(Paragraph(f"• Erfolgswurf von Rot: {success_text}", bullet_style))
            story.append(Paragraph(
                f"  Würfelergebnisse: {p2['dice_results']} (Summe: {p2['dice_total']})",
                bullet_style
            ))
            story.append(Paragraph(f"• Ergebnis: {p2['result_type']}", bullet_style))
            story.append(Spacer(1, 0.2*cm))
            
            story.append(Paragraph("• Auswirkungen:", bullet_style))
            story.append(Paragraph(f"  {p2['what_happened']}", bullet_style))
            
            # Spacer zwischen Runden
            if round_num < len(self.reports):
                story.append(Spacer(1, 0.5*cm))
        
        # Transkript-Sektion hinzufügen
        if transcript_text:
            story.append(PageBreak())
            story.append(Paragraph("VOLLSTÄNDIGES TRANSKRIPT", title_style))
            story.append(Spacer(1, 0.5*cm))
            
            # Style für Transkript
            transcript_style = ParagraphStyle(
                'TranscriptStyle',
                parent=styles['Normal'],
                fontSize=9,
                textColor='black',
                spaceAfter=4,
                fontName='Helvetica',
                leading=12
            )
            
            # Verarbeite Transkript Zeile für Zeile und füge Anker hinzu
            lines = transcript_text.split('\n')
            for line in lines:
                if line.strip():
                    # Prüfe ob Zeile mit Timestamp beginnt (Format: HH:MM–HH:MM)
                    if '–' in line[:10]:
                        # Extrahiere ersten Timestamp
                        try:
                            timestamp_part = line.split()[0]  # z.B. "00:00–00:16"
                            start_time = timestamp_part.split('–')[0]  # z.B. "00:00"
                            anchor = f"ts_{start_time.replace(':', '_')}"
                            # Füge unsichtbaren Anker hinzu
                            line_with_anchor = f'<a name="{anchor}"/>{line}'
                            story.append(Paragraph(line_with_anchor, transcript_style))
                        except:
                            story.append(Paragraph(line, transcript_style))
                    else:
                        story.append(Paragraph(line, transcript_style))
        
        # Build PDF
        doc.build(story)
        
        print(f"✅ OnePager PDF erstellt: {output_file}")


def main():
    """Hauptfunktion."""
    
    print("=" * 80)
    print("MATRIX WARGAME - ONEPAGER GENERATOR (PDF)")
    print("=" * 80)
    print()
    
    # Konfiguration
    REPORT_DIR = "data/reports"
    OUTPUT_FILE = "data/reports/game_onepager.pdf"
    
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
    
    # Erstelle OnePager PDF mit Transkript
    transcript_path = f"{REPORT_DIR}/../transcript.txt"  # data/transcript.txt
    generator.generate_onepager_pdf(OUTPUT_FILE, transcript_path)
    
    print()
    print("=" * 80)
    print("✅ ONEPAGER PDF ERFOLGREICH GENERIERT!")
    print("=" * 80)
    print(f"\nGenerierte Dateien:")
    print(f"  • OnePager PDF: {OUTPUT_FILE}")
    print(f"  • Kombinierte JSON: {REPORT_DIR}/game_report_combined.json")


if __name__ == "__main__":
    main()