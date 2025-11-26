import os
import re
import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Callable, Optional
from pathlib import Path
import sys

# Add data_processing to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from data_processing.wargame_analyzer import WargameAnalyzer


class PipelineService:
    """Service for running data processing pipeline."""

    def __init__(
        self,
        api_key: str = None,
        model: str = "anthropic/claude-3.5-sonnet"
    ):
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY not configured")

        self.model = model
        self.analyzer = WargameAnalyzer(api_key=self.api_key)
        self._executor = ThreadPoolExecutor(max_workers=2)

        # Load system prompts
        prompts_dir = Path(__file__).parent.parent.parent.parent / "data_processing"
        self.round_splitter_prompt = (prompts_dir / "systemprompt_split_rounds.txt").read_text(encoding="utf-8")
        self.game_report_prompt = (prompts_dir / "systemprompt_json.txt").read_text(encoding="utf-8")

    def _convert_transcript_format(self, transcript: str) -> str:
        """
        Convert from audio pipeline format to data_processing format.

        Input:  HH:MM:SS Speaker 0 (Moderator): "text"
        Output: MM:SS-MM:SS Speaker 0 (Moderator): "text"
        """
        lines = transcript.split('\n')
        converted = []

        for i, line in enumerate(lines):
            # Match HH:MM:SS pattern at start of line
            match = re.match(r'(\d{2}):(\d{2}):(\d{2})\s+(.+)', line)
            if match:
                hours, mins, secs, rest = match.groups()

                # Calculate total minutes for start
                total_mins = int(hours) * 60 + int(mins)

                # Calculate end time from next line or estimate
                end_mins = total_mins
                end_secs = secs

                if i + 1 < len(lines):
                    next_match = re.match(r'(\d{2}):(\d{2}):(\d{2})', lines[i + 1])
                    if next_match:
                        next_hours = int(next_match.group(1))
                        next_mins_raw = int(next_match.group(2))
                        next_secs = next_match.group(3)
                        end_mins = next_hours * 60 + next_mins_raw
                        end_secs = next_secs

                # Format: MM:SS-MM:SS rest
                converted.append(f"{total_mins:02d}:{secs}–{end_mins:02d}:{end_secs} {rest}")
            else:
                converted.append(line)

        return '\n'.join(converted)

    async def run_pipeline(
        self,
        transcript: str,
        progress_callback: Callable[[int, str, str], Any] = None
    ) -> Dict[str, Any]:
        """
        Run full pipeline on transcript.

        Args:
            transcript: Formatted transcript text from audio pipeline
            progress_callback: Async callback(progress_pct, step, step_name)

        Returns:
            Dict with rounds_overview, rounds, combined report
        """
        result = {
            "rounds_overview": None,
            "rounds": [],
            "combined": None,
            "errors": []
        }

        # Convert transcript format
        converted_transcript = self._convert_transcript_format(transcript)

        # Step 1: Split rounds (70-80%)
        if progress_callback:
            await progress_callback(70, "splitting", "Erkenne Runden-Grenzen...")

        try:
            loop = asyncio.get_event_loop()
            rounds_json = await loop.run_in_executor(
                self._executor,
                lambda: self.analyzer.split_rounds_from_text(
                    converted_transcript,
                    self.round_splitter_prompt,
                    self.model
                )
            )
            result["rounds_overview"] = rounds_json
        except Exception as e:
            result["errors"].append(f"Round splitting failed: {str(e)}")
            # Fall back to treating entire transcript as one round
            rounds_json = {"runde_1": "00:00–END [Gesamtes Spiel]"}
            result["rounds_overview"] = rounds_json

        if progress_callback:
            await progress_callback(80, "extracting", "Extrahiere Runden-Texte...")

        # Step 2: Extract round texts
        try:
            round_texts = self.analyzer.split_transcript_by_rounds_from_text(
                rounds_json,
                converted_transcript
            )
        except Exception as e:
            result["errors"].append(f"Round text extraction failed: {str(e)}")
            round_texts = [converted_transcript]  # Fallback: entire transcript

        # Step 3: Generate reports (80-98%)
        num_rounds = len(round_texts)
        for i, round_text in enumerate(round_texts, start=1):
            progress_pct = 80 + int((i / num_rounds) * 18)

            if progress_callback:
                await progress_callback(
                    progress_pct,
                    f"report_round_{i}",
                    f"Analysiere Runde {i} von {num_rounds}..."
                )

            try:
                loop = asyncio.get_event_loop()
                report = await loop.run_in_executor(
                    self._executor,
                    lambda rt=round_text, rn=i: self.analyzer.generate_report_for_round_from_text(
                        rn,
                        rt,
                        self.game_report_prompt,
                        self.model
                    )
                )
                result["rounds"].append(report)
            except Exception as e:
                result["errors"].append(f"Round {i} report failed: {str(e)}")
                result["rounds"].append(None)

        # Step 4: Combine reports (98-100%)
        if progress_callback:
            await progress_callback(98, "combining", "Erstelle Gesamtbericht...")

        result["combined"] = self._combine_reports(result["rounds_overview"], result["rounds"])

        return result

    def _combine_reports(
        self,
        rounds_overview: dict,
        round_reports: list
    ) -> dict:
        """Combine individual round reports into a final combined report."""
        if not round_reports or all(r is None for r in round_reports):
            return None

        # Use first valid report as base
        combined = None
        all_rounds = []

        for i, report in enumerate(round_reports):
            if report is None:
                continue

            if combined is None:
                combined = report.copy()

            # Extract rounds from report
            if "rounds" in report:
                for round_data in report["rounds"]:
                    round_data["round_number"] = i + 1
                    all_rounds.append(round_data)

        if combined:
            combined["rounds"] = all_rounds
            combined["rounds_overview"] = rounds_overview

        return combined
