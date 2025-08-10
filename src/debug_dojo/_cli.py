"""Command-line interface for running Python scripts or modules with debugging tools."""

from __future__ import annotations

import runpy
import sys
from bdb import BdbQuit
from pathlib import Path
from typing import Annotated

import typer
from rich import print as rich_print

from ._config import DebugDojoConfig, DebuggerType, load_config
from ._installers import install_by_config

cli = typer.Typer(
    name="debug_dojo",
    help="Run a Python script or module with debugging tools installed.",
    no_args_is_help=True,
)


def execute_with_debug(  # noqa: C901
    target_name: str,
    target_args: list[str],
    *,
    target_is_module: bool,
    verbose: bool,
    config: DebugDojoConfig,
) -> None:
    """Execute a target script or module with installation of debugging tools."""
    sys.argv = [target_name, *target_args]

    if verbose:
        rich_print(f"[blue]Installing debugging tools for {target_name}.[/blue]")
        rich_print(f"[blue]Arguments for target: {target_args}[/blue]")

    install_by_config(config)

    if target_is_module:
        runner = runpy.run_module
    else:
        if not Path(target_name).exists():
            sys.exit(1)
        runner = runpy.run_path

    try:
        _ = runner(target_name, run_name="__main__")
    except ImportError as e:
        rich_print(f"[red]Error importing {target_name}:[/red]\n{e}")
        sys.exit(1)
    except BdbQuit:
        rich_print("[red]Debugging session terminated by user.[/red]")
        sys.exit(0)
    except KeyboardInterrupt:
        rich_print("[red]Execution interrupted by user.[/red]")
        sys.exit(0)
    except SystemExit as e:
        if e.code:
            rich_print(f"[red]Script exited with code {e.code}.[/red]")
    except Exception as e:  # noqa: BLE001
        rich_print(f"[red]Error while running {target_name}:[/red]\n{e}")
        if config.exceptions.post_mortem:
            import pdb  # noqa: PLC0415, T100

            rich_print("[blue]Entering post-mortem debugging session...[/blue]")
            pdb.post_mortem(e.__traceback__)
        sys.exit(1)


def display_config(config: DebugDojoConfig) -> None:
    """Display the configuration for the debug dojo."""
    rich_print("[blue]Using debug-dojo configuration:[/blue]")
    rich_print(config.model_dump_json(indent=4))


@cli.command(
    help="Run a Python script or module with debugging tools installed.",
    no_args_is_help=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def run_debug(  # noqa: PLR0913
    ctx: typer.Context,
    target_name: Annotated[
        str | None, typer.Argument(help="The target script or module to debug.")
    ] = None,
    *,
    config_path: Annotated[
        Path | None, typer.Option("--config", "-c", help="Show configuration")
    ] = None,
    debugger: Annotated[
        DebuggerType | None,
        typer.Option("--debugger", "-d", help="Specify the debugger to use"),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", is_flag=True, help="Enable verbose output"),
    ] = False,
    module: Annotated[
        bool,
        typer.Option("--module", "-m", is_flag=True, help="Run as a module"),
    ] = False,
) -> None:
    """Run the command-line interface."""
    config = load_config(config_path, verbose=verbose, debugger=debugger)

    if verbose:
        display_config(config)

    if target_name:
        execute_with_debug(
            target_name=target_name,
            target_is_module=module,
            target_args=ctx.args,
            verbose=verbose,
            config=config,
        )


def main() -> None:
    """Run the command-line interface."""
    cli()
