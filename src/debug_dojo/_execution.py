"""Module for executing targets with debugging tools."""

from __future__ import annotations

import os
import runpy
import site
import sys
import traceback
from bdb import BdbQuit
from enum import StrEnum
from pathlib import Path
from shutil import which
from typing import TYPE_CHECKING

import typer
from rich import print as rich_print

from debug_dojo._installers import install_tools
from debug_dojo.adapters import DebuggerType, enter_post_mortem

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    Runner = Callable[..., dict[str, Any]]


class ExecMode(StrEnum):
    """Execution mode for the target."""

    FILE = "file"
    MODULE = "module"
    EXECUTABLE = "executable"


def _configure_sys_argv(target_name: str, target_args: list[str]) -> None:
    """Configure sys.argv for the target script.

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
    directories so `uvx debug-dojo run` works without manual venv activation.

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


def _configure_project_venv(target_name: str, target_mode: ExecMode) -> None:
    """Discover and attach a project virtual environment for `uvx` execution.

    Args:
        target_name (str): The target script, module, or executable name.
        target_mode (ExecMode): The execution mode (FILE, MODULE, EXECUTABLE).

    """
    target_path = Path(target_name)
    start_dir = (
        target_path.resolve().parent
        if target_mode is ExecMode.FILE and target_path.exists()
        else Path.cwd().resolve()
    )
    venv_dir = _resolve_project_venv(start_dir)
    if venv_dir is not None and venv_dir != Path(sys.prefix).resolve():
        _activate_venv_paths(venv_dir)


def _configure_sys_path(resolved_target: str, target_mode: ExecMode) -> None:
    """Place the target script's directory (or CWD for modules) at `sys.path[0]`.

    Mirrors standard Python and `ipdb` script execution so sibling imports in
    the target directory resolve cleanly.

    Args:
        resolved_target (str): The resolved path or module name of the target.
        target_mode (ExecMode): The execution mode (FILE, MODULE, EXECUTABLE).

    """
    entry_dir = (
        str(Path.cwd().resolve())
        if target_mode is ExecMode.MODULE
        else str(Path(resolved_target).resolve().parent)
    )
    if sys.path:
        sys.path[0] = entry_dir
    else:
        sys.path.insert(0, entry_dir)


def _install_debug_tools(
    target_name: str,
    target_args: list[str],
    *,
    verbose: bool,
    debugger: DebuggerType | None = None,
) -> None:
    """Install opinionated debugging tools.

    Args:
        target_name (str): The name of the target script.
        target_args (list[str]): The arguments passed to the target.
        verbose (bool): Whether to print verbose output.
        debugger (DebuggerType | None): Optional debugger backend override.

    """
    if verbose:
        rich_print(f"[blue]Installing debugging tools for {target_name}.[/blue]")
        rich_print(f"[blue]Arguments for target: {target_args}[/blue]")

    install_tools(debugger)


def _get_runner_and_target(
    target_name: str,
    target_mode: ExecMode,
) -> tuple[Runner, str]:
    """Determine the runner function and resolved target path.

    Args:
        target_name (str): The name of the target.
        target_mode (ExecMode): The execution mode (FILE, MODULE, EXECUTABLE).

    Returns:
        tuple[Runner, str]: A tuple containing the runner function and the resolved
            target name.

    Raises:
        typer.Exit: If the target does not exist.

    """
    if target_mode is ExecMode.MODULE:
        return runpy.run_module, target_name

    resolved_name = target_name
    if target_mode is ExecMode.EXECUTABLE:
        resolved_name = which(target_name) or target_name

    if not Path(resolved_name).exists():
        rich_print(f"[red]File run mode couldn't resolve path {resolved_name}.[/red]")
        raise typer.Exit(1)

    return runpy.run_path, resolved_name


def _handle_exception(
    e: Exception, target_name: str, debugger: DebuggerType | None = None
) -> None:
    """Handle exceptions during execution and enter post-mortem debugging.

    Args:
        e (Exception): The exception that occurred.
        target_name (str): The name of the target being executed.
        debugger (DebuggerType | None): The selected debugger type.

    Raises:
        typer.Exit: Always raises Exit(1) after handling.

    """
    rich_print(f"[red]Error while running {target_name}:[/red]\n{e}")
    rich_print(traceback.format_exc())
    enter_post_mortem(e.__traceback__, debugger)
    raise typer.Exit(1) from e


def _safe_execute(
    runner: Runner,
    target_name: str,
    debugger: DebuggerType | None = None,
) -> None:
    """Execute the target safely, handling specific exceptions.

    Args:
        runner (Runner): The function to run the target.
        target_name (str): The name of the target.
        debugger (DebuggerType | None): The selected debugger type.

    Raises:
        typer.Exit: If an error occurs or the user interrupts the execution.

    """
    try:
        _ = runner(target_name, run_name="__main__")
    except ImportError as e:
        rich_print(f"[red]Error importing {target_name}:[/red]\n{e}")
        raise typer.Exit(1) from e
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
        _handle_exception(e, target_name, debugger)


def execute_with_debug(
    target_name: str,
    target_args: list[str],
    *,
    target_mode: ExecMode,
    verbose: bool,
    debugger: DebuggerType | None = None,
) -> None:
    """Execute a target script or module with installed debugging tools.

    Args:
        target_name (str): The name of the script, module, or executable to run.
        target_args (list[str]): Arguments to pass to the target.
        target_mode (ExecMode): The execution mode (FILE, MODULE, or EXECUTABLE).
        verbose (bool): If True, print verbose output.
        debugger (DebuggerType | None): Optional debugger backend override.

    """
    _configure_sys_argv(target_name, target_args)
    _configure_project_venv(target_name, target_mode)
    _install_debug_tools(target_name, target_args, verbose=verbose, debugger=debugger)
    runner, resolved_target = _get_runner_and_target(target_name, target_mode)
    _configure_sys_path(resolved_target, target_mode)
    _safe_execute(runner, resolved_target, debugger)
