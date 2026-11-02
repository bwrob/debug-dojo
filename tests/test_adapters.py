"""Tests for debugger backend adapters in `debug_dojo.adapters`."""

from __future__ import annotations

import io
import os
import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from IPython.core.debugger import BdbQuit_excepthook, Pdb
from rich.console import Console

from debug_dojo.adapters import (
    BREAKPOINT_ENV_VAR,
    DebuggerType,
    debugpy,
    dpdb,
    enter_post_mortem,
    get_adapter,
    ipdb,
    pdb,
    pudb,
    setup_debugger,
)
from debug_dojo.adapters.dpdb import (
    DEFAULT_CONTEXT_LINES,
    STEP_CONTEXT_LINES,
    DojoPdb,
    _build_breakpoints_table,
    _build_psource_panel,
    _build_stack_table,
    _build_variables_table,
    _build_whatis_panel,
    _compute_locals_diff,
    _extract_arg_names,
    _extract_line_variables,
    _format_callable_signature,
    _format_return_banner,
    _format_shape_or_len,
    _format_watch_entries,
    _get_debugger_cls,
    _init_pdb,
    _is_runner_frame,
    _is_user_local,
    _join_inline_items,
    _render_post_mortem_banner,
    _snapshot_user_locals,
    _tokenize_identifiers,
)

if TYPE_CHECKING:
    from pathlib import Path
    from types import FrameType

    import pytest

EXPECTED_PAIR_COUNT = 2


class _ShapeDummy:
    """Dummy object with a non-callable `.shape` attribute."""

    shape = (3, 4)


class _UnSizedDummy:
    """Dummy object without `.shape` or `__len__`."""


def _make_dojo_pdb(
    stdout: io.StringIO | None = None,
    *,
    pt_session_options: dict[str, object] | None = None,
) -> DojoPdb:
    """Create a DojoPdb instance with mocked prompt_toolkit initialization.

    Returns:
        DojoPdb: Configured debugger instance writing to `stdout`.

    """
    stream = io.StringIO() if stdout is None else stdout
    with (
        patch.object(DojoPdb, "pt_init"),
        patch(
            "IPython.core.debugger.get_ipython",
            return_value=MagicMock(colors="neutral"),
        ),
    ):
        dbg = DojoPdb(
            stdout=stream,
            context=5,
            pt_session_options=pt_session_options,
        )
    dbg.reset()
    return dbg


def test_debugger_type_set_trace_hooks() -> None:
    """Test set_trace_hook property on DebuggerType."""
    assert DebuggerType.DPDB.set_trace_hook == "debug_dojo.adapters.dpdb.set_trace"
    assert DebuggerType.PDB.set_trace_hook == "pdb.set_trace"
    assert DebuggerType.IPDB.set_trace_hook == "ipdb.set_trace"
    assert DebuggerType.PUDB.set_trace_hook == "pudb.set_trace"
    assert DebuggerType.DEBUGPY.set_trace_hook == "debugpy.breakpoint"


def test_get_adapter_resolution() -> None:
    """Test get_adapter maps DebuggerType values and None to adapter modules."""
    assert get_adapter(None) is dpdb
    assert get_adapter(DebuggerType.DPDB) is dpdb
    assert get_adapter(DebuggerType.PDB) is pdb
    assert get_adapter(DebuggerType.IPDB) is ipdb
    assert get_adapter(DebuggerType.PUDB) is pudb
    assert get_adapter(DebuggerType.DEBUGPY) is debugpy


def test_format_shape_or_len() -> None:
    """Test _format_shape_or_len handles shape, Sized, and unsized objects."""
    assert _format_shape_or_len(_ShapeDummy()) == "shape=(3, 4)"
    assert _format_shape_or_len([1, 2, 3]) == "len=3"
    assert _format_shape_or_len(_UnSizedDummy()) == "-"


def test_is_user_local_and_snapshot() -> None:
    """Test _is_user_local filters dunders, underscore, pytest temps, and modules."""
    assert _is_user_local("count", 42) is True
    assert _is_user_local("_", 99) is False
    assert _is_user_local("__name__", "main") is False
    assert _is_user_local("@py_assert1", 1) is False
    assert _is_user_local("sys", sys) is False

    snap = _snapshot_user_locals({"x": 10, "_": 99, "__doc__": "ignore", "sys": sys})
    assert snap == {"x": "10"}


