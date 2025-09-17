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
    """Execute a target script or module with installed debugging tools.

    Args:
        target_name (str): The name of the script, module, or executable to run.
        target_args (list[str]): Arguments to pass to the target.
        target_mode (ExecMode): The execution mode (FILE, MODULE, or EXECUTABLE).
        verbose (bool): If True, print verbose output.
        config (DebugDojoConfig): The debug-dojo configuration.

    Raises:
        typer.Exit: If the target file is not found, or if an import error occurs,
                    or if the script exits with a non-zero code.

    """
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
            import ipdb  # pyright: ignore[reportMissingTypeStubs]  # noqa: PLC0415, T100

            rich_print("[blue]Entering post-mortem debugging session...[/blue]")
            ipdb.post_mortem(e.__traceback__)  # pyright: ignore[reportUnknownMemberType]
        raise typer.Exit(1) from e


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
    """Run a Python script, module, or executable with debug-dojo tools.

    This command acts as the main entry point for `debug-dojo`, allowing users to
    execute their code while automatically installing and configuring debugging tools
    based on the provided options or configuration file.

    Args:
        ctx (typer.Context): The Typer context object.
        target_name (str | None): The path to the script, name of the module, or
                                  name of the executable to run. If not provided,
                                  the command will exit.
        config_path (Path | None): Path to a custom configuration file
                                   (e.g., `dojo.toml`).
        debugger (DebuggerType | None): Override the default debugger specified
                                        in the config.
        verbose (bool): Enable verbose output, showing loaded configuration
                        and installation steps.
        module (bool): Treat `target_name` as a Python module to run
                       (e.g., `dojo -m my_package.my_module`).
        executable (bool): Treat `target_name` as an executable command to run
                           (e.g., `dojo -e pytest`).

    Raises:
        typer.Exit: If `--module` and `--exec` are used together, or if the target
                    cannot be executed, or if an error occurs during execution.

    """
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
        rich_print(f"[blue]Using debug-dojo configuration: {config} [/blue]")

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
