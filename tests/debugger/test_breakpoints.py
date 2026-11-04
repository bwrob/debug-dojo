"""Tests for callable and CLI breakpoint resolution."""

from __future__ import annotations

import bdb
import functools
import io
import sys
from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

from debug_dojo._core.debugger.breakpoints import (
    _extract_callable_target,
    _find_symbol_lineno,
    _unwrap_callable_code,
    has_active_breakpoints,
)
from debug_dojo._core.debugger.debugger import DojoPdb
from debug_dojo._core.debugger.session import (
    run_with_active_breakpoints,
    seed_cli_breakpoints,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path


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


def test_smart_callable_breakpoint_resolution() -> None:
    """Test callable breakpoint unwrapping and resolution helpers."""

    def real_fn(x: int, y: int) -> int:
        return (x * 2) + y

    partial_fn = functools.partial(real_fn, 1)
    assert partial_fn(2) == 4  # ruff: ignore[magic-value-comparison] -- exercise helper body for 100% test coverage

    class SampleCallable:
        def __init__(self) -> None:
            pass

        def __call__(self) -> int:
            return 42

        @property
        def prop(self) -> int:
            return 7

    inst = SampleCallable()
    assert inst() == 42  # ruff: ignore[magic-value-comparison] -- exercise __call__ body for 100% test coverage
    assert inst.prop == 7  # ruff: ignore[magic-value-comparison] -- exercise property body for 100% test coverage

    assert _extract_callable_target(partial_fn) is real_fn
    assert _extract_callable_target(SampleCallable.prop) is SampleCallable.prop.fget
    assert _extract_callable_target(SampleCallable) is SampleCallable.__init__
    assert _extract_callable_target(inst) is SampleCallable.__call__
    assert _extract_callable_target(123) == 123  # ruff: ignore[magic-value-comparison] -- verify non-callable passthrough

    assert _unwrap_callable_code(real_fn) is real_fn.__code__
    assert _unwrap_callable_code(123) is None

    # Test DojoPdb.do_break resolving an in-scope callable expression with condition
    dbg = _make_dojo_pdb()
    try:
        dbg.clear_all_breaks()
        dbg.setup(sys._getframe(), None)  # ruff: ignore[private-member-access] -- obtain real frame for test
        dbg.do_break("real_fn, x > 0")
        assert has_active_breakpoints() is True

        # Test do_continue with c(...) routing to default
        with patch.object(dbg, "default") as mock_default:
            dbg.do_continue("(1, 2)")
            mock_default.assert_called_once_with("c(1, 2)")

        # Test normal do_continue delegates
        with patch(
            "IPython.core.debugger.Pdb.do_continue", return_value=1
        ) as mock_super_c:
            assert dbg.do_continue("") == 1
            mock_super_c.assert_called_once_with("")
    finally:
        dbg.clear_all_breaks()
        bdb.Breakpoint.next = 1
        bdb.Breakpoint.bplist.clear()
        bdb.Breakpoint.bpbynumber = [None]


def test_cli_breakpoint_helpers(tmp_path: Path) -> None:
    """Test CLI breakpoint seeding and active breakpoint execution helpers."""
    script = tmp_path / "sample.py"
    script.write_text(
        "def alpha():\n    return 1\n\nx = alpha()\n",
        encoding="utf-8",
    )

    assert _find_symbol_lineno(str(script), "alpha") == 1
    assert _find_symbol_lineno(str(script), "missing") is None
    assert _find_symbol_lineno(str(tmp_path / "nonexistent.py"), "alpha") is None

    dbg = _make_dojo_pdb()
    try:
        dbg.clear_all_breaks()
        assert has_active_breakpoints() is False

        with patch("debug_dojo._core.debugger.session._init_pdb", return_value=dbg):
            seed_cli_breakpoints(
                str(script),
                ["2", f"{script}:4", f"{script}:bad", "alpha", "unknown_sym"],
            )
            assert has_active_breakpoints() is True

            called: list[bool] = []
            mock_shell = MagicMock()
            dbg.shell = mock_shell
            run_with_active_breakpoints(lambda: called.append(True))
            assert called == [True]
            mock_shell.restore_sys_module_state.assert_called_once()

            # Also test when shell is None
            with patch.object(dbg, "shell", None):
                run_with_active_breakpoints(lambda: called.append(False))
            assert called == [True, False]
    finally:
        dbg.clear_all_breaks()
        bdb.Breakpoint.next = 1
        bdb.Breakpoint.bplist.clear()
        bdb.Breakpoint.bpbynumber = [None]
