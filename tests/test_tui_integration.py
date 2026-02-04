"""Integration tests for TUI history and launch logic."""

import json
from io import StringIO
from pathlib import Path

import pytest
from rich.console import Console
from textual.widgets import OptionList, Static

from debug_dojo._tui import ConfigWidget, DojoApp, HistoryWidget


@pytest.fixture
def history_file(tmp_path: Path) -> Path:
    """Create a temporary history file."""
    stats_file = tmp_path / "stats.json"
    data = {
        "sessions": 1,
        "history": [
            {
                "timestamp": "2023-01-01T10:00:00",
                "duration_minutes": 5.0,
                "command": "dojo run target.py --backend debugpy",
            },
            {
                "timestamp": "2023-01-02T10:00:00",
                "duration_minutes": 10.0,
                "command": "dojo run other.py",
            },
        ],
    }
    _ = stats_file.write_text(json.dumps(data), encoding="utf-8")
    return stats_file


@pytest.mark.asyncio
async def test_app_loads_history(history_file: Path) -> None:
    """Test that the app loads history on mount."""
    # We need to inject the stats file path into the app
    app = DojoApp(stats_path=history_file)

    async with app.run_test() as pilot:
        # Wait for mount
        await pilot.pause()

        history_widget = app.screen.query_one(HistoryWidget)
        option_list = history_widget.query_one(OptionList)

        # Should have 2 items
        expected_items = 2
        assert option_list.option_count == expected_items

        # Check item content (OptionList stores it as Renderable, usually Text)
        # We can check the text of the options
        option_0 = option_list.get_option_at_index(0)
        assert "target.py" in str(option_0.prompt)

        option_1 = option_list.get_option_at_index(1)
        assert "other.py" in str(option_1.prompt)


@pytest.mark.asyncio
async def test_history_selection_updates_config(history_file: Path) -> None:
    """Test that selecting a history item updates the config widget."""
    app = DojoApp(stats_path=history_file)

    async with app.run_test() as pilot:
        await pilot.pause()

        history_widget = app.screen.query_one(HistoryWidget)
        config_widget = app.screen.query_one(ConfigWidget)
        option_list = history_widget.query_one(OptionList)

        # Select first item (index 0)
        option_list.highlighted = 0
        await pilot.pause()  # Wait for event processing

        # Query inner Static
        details = config_widget.query_one("#config_details", Static)

        # Access private attribute (name mangled)
        renderable = getattr(details, "_Static__content", None)

        string_io = StringIO()
        console = Console(file=string_io, force_terminal=False)
        console.print(renderable)
        content = string_io.getvalue()

        assert "target.py" in content
        assert "debugpy" in content


@pytest.mark.asyncio
async def test_launch_action(history_file: Path) -> None:
    """Test that clicking launch returns the command."""
    app = DojoApp(stats_path=history_file)

    async with app.run_test() as pilot:
        await pilot.pause()

        # Select first item
        history_widget = app.screen.query_one(HistoryWidget)
        history_widget.query_one(OptionList).highlighted = 0
        await pilot.pause()

        # Click it
        _ = await pilot.click("#launch_btn")
        await pilot.pause()

        # App should exit
        assert app.return_value == "dojo run target.py --backend debugpy"
