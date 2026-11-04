"""Tests for DojoPdb interactive debugger class, command handlers, and toolbar."""

from __future__ import annotations

import io
import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from IPython.core.debugger import Pdb

from debug_dojo._core.debugger.debugger import DojoPdb
from debug_dojo._core.debugger.views import STEP_CONTEXT_LINES

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path
    from types import FrameType


def _make_dojo_pdb(
    stdout: io.StringIO | None = None,
    *,
    pt_session_options: Mapping[str, object] | None = None,
) -> DojoPdb:
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


def test_dojo_pdb_hidden_predicate_and_stepping() -> None:
    """Test DojoPdb._hidden_predicate and stop_here behavior on framework frames."""
    runner_frame = MagicMock()
    runner_frame.f_code.co_filename = "/path/to/execution.py"
    runner_frame.f_globals = {"__name__": "debug_dojo._core.execution"}

    user_frame = MagicMock()
    user_frame.f_code.co_filename = "/path/to/app.py"
    user_frame.f_globals = {"__name__": "__main__"}

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

    dbg.curframe = None
    with patch.object(dbg, "error") as mock_err:
        dbg.do_args("")
    mock_err.assert_called_once()


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


def test_dojo_pdb_display_and_break_commands() -> None:
    """Test DojoPdb do_break and do_display commands."""
    bp_enabled = MagicMock()
    bp_enabled.number = 1
    bp_enabled.enabled = True
    bp_enabled.temporary = True
    bp_enabled.file = "app.py"
    bp_enabled.line = 10
    bp_enabled.hits = 2
    bp_enabled.cond = "x > 0"

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

    frame: FrameType = sys._getframe()  # ruff: ignore[private-member-access] -- obtain frame for display test
    dbg.curframe = frame
    empty_displaying: dict[FrameType, dict[str, object]] = {}
    dbg.displaying = empty_displaying
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


def test_dojo_pdb_whatis_and_psource_commands() -> None:
    """Test DojoPdb do_whatis and do_psource commands."""

    def sample_callable(x: int) -> None:
        """Sample callable for inspection."""

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

    dbg.do_help("")
    overview = buf.getvalue()
    assert "dpdb Commands" in overview
    assert "pinfo / pinfo2 [expr]" in overview

    buf.truncate(0)
    buf.seek(0)
    dbg.do_help("p")
    assert "help p" in buf.getvalue()

    with patch.object(Pdb, "do_help", return_value=None) as mock_super_help:
        dbg.do_help("exec")
    mock_super_help.assert_called_once_with("exec")

    with patch.object(dbg, "error") as mock_err:
        dbg.do_help("nonexistent_cmd")
    mock_err.assert_called_once()

    with (
        patch.object(dbg, "do_p", MagicMock(__doc__="")),
        patch.object(dbg, "error") as mock_err_doc,
    ):
        dbg.do_help("p")
    mock_err_doc.assert_called_once()


def test_dojo_pdb_do_interact() -> None:
    """Test DojoPdb.do_interact with and without an active frame."""
    buf = io.StringIO()
    dbg = _make_dojo_pdb(stdout=buf)

    dbg.curframe = None
    with patch.object(dbg, "error") as mock_err:
        dbg.do_interact("")
    mock_err.assert_called_once()

    test_frame = sys._getframe()  # ruff: ignore[private-member-access] -- obtain real frame for interact test
    dbg.setup(test_frame, None)
    mock_embed_instance = MagicMock()
    expected_interact_val = 42

    def fake_embed(*, local_ns: dict[str, object], **_kwargs: object) -> None:
        local_ns["interact_var"] = expected_interact_val

    mock_embed_instance.side_effect = fake_embed
    with patch(
        "debug_dojo._core.debugger.debugger.InteractiveShellEmbed",
        return_value=mock_embed_instance,
    ):
        dbg.do_interact("")
    mock_embed_instance.assert_called_once()
    assert "Interactive IPython shell" in buf.getvalue()
    assert (
        dbg._get_frame_locals(test_frame).get("interact_var")  # ruff: ignore[private-member-access] -- verify interact local mutation
        == expected_interact_val
    )
    dbg.close()


def test_dojo_pdb_close_and_message() -> None:
    """Test DojoPdb loop/executor cleanup and message output suppression."""
    dbg = _make_dojo_pdb()
    mock_loop = MagicMock()
    mock_loop.is_closed.return_value = False
    mock_executor = MagicMock()
    dbg.pt_loop = mock_loop
    dbg.thread_executor = mock_executor
    dbg.close()
    mock_loop.close.assert_called_once()
    mock_executor.shutdown.assert_called_once_with(wait=False)

    mock_loop.is_closed.return_value = True
    del dbg.thread_executor
    dbg.close()

    with patch("IPython.core.debugger.Pdb.message") as mock_super_msg:
        dbg.message("hello world")
        mock_super_msg.assert_called_once_with("hello world")

    dbg._suppress_message = True  # ruff: ignore[private-member-access] -- verify internal flag suppression
    with patch("IPython.core.debugger.Pdb.message") as mock_super_msg:
        dbg.message("suppressed")
        mock_super_msg.assert_not_called()


