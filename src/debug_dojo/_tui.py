from collections.abc import Mapping
from typing import ClassVar

from rich.pretty import Pretty
from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Footer, Header, OptionList, Static
from typing_extensions import override


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


class ConfigWidget(Static):
    """Configuration for the selected run."""

    def show_config(self, config: Mapping[str, object]) -> None:
        """Display the configuration."""
        self.update(Pretty(config))


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


class DojoApp(App[None]):
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

    async def on_mount(self) -> None:
        await self.push_screen(MainScreen(id="main"))
