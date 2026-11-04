"""IPython-powered interactive debugger (`DojoPdb`) with Rich enhancements."""

from __future__ import annotations

import bdb
import linecache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, cast, override

from IPython.terminal.debugger import TerminalPdb
from IPython.terminal.embed import (  # ruff: ignore[debugger] -- used by DojoPdb.do_interact to launch an embedded IPython shell
    InteractiveShellEmbed,
)
from rich import inspect as rich_inspect
from rich.console import Console
from rich.pretty import pprint as rich_pprint

from debug_dojo._core.debugger.breakpoints import _unwrap_callable_code
from debug_dojo._core.debugger.views import (
    _REPEATABLE_COMMANDS,
    STEP_CONTEXT_LINES,
    _build_breakpoints_table,
    _build_command_help_panel,
    _build_help_table,
    _build_psource_panel,
    _build_stack_table,
    _build_variables_table,
    _build_whatis_panel,
    _compute_locals_diff,
    _extract_arg_names,
    _extract_line_variables,
    _format_return_banner,
    _format_watch_entries,
    _is_explicit_return_line,
    _join_inline_items,
    _snapshot_user_locals,
    is_runner_frame,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, MutableMapping
    from types import FrameType


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
        if self._predicates.get("tbhide", True) and is_runner_frame(frame):
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
            if is_runner_frame(frame):
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
