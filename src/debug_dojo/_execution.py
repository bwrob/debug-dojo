"""Module for executing targets with debugging tools."""

from __future__ import annotations

import runpy
import sys
import traceback
from bdb import BdbQuit
from enum import StrEnum
from pathlib import Path
from shutil import which
from typing import TYPE_CHECKING

import typer
from rich import print as rich_print

from debug_dojo._config_models import DebuggerType, DojoSettings
from debug_dojo._installers import install_tools

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import TracebackType
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


def _install_debug_tools(
    target_name: str,
    target_args: list[str],
    *,
    verbose: bool,
    settings: DojoSettings,
) -> None:
    """Install debugging tools based on settings.

    Args:
        target_name (str): The name of the target script.
        target_args (list[str]): The arguments passed to the target.
        verbose (bool): Whether to print verbose output.
        settings (DojoSettings): The runtime settings object.

    """
    if verbose:
        rich_print(f"[blue]Installing debugging tools for {target_name}.[/blue]")
        rich_print(f"[blue]Arguments for target: {target_args}[/blue]")

    install_tools(settings)


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


def _enter_post_mortem(tb: TracebackType | None, debugger: DebuggerType) -> None:
    """Enter a post-mortem debugging session with the requested or fallback debugger.

    Args:
        tb (TracebackType | None): The traceback object from the unhandled exception.
        debugger (DebuggerType): The configured debugger type.

    """
    rich_print("[blue]Entering post-mortem debugging session...[/blue]")
    if debugger is DebuggerType.IPDB:
        try:
            import ipdb  # ruff: ignore[import-outside-top-level, debugger]
        except ImportError:
            rich_print(
                "[yellow]IPDB not available, falling back to PDB post-mortem.[/yellow]",
            )
        else:
            ipdb.post_mortem(tb)
            return
    elif debugger is DebuggerType.PUDB:
        try:
            import pudb  # ruff: ignore[import-outside-top-level, debugger]
        except ImportError:
            rich_print(
                "[yellow]PuDB not available, falling back to PDB post-mortem.[/yellow]",
            )
        else:
            pudb.post_mortem(tb)
            return

    import pdb  # ruff: ignore[import-outside-top-level, debugger]

    pdb.post_mortem(tb)


def _handle_exception(e: Exception, target_name: str, settings: DojoSettings) -> None:
    """Handle exceptions during execution, optionally entering post-mortem debugging.

    Args:
        e (Exception): The exception that occurred.
        target_name (str): The name of the target being executed.
        settings (DojoSettings): The runtime settings object.

    Raises:
        typer.Exit: Always raises Exit(1) after handling.

    """
    rich_print(f"[red]Error while running {target_name}:[/red]\n{e}")
    rich_print(traceback.format_exc())
    if settings.post_mortem:
        _enter_post_mortem(e.__traceback__, settings.debugger)
    raise typer.Exit(1) from e


def _safe_execute(
    runner: Runner,
    target_name: str,
    settings: DojoSettings,
) -> None:
    """Execute the target safely, handling specific exceptions.

    Args:
        runner (Runner): The function to run the target.
        target_name (str): The name of the target.
        settings (DojoSettings): The runtime settings object.

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
        _handle_exception(e, target_name, settings)


def execute_with_debug(
    target_name: str,
    target_args: list[str],
    *,
    target_mode: ExecMode,
    verbose: bool,
    config: DojoSettings | None = None,
) -> None:
    """Execute a target script or module with installed debugging tools.

    Args:
        target_name (str): The name of the script, module, or executable to run.
        target_args (list[str]): Arguments to pass to the target.
        target_mode (ExecMode): The execution mode (FILE, MODULE, or EXECUTABLE).
        verbose (bool): If True, print verbose output.
        config (DojoSettings | None): The runtime settings object (or default if None).

    """
    settings = config or DojoSettings()
    _configure_sys_argv(target_name, target_args)
    _install_debug_tools(target_name, target_args, verbose=verbose, settings=settings)
    runner, resolved_target = _get_runner_and_target(target_name, target_mode)
    _safe_execute(runner, resolved_target, settings)
