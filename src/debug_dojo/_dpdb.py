"""IPython-powered interactive debugger (`dpdb`) with Rich visual enhancements."""

from __future__ import annotations

import ast
import bdb
import contextlib
import functools
import inspect
import io
import keyword
import linecache
import os
import reprlib
import sys
import tokenize
from collections.abc import Callable, Mapping, MutableMapping, Sequence, Sized
from pathlib import Path
from types import CodeType, FrameType, ModuleType, TracebackType
from typing import Any, Literal, cast, override

from IPython.core.debugger import Pdb
from IPython.core.getipython import get_ipython
from IPython.terminal.debugger import TerminalPdb
from IPython.terminal.embed import (  # ruff: ignore[debugger] -- used by DojoPdb.do_interact to launch an embedded IPython shell
    InteractiveShellEmbed,
)
from IPython.terminal.ipapp import TerminalIPythonApp
from rich import box, inspect as rich_inspect
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.pretty import Pretty, pprint as rich_pprint
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

BREAKPOINT_ENV_VAR = "PYTHONBREAKPOINT"
DPDB_SET_TRACE_HOOK = "debug_dojo.set_trace"

DEFAULT_CONTEXT_LINES = 20
STEP_CONTEXT_LINES = 5
MAX_MRO_PREVIEW = 4
MAX_INLINE_BANNER_ITEMS = 4
MAX_CHAINED_EXCEPTIONS = 5

_HIDDEN_MODULE_PREFIXES: tuple[str, ...] = (
    "bdb",
    "click",
    "debug_dojo",
    "runpy",
    "typer",
)

_REPEATABLE_COMMANDS: frozenset[str] = frozenset(
    {
        "c",
        "cont",
        "continue",
        "d",
        "down",
        "l",
        "list",
        "ll",
        "longlist",
        "n",
        "next",
        "r",
        "return",
        "s",
        "step",
        "u",
        "unt",
        "until",
        "up",
    }
)

_HELP_ROWS: tuple[tuple[str, str, str], ...] = (
    ("Stepping", "n / next", "Execute current line and stop at next line in frame"),
    ("", "s / step", "Step into function call on current line"),
    ("", "r / return", "Continue execution until current function returns"),
    ("", "c / cont / continue", "Continue execution until next breakpoint"),
    ("", "unt / until [line]", "Continue until line greater than current (or line)"),
    ("", "j / jump <line>", "Set next line number to be executed"),
    ("Stack", "w / where / bt", "Display compact Rich call stack table"),
    ("", "u / up [count]", "Move up to an older stack frame"),
    ("", "d / down [count]", "Move down to a newer stack frame"),
    ("Source", "l / list [first, last]", "List source code lines around current line"),
    ("", "ll / longlist", "List full source code for current function or frame"),
    ("", "context <lines>", "Set number of context lines shown on frame entry"),
    ("", "psource <expr>", "Show syntax-highlighted source panel for an object"),
    ("Inspection", "p / pp <expr>", "Rich-print or pretty-expand expression value"),
    ("", "a / args", "Display Rich table of current function arguments"),
    ("", "pinfo / pinfo2 [expr]", "Inspect object (or frame locals) in Rich panel"),
    ("", "whatis <expr>", "Display type, MRO, and signature/size in Rich panel"),
    ("", "display [expr]", "Watch expression across steps or list active watches"),
    ("", "undisplay [expr]", "Remove watch expression(s) in current frame"),
    (
        "Breakpoints",
        "b / break [loc, cond]",
        "List breakpoints table or set breakpoint",
    ),
    ("", "tbreak [loc, cond]", "Set temporary one-shot breakpoint"),
    ("", "cl / clear [bp#]", "Clear specified or all breakpoints"),
    ("", "enable / disable <bp#>", "Enable or disable breakpoint(s) by number"),
    ("", "condition <bp#> [expr]", "Set or clear condition on a breakpoint"),
    ("Session", "interact", "Start interactive IPython shell in current frame"),
    ("", "run / restart [args]", "Restart target program with current breakpoints"),
    ("", "!<statement>", "Execute Python statement in current frame namespace"),
    ("", "h / help [cmd]", "Show this command reference or help for a command"),
    ("", "q / quit / exit", "Abort execution and exit debugger"),
)


def _format_shape_or_len(val: object) -> str:
    """Format the shape or length summary of a value for variable tables.

    Args:
        val (object): Value to summarize.

    Returns:
        str: Formatted `shape=...`, `len=...`, or `"-"` when not applicable.

    """
    shape = getattr(val, "shape", None)
    if shape is not None and not callable(shape):
        return f"shape={shape}"
    if isinstance(val, Sized):
        return f"len={len(val)}"
    return "-"


def _is_user_local(name: str, val: object) -> bool:
    """Return whether a frame variable should be shown as a user variable.

    Args:
        name (str): Variable identifier.
        val (object): Bound runtime value.

    Returns:
        bool: `True` when the variable is a user-level binding.

    """
    if (
        name == "_"
        or (name.startswith("__") and name.endswith("__"))
        or name.startswith("@")
    ):
        return False
    return not isinstance(val, ModuleType)


def _is_runner_frame(frame: FrameType) -> bool:
    """Return whether `frame` belongs to an internal runner or CLI framework module.

    Args:
        frame (FrameType): Stack frame to inspect.

    Returns:
        bool: `True` if the frame belongs to `debug_dojo`, `runpy`, `bdb`, `typer`,
            or `click`.

    """
    filename = frame.f_code.co_filename
    if filename == "<frozen runpy>" or Path(filename).name in {"dojo", "debug-dojo"}:
        return True
    mod_name = str(frame.f_globals.get("__name__", ""))
    return any(
        mod_name == prefix or mod_name.startswith(f"{prefix}.")
        for prefix in _HIDDEN_MODULE_PREFIXES
    )


def _snapshot_user_locals(frame_locals: Mapping[str, object]) -> dict[str, str]:
    """Capture truncated string representations of user-level frame locals.

    Args:
        frame_locals (Mapping[str, object]): Frame local mapping.

    Returns:
        dict[str, str]: Mapping of variable names to compact `repr` strings.

    """
    return {
        name: reprlib.repr(val)
        for name, val in frame_locals.items()
        if _is_user_local(name, val)
    }


