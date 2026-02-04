from collections.abc import Mapping
from pathlib import Path
from typing import ClassVar

from rich.pretty import Pretty
from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Footer, Header, OptionList, Static
from typing_extensions import override

from debug_dojo._gamification import GamificationManager


class BeltWidget(Static):
    """Displays current belt and stats."""

    @override
    def compose(self) -> ComposeResult:
        yield Static("Belt: White | Bugs: 0", id="belt_stats")

    def update_stats(self, belt: str, bugs_crushed: int) -> None:
        """Update the belt stats display."""
        stats_static = self.query_one("#belt_stats", Static)
        stats_static.update(f"Belt: {belt} | Bugs: {bugs_crushed}")


class HistoryWidget(Static):
    """History of previous runs."""

    @override
    def compose(self) -> ComposeResult:
        yield OptionList(id="history_list")

    def update_history(self, items: list[str]) -> None:
        """Update the history list with new items."""
        option_list = self.query_one(OptionList)
        _ = option_list.clear_options()
        for item in items:
            _ = option_list.add_option(item)

        # Auto-select the last item
        if items:
            option_list.highlighted = len(items) - 1


class ConfigWidget(Vertical):
    """Configuration for the selected run."""

    @override
    def compose(self) -> ComposeResult:
        yield Static(id="config_details")
        yield Button("Practice Again", id="launch_btn", variant="primary")

    def show_config(self, config: Mapping[str, object]) -> None:
        """Display the configuration."""
        self.query_one("#config_details", Static).update(Pretty(config))


class MainScreen(Screen[None]):
    """The main dashboard screen of the Debug Dojo."""

    @override
    def compose(self) -> ComposeResult:
        yield Header()
        yield BeltWidget()
        with Horizontal():
            yield HistoryWidget(id="history_pane")
            yield ConfigWidget(id="config_pane")
        yield Footer()


class DojoApp(App[str]):
    """The Debug Dojo TUI Application."""

    TITLE: str | None = "Debug Dojo"
    CSS: ClassVar[str] = """
    BeltWidget {
        height: 3;
        width: 100%;
        border: solid yellow;
    }
    #history_pane {
        width: 1fr;
        height: 100%;
        border: solid green;
    }
    #config_pane {
        width: 1fr;
        height: 100%;
        border: solid blue;
    }
    """

    manager: GamificationManager

    def __init__(self, stats_path: Path | None = None, **kwargs: object) -> None:
        super().__init__(**kwargs)  # pyright: ignore[reportArgumentType]
        self.manager = GamificationManager(stats_path)

    async def on_mount(self) -> None:
        main_screen = MainScreen(id="main")
        await self.push_screen(main_screen)

        # Load history
        history_widget = main_screen.query_one(HistoryWidget)
        items = [s.command for s in self.manager.stats.history]
        history_widget.update_history(items)

        # Initialize belt stats
        belt_info = self.manager.get_current_belt()
        belt_widget = main_screen.query_one(BeltWidget)
        belt_widget.update_stats(belt_info[0], self.manager.stats.bugs_crushed)

    def on_option_list_option_highlighted(
        self, event: OptionList.OptionHighlighted
    ) -> None:
        """Handle history selection."""
        if event.option_index is None:  # pyright: ignore[reportUnnecessaryComparison]
            return  # pyright: ignore[reportUnreachable]

        index = event.option_index
        if 0 <= index < len(self.manager.stats.history):
            session = self.manager.stats.history[index]
            config = {
                "command": session.command,
                "timestamp": session.timestamp,
                "duration_minutes": session.duration_minutes,
            }
            # Use the screen from the event source to ensure we query the correct screen
            event.option_list.screen.query_one(ConfigWidget).show_config(config)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle launch button."""
        if event.button.id == "launch_btn":
            history_widget = event.button.screen.query_one(HistoryWidget)
            idx = history_widget.query_one(OptionList).highlighted
            if idx is not None and 0 <= idx < len(self.manager.stats.history):
                command = self.manager.stats.history[idx].command
                self.exit(command)