def test_is_runner_frame_and_hidden_predicate() -> None:
    """Test _is_runner_frame and DojoPdb._hidden_predicate hide framework frames."""
    frozen_frame = MagicMock()
    frozen_frame.f_code.co_filename = "<frozen runpy>"
    frozen_frame.f_globals = {"__name__": "runpy"}
    assert _is_runner_frame(frozen_frame) is True

    runner_frame = MagicMock()
    runner_frame.f_code.co_filename = "/path/to/_execution.py"
    runner_frame.f_globals = {"__name__": "debug_dojo._execution"}
    assert _is_runner_frame(runner_frame) is True

    user_frame = MagicMock()
    user_frame.f_code.co_filename = "/path/to/app.py"
    user_frame.f_globals = {"__name__": "__main__"}
    assert _is_runner_frame(user_frame) is False

    dbg = _make_dojo_pdb()
    dbg.curframe = runner_frame
    # Active curframe is never hidden
    assert dbg._hidden_predicate(runner_frame) is False  # ruff: ignore[private-member-access] -- verify overridden _hidden_predicate

    dbg.curframe = user_frame
    assert dbg._hidden_predicate(runner_frame) is True  # ruff: ignore[private-member-access] -- verify runner frame hidden when tbhide is active
    assert dbg.stop_here(runner_frame) is False
    with patch.object(Pdb, "user_return") as mock_super_return:
        dbg.user_return(runner_frame, None)
    mock_super_return.assert_not_called()

    dbg.curframe = MagicMock()
    with patch.object(Pdb, "_hidden_predicate", return_value=True):
        assert dbg.stop_here(user_frame) is False

    with patch.object(Pdb, "_hidden_predicate", return_value=False) as mock_super:
        assert dbg._hidden_predicate(user_frame) is False  # ruff: ignore[private-member-access] -- verify delegation to superclass for user frames
    mock_super.assert_called_once_with(user_frame)

    with (
        patch.object(dbg, "_hidden_predicate", return_value=False),
        patch.object(Pdb, "stop_here", return_value=True) as mock_super_stop,
        patch.object(Pdb, "user_return") as mock_super_ret_user,
    ):
        assert dbg.stop_here(user_frame) is True
        dbg.user_return(user_frame, 42)
    mock_super_stop.assert_called_once_with(user_frame)
    mock_super_ret_user.assert_called_once_with(user_frame, 42)


def test_dojo_pdb_emptyline_repeats_only_navigation() -> None:
    """Test DojoPdb.emptyline repeats navigation commands and ignores others."""
    dbg = _make_dojo_pdb()

    dbg.lastcmd = "p x + 1"
    assert dbg.emptyline() is False

    dbg.lastcmd = ""
    assert dbg.emptyline() is False

    dbg.lastcmd = "next"
    with patch.object(Pdb, "emptyline", return_value=False) as mock_super_empty:
        assert dbg.emptyline() is False
    mock_super_empty.assert_called_once_with()


def test_dojo_pdb_store_last_result() -> None:
    """Test DojoPdb._store_last_result binds _ unless _ is a user parameter."""
    dbg = _make_dojo_pdb()

    # No-op when curframe is None or value is None
    dbg.curframe = None
    dbg._store_last_result(42)  # ruff: ignore[private-member-access] -- verify _store_last_result helper

    frame = MagicMock()
    frame.f_code.co_varnames = ("x", "y")
    locals_dict: dict[str, object] = {"x": 1, "y": 2}
    dbg.curframe = frame
    with patch.object(dbg, "_get_frame_locals", return_value=locals_dict):
        dbg._store_last_result(None)  # ruff: ignore[private-member-access] -- verify None is ignored
        assert "_" not in locals_dict

        dbg._store_last_result(123)  # ruff: ignore[private-member-access] -- verify first evaluation binds _
        assert locals_dict["_"] == 123  # ruff: ignore[magic-value-comparison] -- verify bound result value

        # Even if co_varnames later appears to contain '_', managed frames update '_'
        frame.f_code.co_varnames = ("x", "y", "_")
        dbg._store_last_result(456)  # ruff: ignore[private-member-access] -- verify subsequent evaluation updates _
        assert locals_dict["_"] == 456  # ruff: ignore[magic-value-comparison] -- verify updated result value

    # Frame that already has '_' as a user parameter is never overwritten
    user_underscore_frame = MagicMock()
    user_underscore_frame.f_code.co_varnames = ("_",)
    user_locals: dict[str, object] = {"_": "preserve_me"}
    dbg.curframe = user_underscore_frame
    with patch.object(dbg, "_get_frame_locals", return_value=user_locals):
        dbg._store_last_result(999)  # ruff: ignore[private-member-access] -- verify user '_' parameter is preserved
        assert user_locals["_"] == "preserve_me"