def _compute_locals_diff(
    prev: Mapping[str, str] | None,
    current: Mapping[str, str],
) -> list[str]:
    """Compute Rich markup fragments describing added or modified local variables.

    Args:
        prev (Mapping[str, str] | None): Previous snapshot for the same frame.
        current (Mapping[str, str]): Current snapshot for the frame.

    Returns:
        list[str]: Formatted Rich markup diff entries.

    """
    if prev is None:
        return []
    diffs: list[str] = []
    for name, cur_repr in current.items():
        if name not in prev:
            diffs.append(
                f"[bold green]+ {escape(name)}[/bold green] = {escape(cur_repr)}"
            )
        elif prev[name] != cur_repr:
            diffs.append(
                f"[bold yellow]Δ {escape(name)}[/bold yellow]: "
                f"{escape(prev[name])} → {escape(cur_repr)}"
            )
    diffs.extend(
        f"[bold red]- {escape(name)}[/bold red]" for name in prev if name not in current
    )
    return diffs


def _join_inline_items(
    items: Sequence[str],
    max_items: int = MAX_INLINE_BANNER_ITEMS,
) -> str:
    """Join inline banner fragments, truncating excess entries with `(+N more)`.

    Args:
        items (Sequence[str]): Formatted Rich markup fragments.
        max_items (int): Maximum number of entries to display inline.

    Returns:
        str: Joined Rich markup string.

    """
    visible = ", ".join(items[:max_items])
    extra = len(items) - max_items
    if extra > 0:
        return f"{visible} [dim](+{extra} more)[/dim]"
    return visible


def _tokenize_identifiers(source_line: str) -> list[str]:
    """Extract unique non-keyword identifier names from a source line.

    Args:
        source_line (str): Single Python source line.

    Returns:
        list[str]: Ordered unique variable identifiers appearing on the line.

    """
    seen: list[str] = []
    reader = io.StringIO(source_line).readline
    try:
        for tok in tokenize.generate_tokens(reader):
            if (
                tok.type == tokenize.NAME
                and not keyword.iskeyword(tok.string)
                and tok.string not in seen
            ):
                seen.append(tok.string)
    except (tokenize.TokenError, IndentationError):
        pass
    return seen


def _resolve_line_var(
    name: str,
    frame_locals: Mapping[str, object],
    frame_globals: Mapping[str, object],
) -> str | None:
    """Format a single `name=value` entry if `name` is a user-visible variable.

    Args:
        name (str): Identifier name from the active source line.
        frame_locals (Mapping[str, object]): Current frame local variables.
        frame_globals (Mapping[str, object]): Current frame global variables.

    Returns:
        str | None: Rich markup `name=value` string, or `None` if not resolved.

    """
    namespace = (
        frame_locals
        if name in frame_locals
        else frame_globals
        if name in frame_globals
        else None
    )
    if namespace is None:
        return None
    val = namespace[name]
    if not _is_user_local(name, val) or callable(val):
        return None
    return f"[bold cyan]{escape(name)}[/bold cyan]={escape(reprlib.repr(val))}"


def _extract_line_variables(
    source_line: str,
    frame_locals: Mapping[str, object],
    frame_globals: Mapping[str, object],
) -> list[str]:
    """Resolve values of variables referenced on the currently executing source line.

    Args:
        source_line (str): Source line at the active frame line number.
        frame_locals (Mapping[str, object]): Current frame local variables.
        frame_globals (Mapping[str, object]): Current frame global variables.

    Returns:
        list[str]: Rich markup `name=value` fragments for active-line variables.

    """
    fragments: list[str] = []
    for name in _tokenize_identifiers(source_line):
        rendered = _resolve_line_var(name, frame_locals, frame_globals)
        if rendered is not None:
            fragments.append(rendered)
    return fragments


def _format_return_banner(frame_locals: Mapping[str, object]) -> str | None:
    """Format a return value summary when `__return__` is present in `frame_locals`.

    Args:
        frame_locals (Mapping[str, object]): Current frame local variables.

    Returns:
        str | None: Rich markup for the return value, or `None` if not returning.

    """
    if "__return__" not in frame_locals:
        return None
    rv = frame_locals["__return__"]
    return (
        f"[bold magenta]{escape(reprlib.repr(rv))}[/bold magenta] "
        f"[dim]({escape(type(rv).__name__)})[/dim]"
    )


def _format_watch_entries(
    displaying: MutableMapping[str, object] | None,
    eval_fn: Callable[[str], object],
) -> list[str]:
    """Evaluate active `display` watch expressions and format Rich status fragments.

    Args:
        displaying (MutableMapping[str, object] | None): Mapping of watched
            expressions to their last seen values for the active frame.
        eval_fn (Callable[[str], object]): Evaluator returning current value for
            an expression string.

    Returns:
        list[str]: Formatted Rich markup watch fragments.

    """
    if not displaying:
        return []
    entries: list[str] = []
    for expr, old_val in list(displaying.items()):
        new_val = eval_fn(expr)
        new_repr = reprlib.repr(new_val)
        if new_val is not old_val and new_val != old_val:
            old_repr = reprlib.repr(old_val)
            displaying[expr] = new_val
            entries.append(
                f"[bold yellow]Δ {escape(expr)}[/bold yellow]: "
                f"{escape(old_repr)} → {escape(new_repr)}"
            )
        else:
            entries.append(f"[bold blue]{escape(expr)}[/bold blue]={escape(new_repr)}")
    return entries


def _extract_arg_names(code: CodeType) -> list[str]:
    """Extract parameter names from a frame's code object.

    Args:
        code (CodeType): Frame code object.

    Returns:
        list[str]: Ordered parameter names including `*args` and `**kwargs`.

    """
    total = code.co_argcount + code.co_kwonlyargcount
    if code.co_flags & inspect.CO_VARARGS:
        total += 1
    if code.co_flags & inspect.CO_VARKEYWORDS:
        total += 1
    return list(code.co_varnames[:total])


def _build_variables_table(
    title: str,
    items: Sequence[tuple[str, object, bool]],
) -> Table:
    """Build a Rich table displaying variable names, types, sizes, and values.

    Args:
        title (str): Table header title.
        items (Sequence[tuple[str, object, bool]]): Sequence of
            `(name, value, is_defined)` tuples.

    Returns:
        Table: Configured Rich `Table` instance.

    """
    table = Table(
        title=title,
        box=box.ROUNDED,
        header_style="bold cyan",
        title_style="bold",
        expand=False,
    )
    table.add_column("Name", style="bold cyan", no_wrap=True)
    table.add_column("Type", style="magenta", no_wrap=True)
    table.add_column("Size", style="dim", no_wrap=True)
    table.add_column("Value")

    for name, val, is_defined in items:
        if not is_defined:
            table.add_row(
                name,
                "-",
                "-",
                Text("*** undefined ***", style="italic red"),
            )
        else:
            table.add_row(
                name,
                type(val).__name__,
                _format_shape_or_len(val),
                Pretty(val, max_length=10, max_string=60),
            )
    return table


