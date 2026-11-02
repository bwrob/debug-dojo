"""Module for executing targets with debugging tools."""

from __future__ import annotations

import importlib.util
import os
import runpy
import site
import sys
from bdb import BdbQuit
from pathlib import Path
from pdb import Restart
from shutil import which
from typing import TYPE_CHECKING

import typer
from rich import print as rich_print

from debug_dojo import _dpdb
from debug_dojo._installers import install_tools

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from types import TracebackType
    from typing import Any

    Runner = Callable[..., dict[str, Any]]


def _configure_sys_argv(target_name: str, target_args: list[str]) -> None:
    """Configure `sys.argv` for the target script.

    Args:
        target_name (str): The name of the target script.
        target_args (list[str]): The arguments to pass to the target.

    """
    sys.argv = [target_name, *target_args]


def _find_venv_in_ancestors(start_dir: Path, venv_name: str = ".venv") -> Path | None:
    """Search `start_dir` and its parent directories for a virtual environment.

    Args:
        start_dir (Path): Directory from which to begin searching upward.
        venv_name (str): Name or relative path of the virtual environment directory.

    Returns:
        Path | None: Resolved virtual environment directory if found, else `None`.

    """
    for directory in (start_dir, *start_dir.parents):
        candidate = directory / venv_name
        if (candidate / "pyvenv.cfg").is_file():
            return candidate.resolve()
    return None


def _resolve_project_venv(start_dir: Path) -> Path | None:
    """Resolve the active or uv-managed project virtual environment directory.

    Checks `UV_PROJECT_ENVIRONMENT`, `VIRTUAL_ENV`, and ancestor `.venv`
    directories so `uvx debug-dojo` works without manual venv activation.

    Args:
        start_dir (Path): Starting directory for ancestor searches.

    Returns:
        Path | None: Resolved virtual environment path if discovered, else `None`.

    """
    uv_env = os.environ.get("UV_PROJECT_ENVIRONMENT")
    if uv_env:
        uv_path = Path(uv_env)
        if (uv_path / "pyvenv.cfg").is_file():
            return uv_path.resolve()
        found_uv = _find_venv_in_ancestors(start_dir, uv_env)
        if found_uv is not None:
            return found_uv

    active_venv = os.environ.get("VIRTUAL_ENV")
    if active_venv:
        venv_path = Path(active_venv)
        if (venv_path / "pyvenv.cfg").is_file():
            return venv_path.resolve()

    return _find_venv_in_ancestors(start_dir)


def _prepend_venv_bin_to_path(venv_dir: Path) -> None:
    """Prepend a virtual environment's binary directory to `PATH` if present.

    Args:
        venv_dir (Path): Root directory of the virtual environment.

    """
    current_path = os.environ.get("PATH", "")
    path_entries = current_path.split(os.pathsep) if current_path else []
    for bin_name in ("bin", "Scripts"):
        bin_dir = venv_dir / bin_name
        bin_str = str(bin_dir)
        if bin_dir.is_dir() and bin_str not in path_entries:
            os.environ["PATH"] = (
                f"{bin_str}{os.pathsep}{current_path}" if current_path else bin_str
            )
            current_path = os.environ["PATH"]


def _activate_venv_paths(venv_dir: Path) -> None:
    """Register a virtual environment's `site-packages` and `bin` directories.

    Args:
        venv_dir (Path): Root directory of the virtual environment.

    """
    for site_dir in (
        *venv_dir.glob("lib/python*/site-packages"),
        venv_dir / "Lib" / "site-packages",
    ):
        if site_dir.is_dir():
            site.addsitedir(str(site_dir))

    _prepend_venv_bin_to_path(venv_dir)


def _configure_project_venv(target_name: str) -> None:
    """Discover and attach a project virtual environment for `uvx` execution.

    Args:
        target_name (str): The target script, module, or executable name.

    """
    target_path = Path(target_name)
    start_dir = (
        target_path.resolve().parent if target_path.exists() else Path.cwd().resolve()
    )
    venv_dir = _resolve_project_venv(start_dir)
    if venv_dir is not None and venv_dir != Path(sys.prefix).resolve():
        _activate_venv_paths(venv_dir)


def _configure_sys_path(entry_dir: str) -> None:
    """Place `entry_dir` at `sys.path[0]`.

    Mirrors standard Python execution so sibling imports resolve cleanly.

    Args:
        entry_dir (str): Directory path to place at the head of `sys.path`.

    """
    if sys.path:
        sys.path[0] = entry_dir
    else:
        sys.path.insert(0, entry_dir)


def _is_importable_module(target_name: str) -> bool:
    """Return `True` if `target_name` resolves to an importable Python module spec.

    Args:
        target_name (str): Candidate module or package name.

    Returns:
        bool: `True` when `importlib.util.find_spec` locates the module.

    """
    if not target_name or "/" in target_name or "\\" in target_name:
        return False
    if target_name.endswith(".py"):
        return False
    try:
        return importlib.util.find_spec(target_name) is not None
    except (ImportError, ValueError, AttributeError):
        return False