def test_compute_locals_diff() -> None:
    """Test _compute_locals_diff detects added, changed, and removed variables."""
    assert _compute_locals_diff(None, {"x": "1"}) == []
    diffs = _compute_locals_diff(
        {"x": "1", "unchanged": "2", "removed": "3"},
        {"x": "10", "unchanged": "2", "y": "'new'"},
    )
    assert len(diffs) == 3  # ruff: ignore[magic-value-comparison] -- verify changed, added, and removed entries
    assert "Δ x" in diffs[0]
    assert "1 → 10" in diffs[0]
    assert "+ y" in diffs[1]
    assert "- removed" in diffs[2]

    assert _join_inline_items(["a=1", "b=2"], max_items=4) == "a=1, b=2"
    assert (
        _join_inline_items(["a=1", "b=2", "c=3"], max_items=2)
        == "a=1, b=2 [dim](+1 more)[/dim]"
    )


def test_tokenize_and_extract_line_variables() -> None:
    """Test _tokenize_identifiers and _extract_line_variables."""
    assert _tokenize_identifiers("if x + y == x and True:") == ["x", "y"]
    assert _tokenize_identifiers("unclosed_str = 'abc") == ["unclosed_str"]

    line_vars = _extract_line_variables(
        "result = local_var + global_var + unknown_var + fn()",
        {"local_var": 5, "fn": lambda: 1},
        {"global_var": 20, "__builtins__": {}},
    )
    assert len(line_vars) == EXPECTED_PAIR_COUNT
    assert "local_var" in line_vars[0]
    assert "global_var" in line_vars[1]


def test_extract_arg_names_and_build_table() -> None:
    """Test _extract_arg_names with positional, kw-only, *args, and **kwargs."""

    def sample_fn(a: int, *args: int, kw: str = "x", **kwargs: int) -> None:
        """Sample function with varied parameter kinds."""

    assert _extract_arg_names(sample_fn.__code__) == ["a", "kw", "args", "kwargs"]

    table = _build_variables_table(
        "Variables",
        [("a", 42, True), ("missing", None, False)],
    )
    assert table.row_count == EXPECTED_PAIR_COUNT


def test_render_post_mortem_banner(tmp_path: Path) -> None:
    """Test _render_post_mortem_banner renders inner traceback frame and exception."""
    script = tmp_path / "boom.py"
    script.write_text("x = 1 / 0\n", encoding="utf-8")

    buf = io.StringIO()
    console = Console(file=buf, force_terminal=False, width=100)

    def outer() -> None:
        inner()

    def inner() -> None:
        msg = "kaboom"
        raise RuntimeError(msg)

    try:
        outer()
    except RuntimeError:
        _, _, tb = sys.exc_info()
        assert tb is not None
        _render_post_mortem_banner(tb, console)

    output = buf.getvalue()
    assert "Dojo Post-Mortem" in output
    assert "RuntimeError: kaboom" in output
    assert "inner()" in output

    buf_no_exc = io.StringIO()
    console_no_exc = Console(file=buf_no_exc, force_terminal=False, width=100)
    fake_tb = MagicMock()
    fake_tb.tb_next = None
    fake_tb.tb_frame.f_code.co_filename = "<nonexistent>"
    fake_tb.tb_frame.f_code.co_name = ""
    fake_tb.tb_lineno = 1
    _render_post_mortem_banner(fake_tb, console_no_exc)
    assert "Unhandled Exception" in buf_no_exc.getvalue()


def test_dojo_pdb_prompt_and_toolbar() -> None:
    """Test DojoPdb prompt and bottom toolbar."""
    pdb_live = _make_dojo_pdb(pt_session_options={"mouse_support": False})
    assert pdb_live.prompt == "dpdb> "
    assert pdb_live._format_frame_location() == ("<unknown>", "<unknown>", 0)  # ruff: ignore[private-member-access] -- verify internal location fallback

    frame = sys._getframe()  # ruff: ignore[private-member-access] -- obtain real frame for test
    pdb_live.curframe = frame
    pdb_live.breaks = {"test.py": [10, 20]}
    toolbar = pdb_live._render_bottom_toolbar()  # ruff: ignore[private-member-access] -- verify toolbar formatting
    assert toolbar.startswith(" dpdb | ")
    assert "test_dojo_pdb_prompt_and_toolbar()" in toolbar
    assert "2 bp" in toolbar