def _add_stack_row(
    table: Table,
    idx: int,
    frame: FrameType,
    lineno: int,
    *,
    is_cur: bool,
) -> None:
    """Append a single formatted frame row to the call stack table.

    Args:
        table (Table): Target Rich table.
        idx (int): Stack frame index.
        frame (FrameType): Frame object.
        lineno (int): Active line number in `frame`.
        is_cur (bool): Whether `frame` is the currently selected frame.

    """
    marker = "[bold green]→[/bold green]" if is_cur else ""
    func = frame.f_code.co_name or "<module>"
    func_cell = (
        f"[bold cyan]{escape(func)}()[/bold cyan]"
        if is_cur
        else f"[cyan]{escape(func)}()[/cyan]"
    )
    loc = f"{escape(Path(frame.f_code.co_filename).name)}:{lineno}"
    src = escape(linecache.getline(frame.f_code.co_filename, lineno).strip())
    src_cell = f"[bold]{src}[/bold]" if is_cur else f"[dim]{src}[/dim]"
    table.add_row(marker, str(idx), func_cell, loc, src_cell)


def _build_stack_table(
    stack: Sequence[tuple[FrameType, int]],
    hidden_flags: Sequence[bool],
    curframe: FrameType | None,
    *,
    skip_hidden: bool,
) -> Table:
    """Build a compact Rich table summarizing the call stack.

    Args:
        stack (Sequence[tuple[FrameType, int]]): Debugger frame-lineno stack.
        hidden_flags (Sequence[bool]): Per-frame hidden status flags.
        curframe (FrameType | None): Currently selected stack frame.
        skip_hidden (bool): Whether hidden frames should be collapsed.

    Returns:
        Table: Configured Rich `Table` of call stack entries.

    """
    table = Table(
        title="Call Stack",
        box=box.ROUNDED,
        header_style="bold cyan",
        title_style="bold",
        expand=False,
    )
    table.add_column("", width=2, no_wrap=True)
    table.add_column("#", style="dim", justify="right", no_wrap=True)
    table.add_column("Function", no_wrap=True)
    table.add_column("Location", style="magenta", no_wrap=True)
    table.add_column("Source")

    skipped = 0
    for idx, (hidden, (frame, lineno)) in enumerate(
        zip(hidden_flags, stack, strict=False)
    ):
        if hidden and skip_hidden:
            skipped += 1
            continue
        if skipped:
            table.add_row(
                "",
                "...",
                f"[dim]skipped {skipped} hidden frame(s)[/dim]",
                "",
                "",
            )
            skipped = 0
        _add_stack_row(table, idx, frame, lineno, is_cur=frame is curframe)

    if skipped:
        table.add_row(
            "",
            "...",
            f"[dim]skipped {skipped} hidden frame(s)[/dim]",
            "",
            "",
        )
    return table


def _build_breakpoints_table(breakpoints: Sequence[bdb.Breakpoint]) -> Table:
    """Build a Rich table listing all active breakpoints.

    Args:
        breakpoints (Sequence[bdb.Breakpoint]): Active `bdb.Breakpoint` objects.

    Returns:
        Table: Configured Rich `Table` of breakpoints.

    """
    table = Table(
        title="Breakpoints",
        box=box.ROUNDED,
        header_style="bold cyan",
        title_style="bold",
        expand=False,
    )
    table.add_column("#", style="bold cyan", justify="right", no_wrap=True)
    table.add_column("State", no_wrap=True)
    table.add_column("Location", style="magenta", no_wrap=True)
    table.add_column("Hits", style="dim", justify="right", no_wrap=True)
    table.add_column("Condition")

    for bp in breakpoints:
        state = "[green]enabled[/green]" if bp.enabled else "[red]disabled[/red]"
        if bp.temporary:
            state = f"{state} [dim](temp)[/dim]"
        loc = f"{escape(Path(bp.file).name)}:{bp.line}"
        cond = escape(bp.cond) if bp.cond else "-"
        table.add_row(str(bp.number), state, loc, str(bp.hits), cond)
    return table


def _format_callable_signature(val: object) -> str | None:
    """Return the formatted signature of `val` if it is an inspectable callable.

    Args:
        val (object): Object to inspect.

    Returns:
        str | None: String signature, or `None` when not applicable.

    """
    if not callable(val):
        return None
    try:
        return str(inspect.signature(val))
    except (ValueError, TypeError):
        return None


def _build_whatis_panel(expr: str, val: object) -> Panel:
    """Build a Rich summary panel describing the type and signature of `val`.

    Args:
        expr (str): Expression string queried via `whatis`.
        val (object): Evaluated object.

    Returns:
        Panel: Rich `Panel` displaying type, MRO, and signature/size metadata.

    """
    cls = val if isinstance(val, type) else type(val)
    kind = "Class" if isinstance(val, type) else "Instance"
    type_name = f"{cls.__module__}.{cls.__qualname__}"
    mro_chain = " → ".join(
        base.__name__ for base in getattr(cls, "__mro__", ())[:MAX_MRO_PREVIEW]
    )
    lines = [
        f"[dim]Kind:[/dim]      [bold]{kind}[/bold]",
        f"[dim]Type:[/dim]      [magenta]{escape(type_name)}[/magenta]",
        f"[dim]MRO:[/dim]       {escape(mro_chain)}",
    ]
    sig = _format_callable_signature(val)
    if sig is not None:
        lines.append(f"[dim]Signature:[/dim] [cyan]{escape(sig)}[/cyan]")
    else:
        lines.append(f"[dim]Size:[/dim]      {escape(_format_shape_or_len(val))}")
    return Panel(
        "\n".join(lines),
        title=f"[bold cyan]whatis {escape(expr)}[/bold cyan]",
        border_style="cyan",
        expand=False,
    )


def _build_psource_panel(expr: str, val: object) -> Panel | None:
    """Build a syntax-highlighted Rich panel for the source code of `val`.

    Args:
        expr (str): Expression or symbol name.
        val (object): Target object whose source should be extracted.

    Returns:
        Panel | None: Rich `Panel` with syntax-highlighted source, or `None` if
            source code cannot be retrieved.

    """
    target = cast("Any", val)
    try:
        lines, start_line = inspect.getsourcelines(target)
        source_file = inspect.getsourcefile(target) or "<unknown>"
    except (OSError, TypeError):
        return None
    syntax = Syntax(
        "".join(lines),
        "python",
        line_numbers=True,
        start_line=start_line,
        word_wrap=False,
    )
    filename = Path(source_file).name
    panel_title = (
        f"[bold cyan]{escape(expr)} ({escape(filename)}:{start_line})[/bold cyan]"
    )
    return Panel(
        syntax,
        title=panel_title,
        border_style="cyan",
        expand=False,
    )


