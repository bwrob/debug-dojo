"""Command-line interface for running Python scripts or modules with debugging tools."""

from __future__ import annotations

from typing import Annotated

import typer
from rich import print as rich_print

from debug_dojo._config_models import (
    DebuggerType,
    DojoSettings,
)
from debug_dojo._execution import ExecMode, execute_with_debug

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
        DebuggerType,
        typer.Option("--debugger", "-d", help="Specify the debugger to use"),
    ] = DebuggerType.PDB,
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
    post_mortem: Annotated[
        bool,
        typer.Option(
            "--post-mortem/--no-post-mortem",
            help="Enable post-mortem debugging on error",
        ),
    ] = True,
    rich_traceback: Annotated[
        bool,
        typer.Option(
            "--rich-traceback/--no-rich-traceback",
            help="Enable Rich traceback formatting",
        ),
    ] = True,
    show_locals: Annotated[
        bool,
        typer.Option(
            "--show-locals/--no-show-locals",
            help="Show local variables in traceback",
        ),
    ] = False,
    debugpy_host: Annotated[
        str,
        typer.Option("--debugpy-host", help="Host address for debugpy server"),
    ] = "localhost",
    debugpy_port: Annotated[
        int,
        typer.Option("--debugpy-port", help="Port number for debugpy server"),
    ] = 1992,
    debugpy_wait: Annotated[
        bool,
        typer.Option(
            "--debugpy-wait/--no-debugpy-wait",
            help="Wait for client connection before debugging",
        ),
    ] = True,
    prompt_name: Annotated[
        str,
        typer.Option("--prompt-name", help="REPL prompt name"),
    ] = "debug-dojo> ",
) -> None:
    """Run a Python script, module, or executable with debug-dojo tools.

    This command acts as the main entry point for `debug-dojo`, allowing users to
    execute their code while automatically installing and configuring debugging tools
    based on the provided CLI options.

    Args:
        ctx (typer.Context): The Typer context object.
        target_name (str | None): The path to the script, name of the module, or
            name of the executable to run. If not provided, the command will exit.
        debugger (DebuggerType): Specify the debugger to use (default: pdb).
        verbose (bool): Enable verbose output, showing active settings.
        module (bool): Treat `target_name` as a Python module to run
            (for example, `dojo run -m my_package.my_module`).
        executable (bool): Treat `target_name` as an executable command to run
            (for example, `dojo run -e pytest`).
        post_mortem (bool): Enable post-mortem debugging after an unhandled exception.
        rich_traceback (bool): Enable Rich traceback for enhanced error formatting.
        show_locals (bool): Include local variables in traceback.
        debugpy_host (str): Host for debugpy debugger.
        debugpy_port (int): Port for debugpy debugger.
        debugpy_wait (bool): Whether debugpy waits for client connection.
        prompt_name (str): Prompt string for debugger REPL.

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

    settings = DojoSettings(
        debugger=debugger,
        post_mortem=post_mortem,
        rich_traceback=rich_traceback,
        show_locals=show_locals,
        debugpy_host=debugpy_host,
        debugpy_port=debugpy_port,
        debugpy_wait_for_client=debugpy_wait,
        prompt_name=prompt_name,
    )

    if verbose:
        rich_print(f"[blue]Using debug-dojo configuration: {settings} [/blue]")

    if target_name is not None:
        execute_with_debug(
            target_name=target_name,
            target_mode=mode,
            target_args=ctx.args,
            verbose=verbose,
            config=settings,
        )


def main() -> None:
    """Run the command-line interface."""
    cli()
