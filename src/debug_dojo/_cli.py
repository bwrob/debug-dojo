"""Command-line interface for running Python scripts or modules with debugging tools."""

from __future__ import annotations

import os
import runpy
import sys
from bdb import BdbQuit
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError
from rich import print as rich_print

from ._config import DebugDojoConfig, load_config
from ._installers import install_by_config

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
        rich_print(f"[blue]Installing debugging tools for {target_name}.[/blue]")
        rich_print(f"[blue]Arguments for target: {target_args}[/blue]")

    config = load_config()
    install_by_config(config)

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


def display_config(config: DebugDojoConfig) -> None:
    """Display the configuration for the debug dojo."""
    rich_print("[blue]Using debug-dojo configuration:[/blue]")
    rich_print(config.model_dump_json(indent=4))


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
    config_path: Annotated[
        Path | None, typer.Option("--config", "-c", help="Show configuration")
    ] = None,
    *,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", is_flag=True, help="Enable verbose output"),
    ] = False,
) -> None:
    """Run the command-line interface."""
    try:
        config = load_config(config_path, verbose=verbose)
    except ValidationError as e:
        rich_print(f"[red]Configuration error:\n{e}[/red]")
        sys.exit(1)

    if verbose:
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