def _build_help_table() -> Table:
    """Build the categorized Rich overview table for `help` with no arguments.

    Returns:
        Table: Configured Rich `Table` of debugger commands.

    """
    table = Table(
        title="dpdb Commands (type 'help <command>' for details)",
        box=box.ROUNDED,
        header_style="bold cyan",
        title_style="bold",
        expand=False,
    )
    table.add_column("Category", style="bold magenta", no_wrap=True)
    table.add_column("Command", style="bold cyan", no_wrap=True)
    table.add_column("Description")

    for category, command, description in _HELP_ROWS:
        table.add_row(category, escape(command), escape(description))
    return table


def _build_command_help_panel(cmd_name: str, raw_doc: str) -> Panel:
    """Build a Rich panel displaying cleaned help documentation for `cmd_name`.

    Args:
        cmd_name (str): Command name queried by the user.
        raw_doc (str): Raw docstring from `do_<cmd_name>`.

    Returns:
        Panel: Configured Rich `Panel` containing the command help text.

    """
    cleaned = inspect.cleandoc(raw_doc)
    user_doc = cleaned.split("\n\nArgs:", maxsplit=1)[0].strip()
    return Panel(
        escape(user_doc),
        title=f"[bold cyan]help {escape(cmd_name)}[/bold cyan]",
        border_style="cyan",
        expand=False,
    )


def _format_chained_exception_line(label: str, exc: BaseException) -> str:
    """Format a single chained exception (`__cause__` or `__context__`) summary line.

    Args:
        label (str): Relationship label (`"Caused by"` or `"During handling of"`).
        exc (BaseException): Chained exception instance.

    Returns:
        str: Rich-formatted summary line with optional innermost frame location.

    """
    tb = exc.__traceback__
    while tb is not None and tb.tb_next is not None:
        tb = tb.tb_next
    fname = Path(tb.tb_frame.f_code.co_filename).name if tb is not None else ""
    loc = f" — [cyan]{escape(fname)}:{tb.tb_lineno}[/cyan]" if tb is not None else ""
    return (
        f"[dim]{label}:[/dim] [bold yellow]{escape(type(exc).__name__)}[/bold yellow]: "
        f"{escape(str(exc))}{loc}"
    )


def _format_exception_chain(exc: BaseException | None) -> list[str]:
    """Collect formatted lines for any chained exceptions (`__cause__` / `__context__`).

    Args:
        exc (BaseException | None): Top-level exception being inspected.

    Returns:
        list[str]: Formatted lines describing the exception chain.

    """
    lines: list[str] = []
    seen: set[int] = set()
    cur = exc
    while (
        cur is not None and id(cur) not in seen and len(lines) < MAX_CHAINED_EXCEPTIONS
    ):
        seen.add(id(cur))
        cause = cur.__cause__
        context = None if cur.__suppress_context__ else cur.__context__
        if cause is not None:
            lines.append(_format_chained_exception_line("Caused by", cause))
            cur = cause
        elif context is not None:
            lines.append(_format_chained_exception_line("During handling of", context))
            cur = context
        else:
            break
    return lines


def _extract_callable_target(obj: object) -> object:
    """Resolve `functools.partial`, `property`, classes, or callable instances.

    Args:
        obj (object): Candidate callable or descriptor object.

    Returns:
        object: Underlying function or method object.

    """
    target = obj
    while isinstance(target, functools.partial):
        target = target.func
    if isinstance(target, property) and target.fget is not None:
        return target.fget
    if isinstance(target, type):
        return getattr(target, "__init__", target)
    if not inspect.isroutine(target) and callable(target):
        return type(target).__call__
    return target


def _unwrap_callable_code(obj: object) -> CodeType | None:
    """Extract the `CodeType` of a callable object if backed by a source file.

    Args:
        obj (object): Object evaluated from a breakpoint expression.

    Returns:
        CodeType | None: Resolved code object if its file exists on disk, else `None`.

    """
    target = _extract_callable_target(obj)
    if callable(target):
        with contextlib.suppress(Exception):
            target = inspect.unwrap(target)
    code = getattr(target, "__code__", None)
    if isinstance(code, CodeType) and Path(code.co_filename).is_file():
        return code
    return None


def _render_post_mortem_banner(tb: TracebackType, console: Console) -> None:
    """Render a Rich post-mortem exception header panel before entering interaction.

    Args:
        tb (TracebackType): Exception traceback to summarize.
        console (Console): Target Rich console.

    """
    last_tb = tb
    while last_tb.tb_next is not None:
        last_tb = last_tb.tb_next

    frame = last_tb.tb_frame
    lineno = last_tb.tb_lineno
    filename = Path(frame.f_code.co_filename).name
    func = frame.f_code.co_name or "<module>"
    source_line = linecache.getline(frame.f_code.co_filename, lineno).strip()

    exc_type, exc_val, _ = sys.exc_info()
    exc_header = (
        f"[bold red]{escape(exc_type.__name__)}[/bold red]: {escape(str(exc_val))}"
        if exc_type is not None
        else "[bold red]Unhandled Exception[/bold red]"
    )
    location_line = (
        f"[dim]Location:[/dim] [cyan]{escape(filename)}:{lineno}[/cyan] "
        f"in [bold]{escape(func)}()[/bold]"
    )
    lines = [exc_header, location_line]
    if source_line:
        lines.append(f"[dim]Code:[/dim]     {escape(source_line)}")
    lines.extend(_format_exception_chain(exc_val))
    console.print(
        Panel(
            "\n".join(lines),
            title="[bold red]💥 Dojo Post-Mortem[/bold red]",
            border_style="red",
            expand=False,
        )
    )


def _is_explicit_return_line(frame: FrameType) -> bool:
    """Return `True` if the active source line in `frame` is a `return` statement.

    Args:
        frame (FrameType): Stack frame to inspect.

    Returns:
        bool: `True` when the stripped line starts with `return`.

    """
    line = linecache.getline(frame.f_code.co_filename, frame.f_lineno).strip()
    return line == "return" or line.startswith(("return ", "return("))


