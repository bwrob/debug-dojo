"""Command-line interface for running targets with the `dpdb` debugger."""

from __future__ import annotations

from typing import Annotated

import typer

from debug_dojo._execution import execute_with_debug

cli: typer.Typer = typer.Typer(
    name="debug-dojo",
    help="Run a Python script, module, or command with the dpdb debugger.",
    no_args_is_help=True,
    add_completion=False,
)


@cli.command(
    help="Run a Python script, module, or command with the dpdb debugger.",
    no_args_is_help=True,
    context_settings={"allow_extra_args": True, "ignore_unknown_options": True},
)
def run(
    ctx: typer.Context,
    target_name: Annotated[
        str | None,
        typer.Argument(
            help="The target script, module, or command to debug.", metavar="target"
        ),
    ] = None,
    *,
    breaks: Annotated[
        list[str] | None,
        typer.Option(
            "--break",
            "-b",
            help="Set a breakpoint (line, file:line, or function)",
        ),
    ] = None,
) -> None:
    """Run a Python script, module, or executable with debug-dojo (`dpdb`).

    Args:
        ctx (typer.Context): The Typer context object.
        target_name (str | None): Path to a script, module name, or executable
            command to debug.
        breaks (list[str] | None): Optional breakpoint locations (`line`,
            `file:line`, or function name) to arm before running the target.

    """
    if target_name is not None:
        execute_with_debug(
            target_name=target_name,
            target_args=ctx.args,
            breaks=breaks,
        )


def main() -> None:
    """Entry point for the `debug-dojo` and `dojo` CLI commands."""
    cli()
