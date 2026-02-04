from typing import ClassVar

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Placeholder
from typing_extensions import override


class MainScreen(Screen[None]):
    """The main dashboard screen of the Debug Dojo."""

    @override
    def compose(self) -> ComposeResult:
        yield Header()
        yield Placeholder("History (Left)", id="history_pane")
        yield Placeholder("Config (Right)", id="config_pane")
        yield Footer()


class DojoApp(App[None]):
    """The Debug Dojo TUI Application."""

    TITLE: str | None = "Debug Dojo"
    CSS: ClassVar[str] = """
    MainScreen {
        layout: horizontal;
    }
    #history_pane {
        width: 1fr;
        height: 100%;
    }
    #config_pane {
        width: 1fr;
        height: 100%;
    }
    """

    async def on_mount(self) -> None:
        await self.push_screen(MainScreen())