class DojoPdb(TerminalPdb):  # ruff: ignore[too-many-public-methods] -- overrides standard Pdb/Cmd command methods and lifecycle helpers
    """Enhanced IPython debugger with Rich inspection and live frame context."""

    displaying: dict[FrameType, dict[str, object]]
    _full_context: int
    _last_paused_location: tuple[int, int] | None
    _last_printed_frame_id: int | None
    _managed_underscore_frames: set[int]
    _prev_locals_by_frame: dict[int, dict[str, str]]
    _suppress_message: bool

    @override
    def __init__(
        self,
        *args: object,
        pt_session_options: Mapping[str, object] | None = None,
        **kwargs: object,
    ) -> None:
        """Initialize the DojoPdb debugger session.

        Args:
            *args (object): Positional arguments forwarded to `TerminalPdb`.
            pt_session_options (Mapping[str, object] | None): Optional
                `prompt_toolkit` session options.
            **kwargs (object): Keyword arguments forwarded to `TerminalPdb`.

        """
        self._last_paused_location = None
        self._last_printed_frame_id = None
        self._managed_underscore_frames = set()
        self._prev_locals_by_frame = {}
        self._suppress_message = False
        session_opts: dict[str, object] = {
            "bottom_toolbar": self._render_bottom_toolbar,
        }
        if pt_session_options is not None:
            session_opts.update(pt_session_options)
        super().__init__(
            *args,
            pt_session_options=session_opts,
            **kwargs,
        )
        self._full_context = self.context
        self.prompt = "dpdb> "

    def close(self) -> None:
        """Close prompt_toolkit event loop and executor resources."""
        loop = getattr(self, "pt_loop", None)
        if loop is not None and not loop.is_closed():
            loop.close()
        executor = getattr(self, "thread_executor", None)
        if executor is not None:
            executor.shutdown(wait=False)

    def __del__(self) -> None:
        """Ensure background loop and executor are closed on garbage collection."""
        self.close()

    def _console(self) -> Console:
        """Return a Rich console bound to the debugger's `stdout` stream.

        Returns:
            Console: Rich console writing to `self.stdout`.

        """
        return Console(file=self.stdout, highlight=True, soft_wrap=True)

    @override
    def message(self, msg: str) -> None:
        """Print a message to stdout unless suppressed.

        Args:
            msg (str): Message text to output.

        """
        if not self._suppress_message:
            super().message(msg)

    def _format_frame_location(self) -> tuple[str, str, int]:
        """Extract `(filename, function_name, lineno)` for the current stack frame.

        Returns:
            tuple[str, str, int]: Current file basename, function name, and line number.

        """
        frame = getattr(self, "curframe", None)
        if frame is None:
            return ("<unknown>", "<unknown>", 0)
        filename = Path(frame.f_code.co_filename).name
        func = frame.f_code.co_name or "<module>"
        return (filename, func, frame.f_lineno)

    def _render_bottom_toolbar(self) -> str:
        """Format the `prompt_toolkit` bottom toolbar status line.

        Returns:
            str: Single-line status and keybinding hint bar.

        """
        filename, func, lineno = self._format_frame_location()
        bp_count = sum(len(lines) for lines in self.breaks.values())
        return (
            f" dpdb | {filename}:{lineno} in {func}() | {bp_count} bp | "
            "n:next  s:step  c:cont  w:where  b:breaks  "
            "p/pp:print  a:args  pinfo:inspect  q:quit "
        )

    def _render_frame_context_banner(self, frame: FrameType, lineno: int) -> None:
        """Render return values, changed locals, line vars, and watches below source.

        Args:
            frame (FrameType): Active stack frame.
            lineno (int): Active line number in `frame`.

        """
        frame_locals = self._get_frame_locals(frame)
        return_banner = _format_return_banner(frame_locals)

        current_snapshot = _snapshot_user_locals(frame_locals)
        frame_key = id(frame)
        diffs = _compute_locals_diff(
            self._prev_locals_by_frame.get(frame_key),
            current_snapshot,
        )
        self._prev_locals_by_frame[frame_key] = current_snapshot

        source_line = linecache.getline(frame.f_code.co_filename, lineno)
        line_vars: list[str] = (
            []
            if return_banner is not None
            else _extract_line_variables(
                source_line,
                frame_locals,
                frame.f_globals,
            )
        )
        watches = _format_watch_entries(
            self.displaying.get(frame),
            self._getval_except,
        )

        if not (return_banner or diffs or line_vars or watches):
            return

        console = self._console()
        if return_banner is not None:
            console.print(f"  [bold magenta]↩ Return:[/bold magenta]  {return_banner}")
        if diffs:
            console.print(
                "  [bold yellow]Δ Changed:[/bold yellow] " + _join_inline_items(diffs)
            )
        if line_vars:
            console.print(
                "  [bold cyan]↳ Line:[/bold cyan]    " + _join_inline_items(line_vars)
            )
        if watches:
            console.print(
                "  [bold blue]👁 Watch:[/bold blue]   " + _join_inline_items(watches)
            )

    def _show_display(self) -> None:
        """Suppress stdlib plain-text display output (handled in context banner)."""

    @override
    def _hidden_predicate(self, frame: FrameType) -> bool:
        """Return whether `frame` should be hidden from stack navigation and traces.

        Args:
            frame (FrameType): Stack frame to check.

        Returns:
            bool: `True` when the frame should be skipped when `skip_hidden` is active.

        """
        if frame in {self.curframe, getattr(self, "initial_frame", None)}:
            return False
        if self._predicates.get("tbhide", True) and _is_runner_frame(frame):
            return True
        return bool(super()._hidden_predicate(frame))

    @override
    def stop_here(self, frame: FrameType) -> bool:
        """Return whether execution should stop at `frame` during stepping.

        Args:
            frame (FrameType): Candidate stack frame.

        Returns:
            bool: `False` when `frame` is hidden, otherwise superclass result.

        """
        if self.skip_hidden and self._hidden_predicate(frame):
            if _is_runner_frame(frame):
                self.stopframe = getattr(self, "botframe", None)
                self.returnframe = None
                self.stoplineno = -1
            return False
        return bool(super().stop_here(frame))

    def _should_skip_return_pause(
        self,
        frame: FrameType,
    ) -> bool:
        """Return whether `user_return` should advance past `frame` without pausing.

        Args:
            frame (FrameType): Returning stack frame.

        Returns:
            bool: `True` when pausing on the return event would be redundant.

        """
        if frame.f_code.co_name == "<module>":
            return True
        stripped = getattr(self, "lastcmd", "").strip()
        cmd_name = stripped.split(maxsplit=1)[0] if stripped else ""
        if cmd_name in {"r", "ret", "return"}:
            return False
        return (
            id(frame),
            frame.f_lineno,
        ) == self._last_paused_location and _is_explicit_return_line(frame)

    @override
    def user_return(self, frame: FrameType, return_value: object) -> None:
        """Handle function return events while skipping redundant or hidden returns.

        Args:
            frame (FrameType): Returning stack frame.
            return_value (object): Value returned by `frame`.

        """
        if getattr(self, "_wait_for_mainpyfile", False):
            return
        if self.skip_hidden and self._hidden_predicate(frame):
            return
        if self._should_skip_return_pause(frame):
            self.set_step()
            return
        self._suppress_message = True
        try:
            super().user_return(frame, return_value)
        finally:
            self._suppress_message = False

    @override
    def emptyline(self) -> bool:
        """Repeat `lastcmd` on empty Enter only when it is a safe navigation command.

        Returns:
            bool: Result of repeating `lastcmd`, or `False` when ignored.

        """
        stripped = self.lastcmd.strip()
        cmd_name = stripped.split(maxsplit=1)[0] if stripped else ""
        if cmd_name in _REPEATABLE_COMMANDS:
            return bool(super().emptyline())
        return False

    def _store_last_result(self, val: object) -> None:
        """Store `val` in `_` within the active frame unless `_` is a user parameter.

        Args:
            val (object): Evaluated expression value.

        """
        if val is None:
            return
        frame = getattr(self, "curframe", None)
        if frame is None:
            return
        frame_key = id(frame)
        if (
            "_" in frame.f_code.co_varnames
            and frame_key not in self._managed_underscore_frames
        ):
            return
        self._managed_underscore_frames.add(frame_key)
        frame_locals = cast(
            "MutableMapping[str, object]", self._get_frame_locals(frame)
        )
        frame_locals["_"] = val

    @override
    def print_stack_entry(
        self,
        frame_lineno: tuple[FrameType, int],
        prompt_prefix: str = "\n-> ",
    ) -> None:
        """Print a stack entry with adaptive context lines and live variable banner.

        Args:
            frame_lineno (tuple[FrameType, int]): Target `(frame, lineno)` pair.
            prompt_prefix (str): Prefix string forwarded to superclass.

        """
        frame, lineno = frame_lineno
        is_current = frame is getattr(self, "curframe", None)
        if is_current and id(frame) == self._last_printed_frame_id:
            self.context = min(self._full_context, STEP_CONTEXT_LINES)
        else:
            self.context = self._full_context
        frame_locals = cast(
            "MutableMapping[str, object]", self._get_frame_locals(frame)
        )
        has_return = "__return__" in frame_locals
        saved_return = frame_locals.pop("__return__", None) if has_return else None
        try:
            super().print_stack_entry(frame_lineno, prompt_prefix)
        finally:
            if has_return:
                frame_locals["__return__"] = saved_return
            self.context = self._full_context
        if is_current:
            self._last_printed_frame_id = id(frame)
            self._last_paused_location = (id(frame), lineno)
            self._render_frame_context_banner(frame, lineno)

    @override
    def print_stack_trace(self, context: int | None = None) -> None:
        """Render a compact Rich call stack table followed by active frame context.

        Args:
            context (int | None): Optional context line override for the active frame.

        """
        del context
        console = self._console()
        table = _build_stack_table(
            self.stack,
            self.hidden_frames(self.stack),
            getattr(self, "curframe", None),
            skip_hidden=self.skip_hidden,
        )
        console.print(table)

    @override
    def do_context(self, context: str) -> None:
        """Set the number of source context lines shown on frame entry (`context`).

        Args:
            context (str): Positive integer number of lines.

        """
        super().do_context(context)
        self._full_context = self.context

    def _try_set_callable_break(
        self,
        expr: str,
        cond_str: str | None,
        *,
        temporary: bool,
    ) -> bool:
        """Attempt to resolve and set a breakpoint on a callable object.

        Args:
            expr (str): Expression to evaluate in the current frame.
            cond_str (str | None): Optional breakpoint condition expression.
            temporary (bool): Whether the breakpoint is temporary.

        Returns:
            bool: `True` if a callable breakpoint was handled, `False` otherwise.

        """
        if getattr(self, "curframe", None) is None:
            return False
        if ":" in expr or expr.isdigit():
            return False
        val = self._getval_except(expr)
        code = _unwrap_callable_code(val)
        if code is None:
            return False
        filename = self.canonic(code.co_filename)
        line = self.checkline(filename, code.co_firstlineno)
        if not line:
            return False
        err = self.set_break(filename, line, temporary, cond_str, code.co_name)
        if err:
            self.error(err)
        else:
            bp = self.get_breaks(filename, line)[-1]
            self.message(f"Breakpoint {bp.number} at {bp.file}:{bp.line}")
        return True

    @override
    def do_break(self, arg: str, temporary: Literal[0, 1] | bool = 0) -> None:
        """Set a breakpoint or render a Rich table of active breakpoints (`b`).

        Args:
            arg (str): Breakpoint location/condition, or empty to list breakpoints.
            temporary (Literal[0, 1] | bool): Whether the breakpoint is temporary.

        """
        if not arg.strip():
            active_bps = [bp for bp in bdb.Breakpoint.bpbynumber if bp is not None]
            console = self._console()
            if not active_bps:
                console.print("[dim]No breakpoints set.[/dim]")
                return
            console.print(_build_breakpoints_table(active_bps))
            return
        target_part, sep, cond_part = arg.partition(",")
        expr = target_part.strip()
        cond_str = cond_part.strip() if sep else None
        if self._try_set_callable_break(expr, cond_str, temporary=bool(temporary)):
            return
        super().do_break(arg, temporary)

    do_b = do_break

    @override
    def do_continue(self, arg: str) -> bool | None:
        """Continue execution until next breakpoint (`c`), or evaluate `c(...)`.

        Args:
            arg (str): Command argument, forwarded to evaluator when `c(...)`.

        Returns:
            bool | None: Superclass return value, or `None` when executing `c(...)`.

        """
        stripped = arg.strip()
        if stripped.startswith("(") and stripped.endswith(")"):
            self.default(f"c{stripped}")
            return None
        return super().do_continue(arg)

    do_c = do_continue
    do_cont = do_continue

    @override
    def do_display(self, arg: str) -> None:
        """Add a watch expression or render a Rich table of watched expressions.

        Args:
            arg (str): Expression to watch, or empty to list active watches.

        """
        target_expr = arg.strip()
        frame = getattr(self, "curframe", None)
        if not target_expr:
            watches = self.displaying.get(frame, {}) if frame is not None else {}
            console = self._console()
            if not watches:
                console.print("[dim]No expressions are being displayed.[/dim]")
                return
            items = [(expr, self._getval_except(expr), True) for expr in watches]
            console.print(_build_variables_table("Watched Expressions", items))
            return
        super().do_display(target_expr)

    @override
    def do_whatis(self, arg: str) -> None:
        """Display the type, MRO, and signature/size of an expression (`whatis`).

        Args:
            arg (str): Expression string to inspect.

        """
        target_expr = arg.strip()
        ok, val = self._eval_arg(target_expr)
        if ok:
            self._console().print(_build_whatis_panel(target_expr, val))

    @override
    def do_psource(self, arg: str) -> None:
        """Render syntax-highlighted source code for an object (`psource`).

        Args:
            arg (str): Expression or symbol name whose source should be shown.

        """
        target_expr = arg.strip()
        ok, val = self._eval_arg(target_expr)
        if not ok:
            return
        panel = _build_psource_panel(target_expr, val)
        if panel is None:
            self.error(f"Source code unavailable for {target_expr!r}.")
            return
        self._console().print(panel)

    @override
    def displayhook(self, obj: object) -> None:
        """Render interactive REPL expression results with Rich pretty-printing.

        Args:
            obj (object): Evaluated expression value.

        """
        if obj is not None:
            self._store_last_result(obj)
            rich_pprint(obj, console=self._console(), expand_all=True)

    def _eval_arg(self, arg: str) -> tuple[bool, object]:
        """Evaluate an expression string in the current frame context.

        Args:
            arg (str): Expression to evaluate.

        Returns:
            tuple[bool, object]: `(True, value)` on success, or `(False, None)`
                on error.

        """
        try:
            return (True, self._getval(arg))
        except Exception:  # ruff: ignore[blind-except] -- _getval re-raises arbitrary user expression exceptions after reporting them
            return (False, None)

    @override
    def do_p(self, arg: str) -> None:
        """Rich-print the value of an expression (`p <expr>`).

        Args:
            arg (str): Expression string to evaluate and print.

        """
        ok, val = self._eval_arg(arg)
        if ok:
            self._store_last_result(val)
            rich_pprint(val, console=self._console(), expand_all=False)

    @override
    def do_pp(self, arg: str) -> None:
        """Rich pretty-print the expanded value of an expression (`pp <expr>`).

        Args:
            arg (str): Expression string to evaluate and pretty-print.

        """
        ok, val = self._eval_arg(arg)
        if ok:
            self._store_last_result(val)
            rich_pprint(val, console=self._console(), expand_all=True)

    @override
    def do_pinfo(self, arg: str) -> None:
        """Provide detailed information about an object in a Rich panel (`pinfo`).

        Args:
            arg (str): Expression or object name to inspect.

        """
        target_expr = arg.strip()
        if not target_expr:
            rich_inspect(
                self._get_frame_locals(self.curframe),
                console=self._console(),
                title="Frame Locals",
            )
            return
        ok, val = self._eval_arg(target_expr)
        if ok:
            rich_inspect(
                val,
                console=self._console(),
                methods=True,
                title=target_expr,
            )

    @override
    def do_pinfo2(self, arg: str) -> None:
        """Provide extra detailed information about an object (`pinfo2`).

        Args:
            arg (str): Expression or object name to inspect in full detail.

        """
        target_expr = arg.strip()
        if not target_expr:
            rich_inspect(
                self._get_frame_locals(self.curframe),
                console=self._console(),
                all=True,
                title="Frame Locals",
            )
            return
        ok, val = self._eval_arg(target_expr)
        if ok:
            rich_inspect(
                val,
                console=self._console(),
                methods=True,
                all=True,
                title=target_expr,
            )

    @override
    def do_args(self, arg: str) -> None:
        """Display the argument list of the current function in a Rich table (`a`).

        Args:
            arg (str): Unused command argument string.

        """
        del arg
        frame = getattr(self, "curframe", None)
        if frame is None:
            self.error("No active frame.")
            return
        frame_locals = self._get_frame_locals(frame)
        arg_names = _extract_arg_names(frame.f_code)
        console = self._console()
        if not arg_names:
            console.print("[dim]No function arguments in current frame.[/dim]")
            return
        items = [
            (name, frame_locals.get(name), name in frame_locals) for name in arg_names
        ]
        console.print(_build_variables_table("Function Arguments", items))

    do_a = do_args

    @override
    def do_interact(self, arg: str) -> None:
        """Start an interactive IPython shell in the current frame (`interact`).

        Args:
            arg (str): Unused command argument string.

        """
        del arg
        frame = getattr(self, "curframe", None)
        if frame is None:
            self.error("No active frame.")
            return
        ns: dict[str, Any] = {
            **frame.f_globals,
            **self._get_frame_locals(frame),
        }
        self._console().print(
            "[bold cyan]Interactive IPython shell "
            "[dim](Ctrl-D or exit() to return to dpdb)[/dim][/bold cyan]"
        )
        embed_shell = InteractiveShellEmbed(banner1="", exit_msg="")  # ruff: ignore[debugger] -- do_interact intentionally instantiates an embedded IPython shell
        embed_shell(local_ns=ns, global_ns=frame.f_globals)
        frame_locals = cast(
            "MutableMapping[str, object]", self._get_frame_locals(frame)
        )
        for k, v in ns.items():
            if k not in frame.f_globals and not k.startswith("_ih"):
                frame_locals[k] = v

    @override
    def do_help(self, arg: str = "") -> bool | None:
        """Display the categorized command reference table or help for a command (`h`).

        Args:
            arg (str): Optional command or topic name.

        Returns:
            bool | None: Superclass return value when delegating to topic handlers.

        """
        target = arg.strip()
        console = self._console()
        if not target:
            console.print(_build_help_table())
            return None
        if hasattr(self, f"help_{target}"):
            return super().do_help(target)
        cmd_fn = getattr(self, f"do_{target}", None)
        if cmd_fn is None:
            self.error(f"No help for {target!r}")
            return None
        doc = getattr(cmd_fn, "__doc__", None)
        if not isinstance(doc, str) or not doc.strip():
            self.error(f"No help for {target!r}; docstring missing")
            return None
        console.print(_build_command_help_panel(target, doc))
        return None

    do_h = do_help


