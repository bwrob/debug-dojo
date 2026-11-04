"""Interactive debugger package (`dpdb`) powered by IPython and Rich."""

from __future__ import annotations

from debug_dojo._core.debugger.breakpoints import (
    _apply_break_spec,
    _extract_callable_target,
    _find_symbol_lineno,
    _unwrap_callable_code,
    has_active_breakpoints,
)
from debug_dojo._core.debugger.debugger import DojoPdb
from debug_dojo._core.debugger.session import (
    BREAKPOINT_ENV_VAR,
    DPDB_SET_TRACE_HOOK,
    _bdb_quit_excepthook,
    _get_debugger_cls,
    _init_pdb,
    pm,
    post_mortem,
    run_with_active_breakpoints,
    seed_cli_breakpoints,
    set_trace,
    setup,
    wrap_sys_excepthook,
)
from debug_dojo._core.debugger.views import is_runner_frame

__all__ = [
    "BREAKPOINT_ENV_VAR",
    "DPDB_SET_TRACE_HOOK",
    "DojoPdb",
    "_apply_break_spec",
    "_bdb_quit_excepthook",
    "_extract_callable_target",
    "_find_symbol_lineno",
    "_get_debugger_cls",
    "_init_pdb",
    "_unwrap_callable_code",
    "has_active_breakpoints",
    "is_runner_frame",
    "pm",
    "post_mortem",
    "run_with_active_breakpoints",
    "seed_cli_breakpoints",
    "set_trace",
    "setup",
    "wrap_sys_excepthook",
]
