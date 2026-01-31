"""Tests for the gamification module."""

import json
from pathlib import Path
from typing import cast

import pytest

from debug_dojo._gamification import BELTS, GamificationManager, SessionInfo


@pytest.fixture
def temp_stats_file(tmp_path: Path) -> Path:
    """Fixture providing a temporary stats file path."""
    return tmp_path / "stats.json"


def test_initial_stats(temp_stats_file: Path) -> None:
    """Test that a fresh manager starts with 0 sessions."""
    manager = GamificationManager(stats_path=temp_stats_file)
    assert manager.stats.sessions == 0
    assert manager.stats.bugs_crushed == 0
    assert manager.stats.total_minutes == 0

    belt_name, _color, rank, next_sessions, next_mins = manager.get_current_belt()
    assert belt_name == "White Belt"
    assert rank == 0
    assert next_sessions == BELTS[1][1]
    assert next_mins == float(BELTS[1][2])


def test_increment_session(temp_stats_file: Path) -> None:
    """Test that incrementing session updates stats and saves to file."""
    manager = GamificationManager(stats_path=temp_stats_file)

    duration_seconds = 120.0

    expected_minutes = 2.0

    expected_command = "dojo run script.py"

    manager.increment_session(
        duration_seconds=duration_seconds, command=expected_command
    )

    assert manager.stats.sessions == 1

    assert len(manager.stats.history) == 1

    assert manager.stats.history[0].duration_minutes == expected_minutes

    assert manager.stats.history[0].command == expected_command

    assert manager.stats.total_minutes == expected_minutes

    # Verify file persistence

    assert temp_stats_file.exists()

    data = cast("dict[str, object]", json.loads(temp_stats_file.read_text()))

    assert data["sessions"] == 1

    history = cast("list[dict[str, object]]", data["history"])

    assert len(history) == 1

    assert history[0]["duration_minutes"] == expected_minutes

    assert history[0]["command"] == expected_command


def test_load_existing_stats(temp_stats_file: Path) -> None:
    """Test loading existing stats from file."""
    # Create a fake stats file

    expected_sessions = 15

    expected_bugs = 2

    expected_mins = 60.0

    data = {
        "sessions": expected_sessions,
        "bugs_crushed": expected_bugs,
        "history": [
            {
                "timestamp": "2024-01-01T12:00:00",
                "duration_minutes": expected_mins,
                "command": "dojo run test.py",
            }
        ],
    }

    _ = temp_stats_file.write_text(json.dumps(data))

    manager = GamificationManager(stats_path=temp_stats_file)

    assert manager.stats.sessions == expected_sessions

    assert manager.stats.bugs_crushed == expected_bugs

    assert len(manager.stats.history) == 1

    assert manager.stats.history[0].command == "dojo run test.py"

    assert manager.stats.total_minutes == expected_mins


def test_load_legacy_stats(temp_stats_file: Path) -> None:
    """Test migration from duration_seconds."""
    expected_mins = 2.0

    data = {
        "sessions": 1,
        "history": [
            {
                "timestamp": "2024-01-01T12:00:00",
                "duration_seconds": 120.0,
                "command": "dojo run test.py",
            }
        ],
    }

    _ = temp_stats_file.write_text(json.dumps(data))

    manager = GamificationManager(stats_path=temp_stats_file)

    assert manager.stats.total_minutes == expected_mins


def test_belt_progression(temp_stats_file: Path) -> None:
    """Test that belt ranking works correctly."""
    manager = GamificationManager(stats_path=temp_stats_file)

    # White Belt
    manager.stats.sessions = 0
    assert manager.get_current_belt()[0] == "White Belt"

    # Need 5 sessions AND 10 minutes for Yellow Belt
    manager.stats.history = [SessionInfo("t", 5.0, "c")]
    manager.stats.sessions = 5
    assert manager.get_current_belt()[0] == "White Belt"  # Only 5 mins

    manager.stats.history = [SessionInfo("t", 10.0, "c")]
    assert manager.get_current_belt()[0] == "Yellow Belt"  # 5 sessions + 10 mins

    # Blue Belt (Threshold 60 sessions, 120 mins)
    manager.stats.sessions = 65
    manager.stats.history = [SessionInfo("t", 150.0, "c")]
    assert manager.get_current_belt()[0] == "Blue Belt"


def test_corrupt_stats_file(temp_stats_file: Path) -> None:
    """Test that corrupt stats file is handled gracefully."""
    _ = temp_stats_file.write_text("invalid json")

    manager = GamificationManager(stats_path=temp_stats_file)
    assert manager.stats.sessions == 0
