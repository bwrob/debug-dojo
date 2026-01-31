"""Tests for the gamification module."""

import json
from pathlib import Path
from typing import cast

import pytest

from debug_dojo._gamification import BELTS, GamificationManager


@pytest.fixture
def temp_stats_file(tmp_path: Path) -> Path:
    """Fixture providing a temporary stats file path."""
    return tmp_path / "stats.json"


def test_initial_stats(temp_stats_file: Path) -> None:
    """Test that a fresh manager starts with 0 sessions."""
    manager = GamificationManager(stats_path=temp_stats_file)
    assert manager.stats.sessions == 0
    assert manager.stats.bugs_crushed == 0

    belt_name, _color, rank, next_threshold = manager.get_current_belt()
    assert belt_name == "White Belt"
    assert rank == 0
    assert next_threshold == BELTS[1][1]


def test_increment_session(temp_stats_file: Path) -> None:
    """Test that incrementing session updates stats and saves to file."""
    manager = GamificationManager(stats_path=temp_stats_file)
    manager.increment_session()

    assert manager.stats.sessions == 1

    # Verify file persistence
    assert temp_stats_file.exists()
    data = cast("dict[str, object]", json.loads(temp_stats_file.read_text()))
    assert data["sessions"] == 1


def test_load_existing_stats(temp_stats_file: Path) -> None:
    """Test loading existing stats from file."""
    # Create a fake stats file
    expected_sessions = 15
    expected_bugs = 2
    data = {"sessions": expected_sessions, "bugs_crushed": expected_bugs}
    _ = temp_stats_file.write_text(json.dumps(data))

    manager = GamificationManager(stats_path=temp_stats_file)
    assert manager.stats.sessions == expected_sessions
    assert manager.stats.bugs_crushed == expected_bugs


def test_belt_progression(temp_stats_file: Path) -> None:
    """Test that belt ranking works correctly."""
    manager = GamificationManager(stats_path=temp_stats_file)

    # White Belt
    manager.stats.sessions = 0
    assert manager.get_current_belt()[0] == "White Belt"

    # Yellow Belt (Threshold 5)
    manager.stats.sessions = 5
    assert manager.get_current_belt()[0] == "Yellow Belt"

    # Blue Belt (Threshold 60)
    manager.stats.sessions = 65
    assert manager.get_current_belt()[0] == "Blue Belt"


def test_corrupt_stats_file(temp_stats_file: Path) -> None:
    """Test that corrupt stats file is handled gracefully."""
    _ = temp_stats_file.write_text("invalid json")

    manager = GamificationManager(stats_path=temp_stats_file)
    assert manager.stats.sessions == 0
