"""Command-line interface for running targets with the `dpdb` debugger."""

from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from importlib.metadata import PackageNotFoundError, version
from typing import TYPE_CHECKING, TextIO

from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from debug_dojo._execution import execute_with_debug

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence


@dataclass(frozen=True, slots=True)
class CliArgs:
    """Parsed command-line arguments for Dojo.

    Attributes:
        target: Target script, module, or executable to debug.
        target_args: Command-line arguments forwarded directly to the target.
        breaks: Initial breakpoint expressions armed before running the target.
        show_help: Flag indicating whether the help screen should be displayed.
        show_version: Flag indicating whether version info should be displayed.
        error: Validation error message if argument parsing failed.

    """

    target: str | None = None
    target_args: tuple[str, ...] = ()
    breaks: tuple[str, ...] = ()
    show_help: bool = False
    show_version: bool = False
    error: str | None = None


@dataclass(frozen=True, slots=True)
class CliResult:
    """Result of running a CLI invocation in a captured buffer.

    Attributes:
        exit_code: Exit status code.
        output: Captured combined standard and error output text.

    """

    exit_code: int
    output: str


class CliRunner:
    """Runner for invoking `dojo` CLI commands in test and automation environments."""

    env: dict[str, str]

    def __init__(self, env: Mapping[str, str] | None = None) -> None:
        """Initialize runner with optional environment variables.

        Args:
            env (Mapping[str, str] | None): Environment variables to inject during runs.

        """
        self.env = dict(env) if env is not None else {}

    def invoke(
        self,
        app: Callable[..., int],
        args: Sequence[str] | None = None,
    ) -> CliResult:
        """Invoke `app` with `args`, capturing combined standard and error output.

        Args:
            app (Callable[..., int]): The CLI entrypoint function.
            args (Sequence[str] | None): Arguments passed to `app`.

        Returns:
            CliResult: Exit code and captured output.

        """
        buf = io.StringIO()
        old_env = os.environ.copy()
        os.environ.update(self.env)
        try:
            with redirect_stdout(buf), redirect_stderr(buf):
                exit_code = app(args, stdout=buf, stderr=buf)
        except SystemExit as exc:
            code = exc.code
            exit_code = code if isinstance(code, int) else 0 if code is None else 1
        finally:
            os.environ.clear()
            os.environ.update(old_env)
        return CliResult(exit_code=exit_code, output=buf.getvalue())


def get_version() -> str:
    """Return the package version string.

    Returns:
        str: Installed package version of debug-dojo, or fallback `"0.9.0"`.

    """
    try:
        return version("debug-dojo")
    except PackageNotFoundError:
        return "0.9.0"


def render_help(console: Console) -> None:
    """Render the formatted CLI help screen using Rich panels.

    Args:
        console (Console): Target Rich console for output rendering.

    """
    console.print()
    console.print(
        " [bold]Usage:[/bold] [cyan]dojo[/cyan] [dim][OPTIONS][/dim] "
        "[cyan][target][/cyan] [dim][target_args...][/dim]"
    )
    console.print()
    console.print(" Run a Python script, module, or command with the dpdb debugger.")
    console.print()

    arg_table = Table(box=None, show_header=False, pad_edge=False, expand=True)
    arg_table.add_column("name", style="bold cyan", width=16, no_wrap=True)
    arg_table.add_column("desc", style="default")
    arg_table.add_row("target", "The target script, module, or command to debug.")
    arg_table.add_row(
        "target_args",
        "Arguments forwarded directly to the target program.",
    )
    console.print(
        Panel(arg_table, title="Arguments", title_align="left", box=box.ROUNDED)
    )

    opt_table = Table(box=None, show_header=False, pad_edge=False, expand=True)
    opt_table.add_column("opt", style="bold cyan", width=22, no_wrap=True)
    opt_table.add_column("desc", style="default")
    opt_table.add_row(
        "-b, --break <loc>",
        "Set a breakpoint (line, file:line, or function).",
    )
    opt_table.add_row("-v, --version", "Show version and exit.")
    opt_table.add_row("-h, --help", "Show this message and exit.")
    options_panel = Panel(
        opt_table,
        title="Options",
        title_align="left",
        box=box.ROUNDED,
    )
    console.print(options_panel)
    console.print()


def _extract_break_value(
    arg: str,
    args: Sequence[str],
    idx: int,
) -> tuple[str | None, int]:
    """Extract the breakpoint location string from `-b` or `--break` syntax.

    Args:
        arg (str): Current CLI argument string.
        args (Sequence[str]): Full arguments sequence.
        idx (int): Current argument index in `args`.

    Returns:
        tuple[str | None, int]: Pair of `(break_value, next_index)`.

    """
    if arg.startswith(("-b=", "--break=")):
        return (arg.split("=", 1)[1], idx)
    if idx + 1 < len(args):
        return (args[idx + 1], idx + 1)
    return (None, idx)


def _consume_break(
    arg: str,
    args: Sequence[str],
    idx: int,
    breaks: list[str],
) -> tuple[int, CliArgs | None]:
    """Parse and append a breakpoint argument.

    Args:
        arg (str): Break option flag.
        args (Sequence[str]): Argument list.
        idx (int): Current index.
        breaks (list[str]): Accumulated breakpoints.

    Returns:
        tuple[int, CliArgs | None]: Next argument index and optional error.

    """
    val, next_idx = _extract_break_value(arg, args, idx)
    if not val:
        return (next_idx, CliArgs(error=f"Option '{arg}' requires an argument."))
    breaks.append(val)
    return (next_idx + 1, None)


