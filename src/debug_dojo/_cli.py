"""Command-line interface for running Python scripts or modules with debugging tools."""

from __future__ import annotations

from typing import Annotated

import typer
from rich import print as rich_print

from debug_dojo._execution import ExecMode, execute_with_debug
from debug_dojo._installers import (
    DebuggerType,  # ruff: ignore[typing-only-first-party-import] -- required at runtime by Typer for CLI argument validation
)

cli: typer.Typer = typer.Typer(
    name="debug_dojo",
    help="Run a Python script or module with debugging tools installed.",
    no_args_is_help=True,
)


@cli.callback()
def callback() -> None:
    """Run a Python script or module with debugging tools installed."""


@cli.command(
    help="Run a Python script or module with debugging tools installed.",
    no_args_is_help=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def run(  # ruff: ignore[too-many-arguments] -- CLI commands map CLI options directly to parameters
    ctx: typer.Context,
    target_name: Annotated[
        str | None,
        typer.Argument(help="The target script or module to debug.", metavar="target"),
    ] = None,
    *,
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
    execute their code while automatically installing opinionated debugging tools.

    Args:
        ctx (typer.Context): The Typer context object.
        target_name (str | None): The path to the script, name of the module, or
            name of the executable to run. If not provided, the command will exit.
        debugger (DebuggerType | None): Optional debugger backend override.
        verbose (bool): Enable verbose output.
        module (bool): Treat `target_name` as a Python module to run
            (for example, `dojo run -m my_package.my_module`).
        executable (bool): Treat `target_name` as an executable command to run
            (for example, `dojo run -e pytest`).

    Raises:
        typer.Exit: If `--module` and `--exec` are used together, or if the target
            cannot be executed, or if an error occurs during execution.

    """
    if module and executable:
        rich_print(
            "[red]Error: --module and --command options are mutually exclusive.[/red]",
        )
        raise typer.Exit(1)

    mode = (
        ExecMode.EXECUTABLE
        if executable
        else ExecMode.MODULE
        if module
        else ExecMode.FILE
    )

    if verbose:
        rich_print(f"[blue]Using debugger: {debugger or 'default'}[/blue]")

    if target_name is not None:
        execute_with_debug(
            target_name=target_name,
            target_mode=mode,
            target_args=ctx.args,
            verbose=verbose,
            debugger=debugger,
        )


def main() -> None:
    """Run the command-line interface."""
    cli()