def _get_debugger_cls() -> type[Pdb]:
    """Return the `DojoPdb` debugger class after ensuring an active IPython shell.

    Returns:
        type[Pdb]: The `DojoPdb` class (or fallback `Pdb` if shell creation fails).

    """
    shell = get_ipython()
    if shell is None:
        ipapp = TerminalIPythonApp()
        ipapp.interact = False
        ipapp.initialize(["--no-term-title", "--InteractiveShell.warn_venv=False"])
        shell = ipapp.shell

    if shell is None:
        return Pdb
    return DojoPdb


def _init_pdb() -> Pdb:
    """Initialize and return an IPython Pdb instance.

    Returns:
        Pdb: Configured IPython Pdb debugger instance.

    """
    debugger_cls = _get_debugger_cls()
    return debugger_cls(context=DEFAULT_CONTEXT_LINES)


def _bdb_quit_excepthook(
    exc_type: type[BaseException],
    exc_val: BaseException,
    exc_tb: TracebackType | None,
) -> None:
    """Suppress `bdb.BdbQuit` at top level and forward all other exceptions.

    Args:
        exc_type (type[BaseException]): Exception class.
        exc_val (BaseException): Exception instance.
        exc_tb (TracebackType | None): Exception traceback.

    """
    if issubclass(exc_type, bdb.BdbQuit):
        return
    orig = getattr(_bdb_quit_excepthook, "excepthook_ori", sys.__excepthook__)
    orig(exc_type, exc_val, exc_tb)


