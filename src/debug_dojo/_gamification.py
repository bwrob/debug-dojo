"""Gamification module for Debug Dojo.

This module handles tracking user statistics (debugging sessions) and awarding
Dojo Belts based on experience.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from rich import print as rich_print
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn

# Belt definitions: (Name, Min Sessions Required, Color)
BELTS = [
    ("White Belt", 0, "white"),
    ("Yellow Belt", 5, "yellow"),
    (
        "Orange Belt",
        15,
        "encircle_orange",
    ),  # standard orange might not exist in all themes
    ("Green Belt", 30, "green"),
    ("Blue Belt", 60, "blue"),
    ("Purple Belt", 100, "magenta"),
    ("Brown Belt", 150, "rgb(165,42,42)"),
    ("Black Belt", 250, "black on white"),
    ("Red Belt (Grandmaster)", 500, "red"),
]


@dataclass
class DojoStats:
    """User statistics model."""

    sessions: int = 0
    bugs_crushed: int = 0  # Placeholder for future feature


class GamificationManager:
    """Manages stats loading, saving, and belt progression."""

    def __init__(self, stats_path: Path | None = None) -> None:
        """Initialize the manager.

        Args:
            stats_path: Path to the stats file. If None, defaults to ~/.debug_dojo/stats.json
        """
        if stats_path:
            self.stats_file = stats_path
        else:
            self.stats_file = Path.home() / ".debug_dojo" / "stats.json"

        self.stats = self._load_stats()

    def _load_stats(self) -> DojoStats:
        """Load stats from disk."""
        if not self.stats_file.exists():
            return DojoStats()

        try:
            data = json.loads(self.stats_file.read_text(encoding="utf-8"))
            return DojoStats(**data)
        except (json.JSONDecodeError, TypeError, OSError):
            return DojoStats()

    def _save_stats(self) -> None:
        """Save stats to disk."""
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        self.stats_file.write_text(json.dumps(asdict(self.stats)), encoding="utf-8")

    def increment_session(self) -> None:
        """Record a new debugging session."""
        self.stats.sessions += 1
        self._save_stats()
        # Check for level up could happen here, but we'll keep it simple for now.

    def get_current_belt(self) -> tuple[str, str, int, int]:
        """Get current belt info.

        Returns:
            Tuple of (Belt Name, Color, Current Rank Index, Next Rank Threshold)
        """
        current_belt = BELTS[0]
        rank_index = 0

        for i, belt in enumerate(BELTS):
            if self.stats.sessions >= belt[1]:
                current_belt = belt
                rank_index = i
            else:
                break

        # Determine next threshold
        if rank_index + 1 < len(BELTS):
            next_threshold = BELTS[rank_index + 1][1]
        else:
            next_threshold = self.stats.sessions  # Maxed out

        return current_belt[0], current_belt[2], rank_index, next_threshold

    def display_status(self) -> None:
        """Print the current status to the console using Rich."""
        belt_name, color, rank_index, next_threshold = self.get_current_belt()

        # Calculate progress to next belt
        if rank_index + 1 < len(BELTS):
            prev_threshold = BELTS[rank_index][1]
            total_needed = next_threshold - prev_threshold
            current_progress = self.stats.sessions - prev_threshold
        else:
            # Max level
            total_needed = 1
            current_progress = 1

        rich_print(
            Panel(
                f"[bold {color}]{belt_name}[/bold {color}]\n"
                f"Sessions: {self.stats.sessions}",
                title="🥋 Dojo Status",
                expand=False,
            )
        )

        if rank_index + 1 < len(BELTS):
            next_belt_name = BELTS[rank_index + 1][0]
            rich_print(f"Progress to [bold]{next_belt_name}[/bold]:")

            with Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(style="dim", complete_style=color, finished_style=color),
                TextColumn("{task.completed}/{task.total}"),
            ) as progress:
                progress.add_task(
                    "Training...", total=next_threshold, completed=self.stats.sessions
                )
        else:
            rich_print(
                "[bold gold1]You have mastered the way of the Debug Dojo![/bold gold1]"
            )
