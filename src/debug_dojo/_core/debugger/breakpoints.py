"""Breakpoint management, AST symbol lookup, and callable target resolution."""

from __future__ import annotations

import ast
import bdb
import contextlib
import functools
import inspect
from pathlib import Path
from types import CodeType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from IPython.core.debugger import Pdb


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