def wrap_sys_excepthook() -> None:
    """Wrap `sys.excepthook` with `_bdb_quit_excepthook` once."""
    if sys.excepthook is not _bdb_quit_excepthook:
        _bdb_quit_excepthook.excepthook_ori = sys.excepthook  # pyrefly: ignore[missing-attribute]
        sys.excepthook = _bdb_quit_excepthook


def set_trace(frame: FrameType | None = None) -> None:
    """Enter the internal DPDB debugger at the given or calling stack frame.

    Args:
        frame (FrameType | None): Target stack frame. Defaults to the caller's frame.

    """
    wrap_sys_excepthook()
    target_frame = (
        sys._getframe().f_back  # ruff: ignore[private-member-access] -- sys._getframe is required to resolve the caller stack frame
        if frame is None
        else frame
    )
    pdb_instance = _init_pdb()
    shell = getattr(pdb_instance, "shell", None)
    if shell is not None and hasattr(shell, "restore_sys_module_state"):
        shell.restore_sys_module_state()
    pdb_instance.set_trace(target_frame)


def setup() -> None:
    """Set internal DPDB as the active debugger."""
    wrap_sys_excepthook()
    os.environ[BREAKPOINT_ENV_VAR] = DPDB_SET_TRACE_HOOK
    sys.breakpointhook = cast("Any", set_trace)