def _get_runner_and_target(target_name: str) -> tuple[Runner, str]:
    """Auto-resolve `target_name` as a file path, executable on `PATH`, or module.

    Args:
        target_name (str): Script path, executable command, or module name.

    Returns:
        tuple[Runner, str]: The `runpy` runner function and resolved target string.

    Raises:
        typer.Exit: If `target_name` cannot be resolved as a file, executable, or
            module.

    """
    target_path = Path(target_name)
    if target_path.is_file():
        _configure_sys_path(str(target_path.resolve().parent))
        return runpy.run_path, target_name

    executable_path = which(target_name)
    if executable_path is not None and Path(executable_path).is_file():
        _configure_sys_path(str(Path(executable_path).resolve().parent))
        return runpy.run_path, executable_path

    _configure_sys_path(str(Path.cwd().resolve()))
    if _is_importable_module(target_name):
        return runpy.run_module, target_name

    rich_print(f"[red]Could not resolve target {target_name}.[/red]")
    raise typer.Exit(1)


def _is_runner_only_traceback(tb: TracebackType | None) -> bool:
    """Return `True` if every frame in `tb` belongs to the runner or import machinery.

    Args:
        tb (TracebackType | None): Traceback chain to inspect.

    Returns:
        bool: `True` when no user target frame is present in `tb`.

    """
    cur = tb
    while cur is not None:
        mod_name = str(cur.tb_frame.f_globals.get("__name__", "") or "")
        if not (
            _dpdb._is_runner_frame(cur.tb_frame)  # ruff: ignore[private-member-access] -- share internal runner frame predicate across package modules
            or mod_name.startswith(("importlib", "unittest"))
        ):
            return False
        cur = cur.tb_next
    return True


def _handle_exception(e: Exception) -> None:
    """Enter `dpdb` post-mortem debugging for an unhandled target exception.

    Args:
        e (Exception): The unhandled exception raised by the target.

    Raises:
        typer.Exit: Always raises `Exit(1)` after post-mortem completes.

    """
    _dpdb.post_mortem(e.__traceback__)
    raise typer.Exit(1) from e


def _invoke_target(runner: Runner, target_name: str) -> None:
    """Invoke `runner` directly or under `dpdb` trace dispatch if breakpoints exist.

    Args:
        runner (Runner): The function to run the target.
        target_name (str): The name of the target.

    """
    if _dpdb.has_active_breakpoints():
        _dpdb.run_with_active_breakpoints(
            lambda: runner(target_name, run_name="__main__")
        )
    else:
        _ = runner(target_name, run_name="__main__")


def _run_once(runner: Runner, target_name: str) -> None:
    """Execute a single run of the target, delegating exceptions appropriately.

    Args:
        runner (Runner): The function to run the target.
        target_name (str): The name of the target.

    Raises:
        Restart: Propagated when the user requests a program restart inside `dpdb`.
        typer.Exit: If an error occurs or the user terminates the session.

    """
    try:
        _invoke_target(runner, target_name)
    except Restart:
        raise
    except ImportError as e:
        if _is_runner_only_traceback(e.__traceback__):
            rich_print(f"[red]Error importing {target_name}:[/red]\n{e}")
            raise typer.Exit(1) from e
        _handle_exception(e)
    except BdbQuit:
        rich_print("[red]Debugging session terminated by user.[/red]")
        raise typer.Exit(0) from None
    except KeyboardInterrupt:
        rich_print("[red]Execution interrupted by user.[/red]")
        raise typer.Exit(0) from None
    except SystemExit as e:
        if bool(e.code):
            rich_print(f"[red]Script exited with code {e.code}.[/red]")
    except Exception as e:  # ruff: ignore[blind-except] -- catch all unhandled target errors to delegate to post-mortem handler
        _handle_exception(e)


def _safe_execute(
    runner: Runner,
    target_name: str,
) -> None:
    """Execute the target safely, supporting in-debugger restarts (`run`/`restart`).

    Args:
        runner (Runner): The function to run the target.
        target_name (str): The name of the target.

    """
    while True:
        try:
            _run_once(runner, target_name)
            break
        except Restart:
            rich_print(f"[cyan]Restarting {target_name}...[/cyan]")


def execute_with_debug(
    target_name: str,
    target_args: list[str],
    *,
    breaks: Sequence[str] | None = None,
) -> None:
    """Execute a target script, module, or command with `dpdb` and debugging tools.

    Args:
        target_name (str): The name of the script, module, or executable to run.
        target_args (list[str]): Arguments to pass to the target.
        breaks (Sequence[str] | None): Optional CLI breakpoint specifications.

    """
    _configure_sys_argv(target_name, target_args)
    _configure_project_venv(target_name)
    install_tools()
    runner, resolved_target = _get_runner_and_target(target_name)
    if breaks:
        _dpdb.seed_cli_breakpoints(resolved_target, breaks)
    _safe_execute(runner, resolved_target)