def test_dojo_pdb_print_stack_entry_and_context_banner(tmp_path: Path) -> None:
    """Test DojoPdb.print_stack_entry renders active-line vars and changed locals."""
    src_file = tmp_path / "calc.py"
    src_file.write_text("total = count + 1\npass\n", encoding="utf-8")

    buf = io.StringIO()
    dbg = _make_dojo_pdb(stdout=buf)
    dbg.do_context("12")
    assert dbg.context == 12  # ruff: ignore[magic-value-comparison] -- verify explicit context setting

    empty_globals: dict[str, object] = {}
    fake_frame = MagicMock()
    fake_frame.f_code.co_filename = str(src_file)
    fake_frame.f_code.co_name = "compute"
    fake_frame.f_lineno = 1
    fake_frame.f_globals = empty_globals

    recorded_contexts: list[int] = []

    def record_context(*_args: object) -> None:
        recorded_contexts.append(dbg.context)

    dbg.curframe = fake_frame
    with (
        patch.object(Pdb, "print_stack_entry", side_effect=record_context),
        patch.object(dbg, "_get_frame_locals", return_value={"count": 10}),
    ):
        dbg.print_stack_entry((fake_frame, 1))

    assert recorded_contexts == [12]
    first_out = buf.getvalue()
    assert "Line:" in first_out
    assert "count=10" in first_out

    buf.truncate(0)
    buf.seek(0)
    with (
        patch.object(Pdb, "print_stack_entry", side_effect=record_context),
        patch.object(dbg, "_get_frame_locals", return_value={"count": 11}),
    ):
        dbg.print_stack_entry((fake_frame, 2))

    assert recorded_contexts == [12, STEP_CONTEXT_LINES]

    second_out = buf.getvalue()
    assert "Changed:" in second_out
    assert "10 → 11" in second_out

    # Non-current frame should not re-render banner, and empty locals/line does nothing
    other_frame = MagicMock()
    other_frame.f_code.co_filename = "<empty>"
    other_frame.f_code.co_name = "other"
    other_frame.f_lineno = 1
    other_frame.f_globals = empty_globals
    with (
        patch.object(Pdb, "print_stack_entry"),
        patch.object(dbg, "_get_frame_locals", return_value={}),
    ):
        dbg.print_stack_entry((other_frame, 1))
        dbg.curframe = other_frame
        dbg.print_stack_entry((other_frame, 1))


def test_dojo_pdb_print_and_inspect_commands() -> None:
    """Test DojoPdb commands: displayhook, p, pp, pinfo, and pinfo2."""
    buf = io.StringIO()
    dbg = _make_dojo_pdb(stdout=buf)

    dbg.displayhook(None)
    assert not buf.getvalue()
    dbg.displayhook({"key": "val"})
    assert "'key': 'val'" in buf.getvalue()

    alpha = [1, 2]
    assert alpha
    dbg.setup(sys._getframe(), None)  # ruff: ignore[private-member-access] -- obtain frame for evaluation tests

    buf.truncate(0)
    buf.seek(0)
    dbg.do_p("alpha")
    dbg.do_pp("alpha")
    dbg.do_pinfo("alpha")
    dbg.do_pinfo("")
    dbg.do_pinfo2("alpha")
    dbg.do_pinfo2("")
    out = buf.getvalue()
    assert "[1, 2]" in out
    assert "Frame Locals" in out

    # Invalid expressions in p, pp, pinfo, pinfo2 should be handled gracefully
    with patch.object(dbg, "_error_exc"):
        dbg.do_p("undefined_symbol_xyz")
        dbg.do_pp("undefined_symbol_xyz")
        dbg.do_pinfo("undefined_symbol_xyz")
        dbg.do_pinfo2("undefined_symbol_xyz")


def test_dojo_pdb_args_command() -> None:
    """Test DojoPdb table command: args (and alias a)."""
    buf = io.StringIO()
    dbg = _make_dojo_pdb(stdout=buf)
    dbg.setup(sys._getframe(), None)  # ruff: ignore[private-member-access] -- obtain frame for args tests

    # Test do_args on function without parameters vs function with parameters
    dbg.do_args("")
    assert "No function arguments" in buf.getvalue()

    def fn_with_args(first: int, second: str) -> None:
        """Sample function with positional parameters."""

    arg_frame = MagicMock()
    arg_frame.f_code = fn_with_args.__code__
    dbg.curframe = arg_frame
    buf.truncate(0)
    buf.seek(0)
    with patch.object(dbg, "_get_frame_locals", return_value={"first": 99}):
        dbg.do_args("")
    args_out = buf.getvalue()
    assert "first" in args_out
    assert "undefined" in args_out

    # None curframe error path
    dbg.curframe = None
    with patch.object(dbg, "error") as mock_err:
        dbg.do_args("")
    mock_err.assert_called_once()


def test_return_and_watch_banner_helpers() -> None:
    """Test _format_return_banner and _format_watch_entries."""
    assert _format_return_banner({"x": 1}) is None
    ret_str = _format_return_banner({"__return__": 42})
    assert ret_str is not None
    assert "42" in ret_str
    assert "int" in ret_str

    assert _format_watch_entries(None, lambda _expr: 1) == []
    assert _format_watch_entries({}, lambda _expr: 1) == []
    watches: dict[str, object] = {"a": 10, "b": 20}
    values = {"a": 10, "b": 99}
    watch_strs = _format_watch_entries(watches, lambda expr: values[expr])
    assert len(watch_strs) == EXPECTED_PAIR_COUNT
    assert "a" in watch_strs[0]
    assert "Δ b" in watch_strs[1]
    assert watches["b"] == 99  # ruff: ignore[magic-value-comparison] -- verify updated watch value