def post_mortem(tb: TracebackType | None = None) -> None:
    """Enter post-mortem debugging on the given or active exception traceback.

    Args:
        tb (TracebackType | None): Traceback to inspect (defaults to active exc_info).

    """
    wrap_sys_excepthook()
    pdb_instance = _init_pdb()
    pdb_instance.reset()
    target_tb = sys.exc_info()[2] if tb is None else tb
    if target_tb is not None:
        console = (
            pdb_instance._console()  # ruff: ignore[private-member-access] -- _console is internal to DojoPdb in this module
            if isinstance(pdb_instance, DojoPdb)
            else Console(file=getattr(pdb_instance, "stdout", sys.stdout))
        )
        _render_post_mortem_banner(target_tb, console)
        pdb_instance.interaction(None, target_tb)


def pm() -> None:
    """Enter `dpdb` post-mortem debugging on the last unhandled exception."""
    last_exc = getattr(sys, "last_exc", None)
    tb = (
        last_exc.__traceback__
        if isinstance(last_exc, BaseException)
        else getattr(sys, "last_traceback", None)
    )
    post_mortem(tb)


def _find_symbol_lineno(filepath: str, symbol: str) -> int | None:
    """Find the definition line number of a function or class in `filepath`.

    Args:
        filepath (str): Path to the Python source file.
        symbol (str): Function or class name to locate.

    Returns:
        int | None: Definition line number if found, else `None`.

    """
    try:
        source = Path(filepath).read_text(encoding="utf-8")
        tree = ast.parse(source, filename=filepath)
    except Exception:  # ruff: ignore[blind-except] -- gracefully return None if file cannot be read or parsed
        return None
    for node in ast.walk(tree):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
            and node.name == symbol
        ):
            return node.lineno
    return None


def _apply_break_spec(pdb_instance: Pdb, default_file: str, spec: str) -> None:
    """Register a single CLI breakpoint specification on `pdb_instance`.

    Args:
        pdb_instance (Pdb): Debugger instance on which to set the breakpoint.
        default_file (str): Resolved path to the target script.
        spec (str): Breakpoint specification (`line`, `file:line`, or `symbol`).

    """
    cleaned = spec.strip()
    if ":" in cleaned:
        file_part, _, line_part = cleaned.rpartition(":")
        resolved_file = pdb_instance.lookupmodule(file_part) or str(
            Path(file_part).resolve()
        )
        if line_part.isdigit():
            lineno = pdb_instance.checkline(resolved_file, int(line_part)) or int(
                line_part
            )
            _ = pdb_instance.set_break(resolved_file, lineno)
        return
    if cleaned.isdigit():
        lineno = pdb_instance.checkline(default_file, int(cleaned)) or int(cleaned)
        _ = pdb_instance.set_break(default_file, lineno)
        return
    sym_line = _find_symbol_lineno(default_file, cleaned)
    if sym_line is not None:
        lineno = pdb_instance.checkline(default_file, sym_line) or sym_line
        _ = pdb_instance.set_break(default_file, lineno, funcname=cleaned)


def has_active_breakpoints() -> bool:
    """Return whether any `bdb.Breakpoint` is currently registered.

    Returns:
        bool: `True` when at least one active breakpoint exists in `bdb`.

    """
    return any(bp is not None for bp in bdb.Breakpoint.bpbynumber)


def seed_cli_breakpoints(target_file: str, breaks: Sequence[str]) -> None:
    """Register CLI-supplied breakpoints before target execution.

    Args:
        target_file (str): Path to the resolved target script.
        breaks (Sequence[str]): Breakpoint specifications (`line`, `file:line`, `func`).

    """
    pdb_instance = _init_pdb()
    resolved_default = str(Path(target_file).resolve())
    for spec in breaks:
        _apply_break_spec(pdb_instance, resolved_default, spec)


def run_with_active_breakpoints(call: Callable[[], object]) -> None:
    """Execute `call` under `dpdb` trace dispatch so active breakpoints fire.

    Args:
        call (Callable[[], object]): Zero-argument callable executing the target.

    """
    wrap_sys_excepthook()
    pdb_instance = _init_pdb()
    shell = getattr(pdb_instance, "shell", None)
    if shell is not None and hasattr(shell, "restore_sys_module_state"):
        shell.restore_sys_module_state()
    pdb_instance.reset()
    caller_frame = sys._getframe()  # ruff: ignore[private-member-access] -- anchor botframe to runner frame
    pdb_instance.botframe = caller_frame
    pdb_instance.set_continue()
    prev_trace = sys.gettrace()
    sys.settrace(pdb_instance.trace_dispatch)
    try:
        _ = call()
    finally:
        pdb_instance.quitting = True
        sys.settrace(prev_trace)
