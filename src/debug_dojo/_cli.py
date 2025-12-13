"""Command-line interface for running Python scripts or modules with debugging tools."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated  # Removed TYPE_CHECKING here

import typer
from rich import print as rich_print

from debug_dojo._config import load_config
from debug_dojo._config_models import DebuggerType  # noqa: TC001
from debug_dojo._execution import ExecMode, execute_with_debug

cli = typer.Typer(
    name="debug_dojo",
    help="Run a Python script or module with debugging tools installed.",
    no_args_is_help=True,
)


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
        execute_with_debug(
            target_name=target_name,
            target_mode=mode,
            target_args=ctx.args,
            verbose=verbose,
            config=config,
        )


def main() -> None:
    """Run the command-line interface."""
    cli()