def test_dojo_pdb_return_and_watch_in_context_banner(tmp_path: Path) -> None:
    """Test _render_frame_context_banner includes Return and Watch lines."""
    src_file = tmp_path / "ret.py"
    src_file.write_text("return x\n", encoding="utf-8")

    buf = io.StringIO()
    dbg = _make_dojo_pdb(stdout=buf)
    dbg._show_display()  # ruff: ignore[private-member-access] -- verify no-op override

    empty_globals: dict[str, object] = {}
    fake_frame = MagicMock()
    fake_frame.f_code.co_filename = str(src_file)
    fake_frame.f_code.co_name = "compute"
    fake_frame.f_lineno = 1
    fake_frame.f_globals = empty_globals

    dbg.curframe = fake_frame
    dbg.displaying = {fake_frame: {"x": 5}}
    with (
        patch.object(Pdb, "print_stack_entry"),
        patch.object(
            dbg,
            "_get_frame_locals",
            return_value={"x": 5, "__return__": 5},
        ),
        patch.object(dbg, "_getval_except", return_value=5),
    ):
        dbg.print_stack_entry((fake_frame, 1))

    out = buf.getvalue()
    assert "Return:" in out
    assert "Watch:" in out


def test_stack_table_and_print_stack_trace() -> None:
    """Test _build_stack_table with hidden frames and DojoPdb.print_stack_trace."""
    frame_a = MagicMock()
    frame_a.f_code.co_filename = "a.py"
    frame_a.f_code.co_name = "func_a"
    frame_b = MagicMock()
    frame_b.f_code.co_filename = "b.py"
    frame_b.f_code.co_name = ""

    stack = [(frame_a, 1), (frame_b, 2), (frame_a, 3)]
    table = _build_stack_table(
        stack,
        [True, False, True],
        frame_b,
        skip_hidden=True,
    )
    assert table.row_count == 3  # ruff: ignore[magic-value-comparison] -- 1 leading skip + 1 visible + 1 trailing skip

    buf = io.StringIO()
    dbg = _make_dojo_pdb(stdout=buf)
    dbg.stack = [(frame_a, 1)]
    dbg.curframe = frame_a
    with patch.object(dbg, "hidden_frames", return_value=[False]):
        dbg.print_stack_trace()
    assert "Call Stack" in buf.getvalue()


def test_breakpoints_and_display_commands() -> None:
    """Test _build_breakpoints_table, do_break, and do_display."""
    bp_enabled = MagicMock()
    bp_enabled.number = 1
    bp_enabled.enabled = True
    bp_enabled.temporary = True
    bp_enabled.file = "app.py"
    bp_enabled.line = 10
    bp_enabled.hits = 2
    bp_enabled.cond = "x > 0"

    bp_disabled = MagicMock()
    bp_disabled.number = 2
    bp_disabled.enabled = False
    bp_disabled.temporary = False
    bp_disabled.file = "app.py"
    bp_disabled.line = 20
    bp_disabled.hits = 0
    bp_disabled.cond = None

    table = _build_breakpoints_table([bp_enabled, bp_disabled])
    assert table.row_count == EXPECTED_PAIR_COUNT

    buf = io.StringIO()
    dbg = _make_dojo_pdb(stdout=buf)
    with patch("bdb.Breakpoint.bpbynumber", [None]):
        dbg.do_break("")
    assert "No breakpoints set" in buf.getvalue()

    buf.truncate(0)
    buf.seek(0)
    with patch("bdb.Breakpoint.bpbynumber", [None, bp_enabled]):
        dbg.do_break("")
    assert "Breakpoints" in buf.getvalue()

    with patch.object(Pdb, "do_break") as mock_super_break:
        dbg.do_break("15")
    mock_super_break.assert_called_once_with("15", 0)

    # Test do_display without and with watches
    frame: FrameType = sys._getframe()  # ruff: ignore[private-member-access] -- obtain frame for display test
    dbg.curframe = frame
    dbg.displaying = {}
    buf.truncate(0)
    buf.seek(0)
    dbg.do_display("")
    assert "No expressions are being displayed" in buf.getvalue()

    dbg.displaying = {frame: {"x": 10}}
    buf.truncate(0)
    buf.seek(0)
    with patch.object(dbg, "_getval_except", return_value=10):
        dbg.do_display("")
    assert "Watched Expressions" in buf.getvalue()

    with patch.object(Pdb, "do_display") as mock_super_display:
        dbg.do_display("x + 1")
    mock_super_display.assert_called_once_with("x + 1")