def test_dojo_pdb_user_return_branches() -> None:
    """Test DojoPdb.user_return skipping and pause handling."""
    dbg = _make_dojo_pdb()

    dbg._wait_for_mainpyfile = True  # ruff: ignore[private-member-access] -- verify internal flag branch
    with patch.object(Pdb, "user_return") as mock_super_ret:
        dbg.user_return(MagicMock(), None)
        mock_super_ret.assert_not_called()
    dbg._wait_for_mainpyfile = False  # ruff: ignore[private-member-access] -- reset internal flag

    mod_frame = MagicMock()
    mod_frame.f_code.co_name = "<module>"
    assert dbg._should_skip_return_pause(mod_frame) is True  # ruff: ignore[private-member-access] -- test return pause predicate

    func_frame = MagicMock()
    func_frame.f_code.co_name = "sample_fn"
    func_frame.f_lineno = 20
    dbg.lastcmd = "r"
    assert dbg._should_skip_return_pause(func_frame) is False  # ruff: ignore[private-member-access] -- test return pause predicate
    dbg.lastcmd = "ret"
    assert dbg._should_skip_return_pause(func_frame) is False  # ruff: ignore[private-member-access] -- test return pause predicate

    dbg.lastcmd = "n"
    dbg._last_paused_location = (  # ruff: ignore[private-member-access] -- simulate previous pause
        id(func_frame),
        func_frame.f_lineno,
    )
    with patch(
        "debug_dojo._core.debugger.debugger._is_explicit_return_line", return_value=True
    ):
        assert dbg._should_skip_return_pause(func_frame) is True  # ruff: ignore[private-member-access] -- test return pause predicate

        with patch.object(dbg, "set_step") as mock_step:
            dbg.user_return(func_frame, None)
            mock_step.assert_called_once()


def test_dojo_pdb_callable_break_branches() -> None:
    """Test all branches of _try_set_callable_break."""
    dbg = _make_dojo_pdb()

    dbg.curframe = None
    assert (
        dbg._try_set_callable_break("fn", None, temporary=False)  # ruff: ignore[private-member-access] -- test internal helper
        is False
    )

    test_frame = sys._getframe()  # ruff: ignore[private-member-access] -- obtain frame for test
    dbg.curframe = test_frame

    assert (
        dbg._try_set_callable_break("file.py:10", None, temporary=False)  # ruff: ignore[private-member-access] -- test internal helper
        is False
    )
    assert (
        dbg._try_set_callable_break("42", None, temporary=False)  # ruff: ignore[private-member-access] -- test internal helper
        is False
    )

    with patch.object(dbg, "_getval_except", return_value=123):
        assert (
            dbg._try_set_callable_break("non_callable", None, temporary=False)  # ruff: ignore[private-member-access] -- test internal helper
            is False
        )

    def dummy_fn() -> None:
        pass

    dummy_fn()

    with (
        patch.object(dbg, "_getval_except", return_value=dummy_fn),
        patch.object(dbg, "checkline", return_value=None),
    ):
        assert (
            dbg._try_set_callable_break("dummy_fn", None, temporary=False)  # ruff: ignore[private-member-access] -- test internal helper
            is False
        )

    with (
        patch.object(dbg, "_getval_except", return_value=dummy_fn),
        patch.object(dbg, "checkline", return_value=10),
        patch.object(dbg, "set_break", return_value="Invalid line"),
        patch.object(dbg, "error") as mock_err,
    ):
        assert (
            dbg._try_set_callable_break("dummy_fn", None, temporary=False)  # ruff: ignore[private-member-access] -- test internal helper
            is True
        )
        mock_err.assert_called_once_with("Invalid line")

    mock_bp = MagicMock()
    mock_bp.number = 1
    mock_bp.file = "test.py"
    mock_bp.line = 10
    with (
        patch.object(dbg, "_getval_except", return_value=dummy_fn),
        patch.object(dbg, "checkline", return_value=10),
        patch.object(dbg, "set_break", return_value=None),
        patch.object(dbg, "get_breaks", return_value=[mock_bp]),
        patch.object(dbg, "message") as mock_msg,
    ):
        assert (
            dbg._try_set_callable_break("dummy_fn", None, temporary=False)  # ruff: ignore[private-member-access] -- test internal helper
            is True
        )
        mock_msg.assert_called_once_with("Breakpoint 1 at test.py:10")
