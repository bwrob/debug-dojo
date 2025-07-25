"""Command-line interface for running Python scripts or modules with debugging tools."""

import os
import runpy
import sys
from bdb import BdbQuit
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rich_print

from .installers import install_all

cli = typer.Typer(
    name="debug_dojo",
    help="Run a Python script or module with debugging tools installed.",
    no_args_is_help=True,
)


def execute_with_debug(
    target_name: str,
    target_args: list[str],
    *,
    verbose: bool,
) -> None:
    """Execute a target script or module with installation of debugging tools."""
    sys.argv = [target_name, *target_args]

    if verbose:
        rich_print(f"[blue]Installing debugging tools for {target_name}...[/blue]")
        rich_print(f"[blue]Arguments: {target_args}[/blue]")

    install_all()

    if (
        Path(target_name).exists()
        or target_name.endswith(".py")
        or os.sep in target_name
    ):
        if not Path(target_name).exists():
            sys.exit(1)
        runner = runpy.run_path
    else:
        runner = runpy.run_module

    _ = runner(target_name, run_name="__main__")


def display_config(config) -> None:
    """Display the configuration for the debug dojo."""
    rich_print("[green]Debug Dojo Configuration:[/green]")
    rich_print("This tool installs debugging tools and runs Python scripts or modules.")
    rich_print(
        "You can specify a target script or module to debug, along with any arguments."
    )
    rich_print("Example usage: `debug_dojo target_to_debug.py --some-input-to-target`")


def load_config() -> None:
    """Load the configuration for the debug dojo."""
    # Placeholder for future configuration loading logic


@cli.command(
    help="Run a Python script or module with debugging tools installed.",
    no_args_is_help=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def run_debug(
    ctx: typer.Context,
    target_name: Annotated[
        str | None, typer.Argument(help="The target script or module to debug.")
    ] = None,
    config: Annotated[
        Path | None, typer.Option("--config", "-c", help="Show configuration")
    ] = None,
    *,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", is_flag=True, help="Enable verbose output"),
    ] = False,
) -> None:
    """Run the command-line interface."""
    if config:
        config = load_config()

    if verbose:
        typer.echo("Verbose mode enabled.")
        display_config(config)

    if target_name:
        try:
            execute_with_debug(target_name, ctx.args, verbose=verbose)
        except BdbQuit:
            rich_print("[red]Debugging session terminated by user.[/red]")
            sys.exit(0)


def main() -> None:
    """Run the command-line interface."""
    cli()