def test_whatis_and_psource_commands() -> None:
    """Test _format_callable_signature, do_whatis, and do_psource."""

    def sample_callable(x: int) -> None:
        """Sample callable for signature and source inspection."""

    assert _format_callable_signature(42) is None
    assert _format_callable_signature(sample_callable) == "(x: 'int') -> 'None'"
    with patch("inspect.signature", side_effect=ValueError("no sig")):
        assert _format_callable_signature(sample_callable) is None

    panel_cls = _build_whatis_panel(" _ShapeDummy", _ShapeDummy)
    assert panel_cls is not None
    assert _build_psource_panel("int", 42) is None

    buf = io.StringIO()
    dbg = _make_dojo_pdb(stdout=buf)
    num = 42
    assert num == 42  # ruff: ignore[magic-value-comparison] -- bind local variable for whatis/psource evaluation
    dbg.setup(sys._getframe(), None)  # ruff: ignore[private-member-access] -- obtain frame for whatis/psource test

    dbg.do_whatis("sample_callable")
    dbg.do_whatis("num")
    dbg.do_psource("sample_callable")
    out = buf.getvalue()
    assert "whatis sample_callable" in out
    assert "def sample_callable" in out

    with patch.object(dbg, "error") as mock_err:
        dbg.do_psource("num")
    mock_err.assert_called_once()

    with patch.object(dbg, "_error_exc"):
        dbg.do_whatis("missing_var_xyz")
        dbg.do_psource("missing_var_xyz")


def test_dojo_pdb_help_command() -> None:
    """Test DojoPdb.do_help overview table, command panel, topics, and errors."""
    buf = io.StringIO()
    dbg = _make_dojo_pdb(stdout=buf)

    # Overview table when called with no arguments
    dbg.do_help("")
    overview = buf.getvalue()
    assert "dpdb Commands" in overview
    assert "pinfo / pinfo2 [expr]" in overview

    # Specific command help panel
    buf.truncate(0)
    buf.seek(0)
    dbg.do_help("p")
    assert "help p" in buf.getvalue()

    # Topic handler delegation (e.g., help exec)
    with patch.object(Pdb, "do_help", return_value=None) as mock_super_help:
        dbg.do_help("exec")
    mock_super_help.assert_called_once_with("exec")

    # Unknown command error
    with patch.object(dbg, "error") as mock_err:
        dbg.do_help("nonexistent_cmd")
    mock_err.assert_called_once()

    # Command with missing docstring error
    with (
        patch.object(dbg, "do_p", MagicMock(__doc__="")),
        patch.object(dbg, "error") as mock_err_doc,
    ):
        dbg.do_help("p")
    mock_err_doc.assert_called_once()


def test_get_debugger_cls_no_shell() -> None:
    """Test _get_debugger_cls initializes TerminalIPythonApp when no shell is active."""
    mock_app = MagicMock()
    mock_app.shell.debugger_cls = Pdb
    with (
        patch("debug_dojo.adapters.dpdb.get_ipython", return_value=None),
        patch("debug_dojo.adapters.dpdb.TerminalIPythonApp", return_value=mock_app),
    ):
        cls = _get_debugger_cls()
    assert cls is DojoPdb
    assert mock_app.interact is False
    mock_app.initialize.assert_called_once_with(
        ["--no-term-title", "--InteractiveShell.warn_venv=False"]
    )


def test_get_debugger_cls_no_shell_fallback() -> None:
    """Test _get_debugger_cls returns Pdb when app.shell remains None."""
    mock_app = MagicMock()
    mock_app.shell = None
    with (
        patch("debug_dojo.adapters.dpdb.get_ipython", return_value=None),
        patch("debug_dojo.adapters.dpdb.TerminalIPythonApp", return_value=mock_app),
    ):
        cls = _get_debugger_cls()
    assert cls is Pdb


def test_get_debugger_cls_existing_shell() -> None:
    """Test _get_debugger_cls returns DojoPdb when an IPython shell is active."""
    mock_shell = MagicMock()
    with patch("debug_dojo.adapters.dpdb.get_ipython", return_value=mock_shell):
        cls = _get_debugger_cls()
    assert cls is DojoPdb


def test_init_pdb_uses_default_context() -> None:
    """Test _init_pdb passes DEFAULT_CONTEXT_LINES to debugger_cls."""
    mock_instance = MagicMock()
    mock_cls = MagicMock(return_value=mock_instance)
    with patch("debug_dojo.adapters.dpdb._get_debugger_cls", return_value=mock_cls):
        pdb_inst = _init_pdb()
    assert pdb_inst is mock_instance
    mock_cls.assert_called_once_with(context=DEFAULT_CONTEXT_LINES)


