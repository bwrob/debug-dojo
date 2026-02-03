"""Gamification module for Debug Dojo.

This module handles tracking user statistics (debugging sessions) and awarding
Dojo Belts based on experience.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from rich import print as rich_print
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn

# Belt definitions: (Name, Min Sessions, Min Minutes, Color)
BELTS = [
    ("White Belt", 0, 0, "white"),
    ("Yellow Belt", 5, 10, "yellow"),
    ("Orange Belt", 15, 30, "encircle_orange"),
    ("Green Belt", 30, 60, "green"),
    ("Blue Belt", 60, 120, "blue"),
    ("Purple Belt", 100, 240, "magenta"),
    ("Brown Belt", 150, 480, "rgb(165,42,42)"),
    ("Black Belt", 250, 1000, "black on white"),
    ("Red Belt (Grandmaster)", 500, 2000, "red"),
]


@dataclass
class SessionInfo:
    """Information about a single debugging session.

    Attributes:
        timestamp: ISO 8601 formatted string of the session start time.
        duration_minutes: Duration of the session in minutes.
        command: The command used to start the session.

    """

    timestamp: str  # ISO 8601 string
    duration_minutes: float
    command: str


@dataclass
class DojoStats:
    """User statistics model.

    Attributes:
        sessions: Total number of debugging sessions.
        bugs_crushed: Placeholder for future feature (bugs fixed count).
        history: List of past debugging sessions.

    """

    sessions: int = 0
    bugs_crushed: int = 0  # Placeholder for future feature
    history: list[SessionInfo] = field(default_factory=list)

    @property
    def total_minutes(self) -> float:
        """Calculate total minutes spent debugging."""
        return sum(s.duration_minutes for s in self.history)


class GamificationManager:
    """Manages stats loading, saving, and belt progression."""

    stats_file: Path

    stats: DojoStats

    def __init__(self, stats_path: Path | None = None) -> None:
        """Initialize the manager.

        Args:
            stats_path: Path to the stats file. If None, defaults to


                        ~/.debug_dojo/stats.json


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
            data = json.loads(self.stats_file.read_text(encoding="utf-8"))  # pyright: ignore[reportAny]

            if not isinstance(data, dict):
                return DojoStats()

            data_dict = cast("dict[str, object]", data)

            history_raw = cast("list[dict[str, object]]", data_dict.get("history", []))
            history: list[SessionInfo] = []
            for s in history_raw:
                # Support migration from duration_seconds
                duration = float(cast("float", s.get("duration_minutes", 0.0)))
                if "duration_seconds" in s and duration == 0:
                    duration = (
                        float(cast("float", s.get("duration_seconds", 0.0))) / 60.0
                    )

                history.append(
                    SessionInfo(
                        timestamp=str(s.get("timestamp", "")),
                        duration_minutes=duration,
                        command=str(s.get("command", "")),
                    )
                )

            return DojoStats(
                sessions=int(cast("int", data_dict.get("sessions", 0))),
                bugs_crushed=int(cast("int", data_dict.get("bugs_crushed", 0))),
                history=history,
            )

        except (json.JSONDecodeError, TypeError, OSError):
            return DojoStats()

    def _save_stats(self) -> None:
        """Save stats to disk."""
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)

        _ = self.stats_file.write_text(json.dumps(asdict(self.stats)), encoding="utf-8")

    def increment_session(self, duration_seconds: float, command: str) -> None:
        """Record a new debugging session.

        Args:
            duration_seconds: How long the session lasted.
            command: The command used to start the session.

        """
        self.stats.sessions += 1
        session = SessionInfo(
            timestamp=datetime.now(timezone.utc).isoformat(),
            duration_minutes=duration_seconds / 60.0,
            command=command,
        )
        self.stats.history.append(session)
        self._save_stats()

    def get_current_belt(self) -> tuple[str, str, int, int, float]:
        """Get current belt info.

        Returns:
            Tuple of (Belt Name, Color, Current Rank Index,
            Next Session Threshold, Next Minutes Threshold)

        """
        current_belt = BELTS[0]
        rank_index = 0
        total_mins = self.stats.total_minutes

        for i, belt in enumerate(BELTS):
            # Must meet BOTH session count and total time
            if self.stats.sessions >= belt[1] and total_mins >= belt[2]:
                current_belt = belt
                rank_index = i
            else:
                break

        # Determine next threshold
        if rank_index + 1 < len(BELTS):
            next_session_threshold = BELTS[rank_index + 1][1]
            next_minutes_threshold = float(BELTS[rank_index + 1][2])
        else:
            next_session_threshold = self.stats.sessions  # Maxed out
            next_minutes_threshold = total_mins

        return (
            current_belt[0],
            current_belt[3],
            rank_index,
            next_session_threshold,
            next_minutes_threshold,
        )

    def display_status(self) -> None:
        """Print the current status to the console using Rich."""
        (
            belt_name,
            color,
            rank_index,
            next_session_threshold,
            next_minutes_threshold,
        ) = self.get_current_belt()

        status_msg = (
            f"[bold {color}]{belt_name}[/bold {color}]\n"
            f"Sessions: {self.stats.sessions}\n"
            f"Total Time: {self.stats.total_minutes:.1f} minutes"
        )
        rich_print(
            Panel(
                status_msg,
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
                # Add task for sessions
                _ = progress.add_task(
                    "Sessions",
                    total=int(next_session_threshold),
                    completed=int(self.stats.sessions),
                )
                # Add task for minutes
                _ = progress.add_task(
                    "Minutes ",
                    total=int(next_minutes_threshold),
                    completed=int(self.stats.total_minutes),
                )
        else:
            rich_print(
                "[bold gold1]You have mastered the way of the Debug Dojo![/bold gold1]"
            )
