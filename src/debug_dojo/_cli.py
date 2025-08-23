"""Command-line interface for running Python scripts or modules with debugging tools."""

from __future__ import annotations

import runpy
import sys
import traceback
from bdb import BdbQuit
from enum import Enum
from pathlib import Path
from shutil import which
from typing import Annotated

import typer
from rich import print as rich_print

from ._config import load_config
from ._config_models import DebugDojoConfig, DebuggerType  # noqa: TC001
from ._installers import install_by_config


class ExecMode(Enum):
    """Execution mode for the target."""

    FILE = "file"
    MODULE = "module"
    EXECUTABLE = "executable"


cli = typer.Typer(
    name="debug_dojo",
    help="Run a Python script or module with debugging tools installed.",
    no_args_is_help=True,
)


def __execute_with_debug(  # noqa: C901
    target_name: str,
    target_args: list[str],
    *,
    target_mode: ExecMode,
    verbose: bool,
    config: DebugDojoConfig,
) -> None:
    """Execute a target script or module with installed debugging tools."""
    sys.argv = [target_name, *target_args]

    if verbose:
        rich_print(f"[blue]Installing debugging tools for {target_name}.[/blue]")
        rich_print(f"[blue]Arguments for target: {target_args}[/blue]")

    install_by_config(config)

    if target_mode is ExecMode.MODULE:
        runner = runpy.run_module
    else:
        if target_mode is ExecMode.EXECUTABLE:
            target_name = which(target_name) or target_name

        if not Path(target_name).exists():
            raise typer.Exit(1)

        runner = runpy.run_path

    try:
        _ = runner(target_name, run_name="__main__")
    except ImportError as e:
        rich_print(f"[red]Error importing {target_name}:[/red]\n{e}")
        raise typer.Exit(1) from e
    except BdbQuit:
        rich_print("[red]Debugging session terminated by user.[/red]")
        raise typer.Exit(0) from None
    except KeyboardInterrupt:
        rich_print("[red]Execution interrupted by user.[/red]")
        raise typer.Exit(0) from None
    except SystemExit as e:
        if e.code:
            rich_print(f"[red]Script exited with code {e.code}.[/red]")
    except Exception as e:
        rich_print(f"[red]Error while running {target_name}:[/red]\n{e}")
        rich_print(traceback.format_exc())
        if config.exceptions.post_mortem:
            import ipdb  # noqa: PLC0415, T100 pyright: ignore[reportMissingTypeStubs]

            rich_print("[blue]Entering post-mortem debugging session...[/blue]")
            ipdb.post_mortem(e.__traceback__)
        raise typer.Exit(1) from e


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
        typer.Option("--verbose", "-v", help="Enable verbose output"),
    ] = False,
    module: Annotated[
        bool,
        typer.Option("--module", "-m", help="Run a module"),
    ] = False,
    executable: Annotated[
        bool,
        typer.Option("--exec", "-e", help="Run a command"),
    ] = False,
) -> None:
    """Run the command-line interface."""
    if module and executable:
        rich_print(
            "[red]Error: --module and --command options are mutually exclusive.[/red]"
        )
        raise typer.Exit(1)

    mode = (
        ExecMode.EXECUTABLE
        if executable
        else ExecMode.MODULE
        if module
        else ExecMode.FILE
    )

    config = load_config(config_path, verbose=verbose, debugger=debugger)

    if verbose:
        display_config(config)

    if target_name:
        __execute_with_debug(
            target_name=target_name,
            target_mode=mode,
            target_args=ctx.args,
            verbose=verbose,
            config=config,
        )


def main() -> None:
    """Run the command-line interface."""
    cli()