def test_wrap_sys_excepthook_idempotent() -> None:
    """Test wrap_sys_excepthook wraps sys.excepthook once and is idempotent."""
    orig_hook = sys.excepthook
    try:
        sentinel_hook = MagicMock()
        sys.excepthook = sentinel_hook
        dpdb.wrap_sys_excepthook()
        assert sys.excepthook is BdbQuit_excepthook
        assert getattr(BdbQuit_excepthook, "excepthook_ori", None) is sentinel_hook

        dpdb.wrap_sys_excepthook()
        assert getattr(BdbQuit_excepthook, "excepthook_ori", None) is sentinel_hook
    finally:
        sys.excepthook = orig_hook


def test_dpdb_set_trace_default_frame_and_shell_restore() -> None:
    """Test dpdb.set_trace restores shell state before arming bdb.set_trace."""
    call_order: list[str] = []

    def record_set_trace(_frame: FrameType | None) -> None:
        call_order.append("set_trace")

    mock_pdb = MagicMock()
    mock_shell = MagicMock()
    mock_shell.restore_sys_module_state.side_effect = lambda: call_order.append(
        "restore"
    )
    mock_pdb.set_trace.side_effect = record_set_trace
    mock_pdb.shell = mock_shell
    with patch("debug_dojo.adapters.dpdb._init_pdb", return_value=mock_pdb):
        dpdb.set_trace()
    assert call_order == ["restore", "set_trace"]


def test_dpdb_set_trace_explicit_frame_without_shell() -> None:
    """Test dpdb.set_trace with explicit frame when pdb has no shell attribute."""
    mock_pdb = MagicMock(spec=Pdb)
    explicit_frame = sys._getframe()  # ruff: ignore[private-member-access] -- obtain real frame for test assertion
    with patch("debug_dojo.adapters.dpdb._init_pdb", return_value=mock_pdb):
        dpdb.set_trace(frame=explicit_frame)
    mock_pdb.set_trace.assert_called_once_with(explicit_frame)


def test_dpdb_post_mortem_with_explicit_tb() -> None:
    """Test dpdb.post_mortem renders banner, resets pdb, and enters interaction."""
    buf = io.StringIO()
    dojo_pdb = _make_dojo_pdb(stdout=buf)
    fake_tb = MagicMock()
    fake_tb.tb_next = None
    fake_tb.tb_frame.f_code.co_filename = "script.py"
    fake_tb.tb_frame.f_code.co_name = "main"
    fake_tb.tb_lineno = 10
    with (
        patch("debug_dojo.adapters.dpdb._init_pdb", return_value=dojo_pdb),
        patch.object(dojo_pdb, "reset") as mock_reset,
        patch.object(dojo_pdb, "interaction") as mock_interaction,
    ):
        dpdb.post_mortem(fake_tb)
    mock_reset.assert_called_once_with()
    mock_interaction.assert_called_once_with(None, fake_tb)
    assert "Dojo Post-Mortem" in buf.getvalue()


def test_dpdb_post_mortem_without_active_exception() -> None:
    """Test dpdb.post_mortem does not call interaction when no traceback exists."""
    mock_pdb = MagicMock()
    with patch("debug_dojo.adapters.dpdb._init_pdb", return_value=mock_pdb):
        dpdb.post_mortem(None)
    mock_pdb.reset.assert_called_once_with()
    mock_pdb.interaction.assert_not_called()


@patch("debug_dojo.adapters.dpdb.set_trace")
def test_dpdb_setup(mock_set_trace: MagicMock) -> None:
    """Test dpdb.setup configures PYTHONBREAKPOINT and sys.breakpointhook."""
    dpdb.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "debug_dojo.adapters.dpdb.set_trace"
    assert sys.breakpointhook == mock_set_trace


@patch("pdb.set_trace")
def test_pdb_setup(mock_set_trace: MagicMock) -> None:
    """Test pdb.setup configures PYTHONBREAKPOINT and sys.breakpointhook."""
    pdb.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "pdb.set_trace"
    assert sys.breakpointhook == mock_set_trace


@patch("pdb.post_mortem")
def test_pdb_post_mortem(mock_pm: MagicMock) -> None:
    """Test pdb.post_mortem delegates to standard library pdb.post_mortem."""
    pdb.post_mortem(None)
    mock_pm.assert_called_once_with(None)


@patch("ipdb.set_trace")
def test_ipdb_setup(mock_set_trace: MagicMock) -> None:
    """Test ipdb.setup configures PYTHONBREAKPOINT, context size, and hook."""
    ipdb.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "ipdb.set_trace"
    assert os.environ[ipdb.IPDB_CONTEXT_SIZE] == ipdb.DEFAULT_IPDB_CONTEXT_LINES
    assert sys.breakpointhook == mock_set_trace


def test_ipdb_setup_not_installed() -> None:
    """Test ipdb.setup falls back to dpdb when IPDB is not importable."""
    with patch.dict("sys.modules", {"ipdb": None}):
        ipdb.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "debug_dojo.adapters.dpdb.set_trace"


