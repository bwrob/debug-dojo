"""Tests for debugger visual formatting, Rich tables, and inspection panels."""

from __future__ import annotations

import io
import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from rich.console import Console

from debug_dojo._core.debugger.debugger import DojoPdb
from debug_dojo._core.debugger.views import (
    _build_breakpoints_table,
    _build_psource_panel,
    _build_stack_table,
    _build_variables_table,
    _build_whatis_panel,
    _compute_locals_diff,
    _extract_arg_names,
    _extract_line_variables,
    _format_callable_signature,
    _format_chained_exception_line,
    _format_exception_chain,
    _format_return_banner,
    _format_shape_or_len,
    _format_watch_entries,
    _is_explicit_return_line,
    _is_user_local,
    _join_inline_items,
    _render_post_mortem_banner,
    _snapshot_user_locals,
    _tokenize_identifiers,
    is_runner_frame,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

EXPECTED_PAIR_COUNT = 2


class _ShapeDummy:
    """Dummy object with a non-callable `.shape` attribute."""

    shape = (3, 4)


class _UnSizedDummy:
    """Dummy object without `.shape` or `__len__`."""


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


def test_is_runner_frame() -> None:
    """Test is_runner_frame recognizes framework and runner frames."""
    frozen_frame = MagicMock()
    frozen_frame.f_code.co_filename = "<frozen runpy>"
    frozen_frame.f_globals = {"__name__": "runpy"}
    assert is_runner_frame(frozen_frame) is True

    runner_frame = MagicMock()
    runner_frame.f_code.co_filename = "/path/to/execution.py"
    runner_frame.f_globals = {"__name__": "debug_dojo._core.execution"}
    assert is_runner_frame(runner_frame) is True

    user_frame = MagicMock()
    user_frame.f_code.co_filename = "/path/to/app.py"
    user_frame.f_globals = {"__name__": "__main__"}
    assert is_runner_frame(user_frame) is False


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


def test_breakpoints_table() -> None:
    """Test _build_breakpoints_table creates a Rich table of breakpoints."""
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


def test_whatis_and_psource_helpers() -> None:
    """Test callable signature formatting, whatis panel, and psource panel."""

    def sample_callable(x: int) -> None:
        """Sample callable for signature and source inspection."""

    assert _format_callable_signature(42) is None
    assert _format_callable_signature(sample_callable) == "(x: 'int') -> 'None'"
    with patch("inspect.signature", side_effect=ValueError("no sig")):
        assert _format_callable_signature(sample_callable) is None

    panel_cls = _build_whatis_panel(" ShapeDummy", _ShapeDummy)
    assert panel_cls is not None
    assert _build_psource_panel("int", 42) is None


def test_chained_exception_formatting() -> None:
    """Test _format_chained_exception_line and _format_exception_chain."""
    assert _format_exception_chain(None) == []

    plain_err = ValueError("bad val")
    line_no_tb = _format_chained_exception_line("Caused by", plain_err)
    assert "ValueError" in line_no_tb
    assert "bad val" in line_no_tb

    def fail_inner() -> None:
        msg = "inner boom"
        raise KeyError(msg)

    def fail_chained() -> None:
        try:
            fail_inner()
        except KeyError as err:
            msg = "outer boom"
            raise RuntimeError(msg) from err

    try:
        fail_chained()
    except RuntimeError as outer_err:
        chain_lines = _format_exception_chain(outer_err)
        assert len(chain_lines) == 1
        assert "Caused by" in chain_lines[0]
        assert "KeyError" in chain_lines[0]

    def capture_implicit_context() -> BaseException:
        try:
            try:
                fail_inner()
            except KeyError:
                msg = "implicit outer"
                raise ValueError(msg)  # ruff: ignore[raise-without-from-inside-except] -- intentionally test implicit __context__ chain
        except ValueError as ctx_err:
            return ctx_err
        msg = "unreachable"  # pragma: no cover
        raise AssertionError(msg)  # pragma: no cover

    ctx_lines = _format_exception_chain(capture_implicit_context())
    assert len(ctx_lines) == 1
    assert "During handling of" in ctx_lines[0]


def test_is_explicit_return_line() -> None:
    """Test _is_explicit_return_line checks whether line starts with return."""
    mock_frame = MagicMock()
    mock_frame.f_code.co_filename = "dummy.py"
    mock_frame.f_lineno = 10
    with patch("linecache.getline", return_value="return\n"):
        assert _is_explicit_return_line(mock_frame) is True
    with patch("linecache.getline", return_value="return x + 1\n"):
        assert _is_explicit_return_line(mock_frame) is True
    with patch("linecache.getline", return_value="return(x)\n"):
        assert _is_explicit_return_line(mock_frame) is True
    with patch("linecache.getline", return_value="x = 1\n"):
        assert _is_explicit_return_line(mock_frame) is False