def _handle_delimiter(args: Sequence[str], breaks: list[str]) -> CliArgs:
    """Construct `CliArgs` for remaining tokens after the `--` delimiter.

    Args:
        args (Sequence[str]): Tokens following the `--` delimiter.
        breaks (list[str]): Collected breakpoints before the delimiter.

    Returns:
        CliArgs: Constructed argument state.

    """
    target = args[0] if args else None
    target_args = tuple(args[1:]) if args else ()
    return CliArgs(target=target, target_args=target_args, breaks=tuple(breaks))


def _handle_flag_arg(arg: str) -> CliArgs | None:
    """Return `CliArgs` for standalone help or version flags, or `None`.

    Args:
        arg (str): Argument flag to inspect.

    Returns:
        CliArgs | None: Flag result or `None` if not a help or version flag.

    """
    if arg in {"-h", "--help"}:
        return CliArgs(show_help=True)
    if arg in {"-v", "--version"}:
        return CliArgs(show_version=True)
    return None


def _parse_positional_or_error(
    arg: str,
    rest: Sequence[str],
    breaks: list[str],
) -> CliArgs:
    """Parse a non-option argument as target, or return an unknown option error.

    Args:
        arg (str): Argument token to inspect.
        rest (Sequence[str]): Remaining CLI tokens.
        breaks (list[str]): Collected breakpoints.

    Returns:
        CliArgs: Parsed target or unknown option error.

    """
    if arg.startswith("-"):
        return CliArgs(error=f"Unknown option '{arg}'.")
    return CliArgs(target=arg, target_args=tuple(rest), breaks=tuple(breaks))


def _process_arg_step(
    arg: str,
    args: Sequence[str],
    idx: int,
    breaks: list[str],
) -> tuple[int, CliArgs | None]:
    """Process a single argument token and return next index and optional result.

    Args:
        arg (str): Current argument token.
        args (Sequence[str]): Full arguments sequence.
        idx (int): Current token index.
        breaks (list[str]): Accumulated breakpoints.

    Returns:
        tuple[int, CliArgs | None]: Next index to inspect and parsed result if terminal.

    """
    if arg == "--":
        return (len(args), _handle_delimiter(args[idx + 1 :], breaks))
    flag_result = _handle_flag_arg(arg)
    if flag_result is not None:
        return (len(args), flag_result)
    if arg in {"-b", "--break"} or arg.startswith(("-b=", "--break=")):
        return _consume_break(arg, args, idx, breaks)
    return (len(args), _parse_positional_or_error(arg, args[idx + 1 :], breaks))


def parse_cli_args(args: Sequence[str]) -> CliArgs:
    """Parse raw CLI argument strings into structured `CliArgs`.

    Args:
        args (Sequence[str]): List of command-line argument strings.

    Returns:
        CliArgs: Structured parsed CLI options and arguments.

    """
    breaks: list[str] = []
    idx = 0
    while idx < len(args):
        next_idx, result = _process_arg_step(args[idx], args, idx, breaks)
        if result is not None:
            return result
        idx = next_idx

    return CliArgs(breaks=tuple(breaks))


def _run_target(parsed: CliArgs) -> int:
    """Execute the target under dpdb and return its exit status code.

    Args:
        parsed (CliArgs): Parsed CLI arguments containing target and options.

    Returns:
        int: Process exit code.

    """
    if parsed.target is None:
        return 0
    try:
        execute_with_debug(
            target_name=parsed.target,
            target_args=list(parsed.target_args),
            breaks=list(parsed.breaks) if parsed.breaks else None,
        )
    except SystemExit as exc:
        code = exc.code
        return code if isinstance(code, int) else 0 if code is None else 1
    else:
        return 0


def _dispatch_parsed(
    parsed: CliArgs,
    out_console: Console,
    err_console: Console,
) -> int:
    """Dispatch action for parsed CLI arguments.

    Args:
        parsed (CliArgs): Parsed options and target specification.
        out_console (Console): Console for normal output.
        err_console (Console): Console for error messages.

    Returns:
        int: Exit status code.

    """
    if parsed.error is not None:
        err_console.print(f"[bold red]Error:[/bold red] {parsed.error}")
        return 2
    if parsed.show_help:
        render_help(out_console)
        return 0
    if parsed.show_version:
        out_console.print(f"dojo {get_version()}")
        return 0
    return _run_target(parsed)


def cli(
    args: Sequence[str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Execute the `dojo` command-line interface.

    Args:
        args (Sequence[str] | None): Argument list. Defaults to `sys.argv[1:]`.
        stdout (TextIO | None): Stream for standard output. Defaults to `sys.stdout`.
        stderr (TextIO | None): Stream for error output. Defaults to `sys.stderr`.

    Returns:
        int: Exit status code (0 for success, non-zero for errors).

    """
    out_file = sys.stdout if stdout is None else stdout
    err_file = sys.stderr if stderr is None else stderr
    out_console = Console(
        file=out_file,
        highlight=False,
        soft_wrap=True,
        legacy_windows=False,
    )
    err_console = Console(
        file=err_file,
        highlight=False,
        soft_wrap=True,
        legacy_windows=False,
    )

    raw_args = list(args) if args is not None else sys.argv[1:]
    if not raw_args:
        render_help(out_console)
        return 0

    return _dispatch_parsed(parse_cli_args(raw_args), out_console, err_console)


def main() -> None:
    """Entry point for the `debug-dojo` and `dojo` CLI commands."""
    sys.exit(cli())