@patch("ipdb.post_mortem")
def test_ipdb_post_mortem(mock_pm: MagicMock) -> None:
    """Test ipdb.post_mortem delegates to ipdb.post_mortem."""
    ipdb.post_mortem(None)
    mock_pm.assert_called_once_with(None)


@patch("debug_dojo.adapters.dpdb.post_mortem")
def test_ipdb_post_mortem_fallback(mock_dpdb_pm: MagicMock) -> None:
    """Test ipdb.post_mortem falls back to dpdb.post_mortem when unimportable."""
    with patch.dict("sys.modules", {"ipdb": None}):
        ipdb.post_mortem(None)
    mock_dpdb_pm.assert_called_once_with(None)


@patch("pudb.set_trace")
def test_pudb_setup(mock_set_trace: MagicMock) -> None:
    """Test pudb.setup configures PYTHONBREAKPOINT and sys.breakpointhook."""
    pudb.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "pudb.set_trace"
    assert sys.breakpointhook == mock_set_trace


def test_pudb_setup_not_installed() -> None:
    """Test pudb.setup falls back to dpdb when PuDB is not importable."""
    with patch.dict("sys.modules", {"pudb": None}):
        pudb.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "debug_dojo.adapters.dpdb.set_trace"


@patch("pudb.post_mortem")
def test_pudb_post_mortem(mock_pm: MagicMock) -> None:
    """Test pudb.post_mortem delegates to pudb.post_mortem."""
    pudb.post_mortem(None)
    mock_pm.assert_called_once_with(None)


@patch("debug_dojo.adapters.dpdb.post_mortem")
def test_pudb_post_mortem_fallback(mock_dpdb_pm: MagicMock) -> None:
    """Test pudb.post_mortem falls back to dpdb.post_mortem when unimportable."""
    with patch.dict("sys.modules", {"pudb": None}):
        pudb.post_mortem(None)
    mock_dpdb_pm.assert_called_once_with(None)


@patch("debugpy.listen")
@patch("debugpy.wait_for_client")
@patch("debugpy.breakpoint")
def test_debugpy_setup(
    mock_breakpoint: MagicMock,
    mock_wait_for_client: MagicMock,
    mock_listen: MagicMock,
) -> None:
    """Test debugpy.setup configures breakpoint hook and waits for client."""
    debugpy.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "debugpy.breakpoint"
    assert sys.breakpointhook == mock_breakpoint
    mock_listen.assert_called_once_with(
        (debugpy.DEFAULT_DEBUGPY_HOST, debugpy.DEFAULT_DEBUGPY_PORT)
    )
    mock_wait_for_client.assert_called_once()


def test_debugpy_setup_not_installed() -> None:
    """Test debugpy.setup falls back to dpdb when Debugpy is not importable."""
    with patch.dict("sys.modules", {"debugpy": None}):
        debugpy.setup()
    assert os.environ[BREAKPOINT_ENV_VAR] == "debug_dojo.adapters.dpdb.set_trace"


@patch("debug_dojo.adapters.dpdb.post_mortem")
def test_debugpy_post_mortem(mock_dpdb_pm: MagicMock) -> None:
    """Test debugpy.post_mortem delegates to internal dpdb.post_mortem."""
    debugpy.post_mortem(None)
    mock_dpdb_pm.assert_called_once_with(None)


@patch("debug_dojo.adapters.dpdb.setup")
def test_setup_debugger_none_without_env(
    mock_dpdb_setup: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test setup_debugger(None) calls dpdb.setup when PYTHONBREAKPOINT is unset."""
    monkeypatch.delenv(BREAKPOINT_ENV_VAR, raising=False)
    setup_debugger(None)
    mock_dpdb_setup.assert_called_once_with()


@patch("debug_dojo.adapters.dpdb.setup")
def test_setup_debugger_none_respects_existing_env(
    mock_dpdb_setup: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test setup_debugger(None) preserves existing PYTHONBREAKPOINT when set."""
    monkeypatch.setenv(BREAKPOINT_ENV_VAR, "custom.debugger.set_trace")
    setup_debugger(None)
    mock_dpdb_setup.assert_not_called()
    assert os.environ[BREAKPOINT_ENV_VAR] == "custom.debugger.set_trace"


@patch("debug_dojo.adapters.pdb.setup")
def test_setup_debugger_explicit(mock_pdb_setup: MagicMock) -> None:
    """Test setup_debugger dispatches to explicit adapter setup."""
    setup_debugger(DebuggerType.PDB)
    mock_pdb_setup.assert_called_once_with()


@patch("debug_dojo.adapters.dpdb.post_mortem")
def test_enter_post_mortem_default(mock_dpdb_pm: MagicMock) -> None:
    """Test enter_post_mortem defaults to dpdb.post_mortem."""
    enter_post_mortem(None, None)
    mock_dpdb_pm.assert_called_once_with(None)
