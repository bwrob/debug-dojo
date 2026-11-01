# ruff: ignore[implicit-namespace-package]
# Canonical standalone example script; the examples directory is not a package.
"""Canonical Typer CLI application recipe for this project."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

# In real packages, import `__version__` and `core_business_logic` from the
# parent package instead of defining them locally.
__version__ = "0.1.0"


def core_business_logic(target: str) -> str:
    """Process the requested target and return a formatted result.

    Args:
        target: User-selected target item.

    Returns:
        Confirmation string for the processed target.

    """
    return f"Processed {target}"


app = typer.Typer(
    name="my-app",
    help="High-performance CLI application.",
    no_args_is_help=True,
    rich_markup_mode="rich",
)
console = Console()


def version_callback(*, value: bool) -> None:
    """Print the version and exit.

    Args:
        value: Whether the `--version` option was passed.

    Raises:
        typer.Exit: Always exits once the version is printed.

    """
    if value:
        console.print(
            f"[bold cyan]my-app[/bold cyan] version [green]{__version__}[/green]"
        )
        raise typer.Exit


@app.callback()
def main_callback(
    *,
    _version: Annotated[
        bool,
        typer.Option(
            "--version",
            "-v",
            help="Show version and exit.",
            callback=version_callback,
            is_eager=True,
        ),
    ] = False,
) -> None:
    """Entry point callback for global options."""


@app.command()
def run(
    target: Annotated[str, typer.Argument(help="Target item to process.")] = "default",
) -> None:
    """Execute primary command workflow.

    Args:
        target: Target item passed by the user.

    """
    result = core_business_logic(target)
    console.print(f"[bold green]✨ {result}[/bold green]")


def main() -> None:
    """Execute the CLI application."""
    app()


if __name__ == "__main__":
    main()
