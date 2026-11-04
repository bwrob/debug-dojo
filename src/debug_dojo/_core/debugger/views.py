"""Visual formatting, Rich tables, and inspection panels for `dpdb`."""

from __future__ import annotations

import inspect
import io
import keyword
import linecache
import reprlib
import sys
import tokenize
from collections.abc import Callable, Mapping, MutableMapping, Sequence, Sized
from pathlib import Path
from types import CodeType, FrameType, ModuleType, TracebackType
from typing import TYPE_CHECKING, Any, cast

from rich import box
from rich.markup import escape
from rich.panel import Panel
from rich.pretty import Pretty
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    import bdb

    from rich.console import Console

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
