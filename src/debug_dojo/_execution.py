"""Module for executing targets with debugging tools."""

from __future__ import annotations

import runpy
import sys
import traceback
from bdb import BdbQuit
from enum import Enum
from pathlib import Path
from shutil import which
from typing import TYPE_CHECKING

import typer
from rich import print as rich_print

from debug_dojo._installers import install_by_config

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Any

    from debug_dojo._config_models import DebugDojoConfig

    Runner = Callable[..., dict[str, Any]]  # pyright: ignore[reportExplicitAny]


class ExecMode(Enum):
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
    config: DebugDojoConfig,
) -> None:
    """Install debugging tools based on configuration.

    Args:
        target_name (str): The name of the target script.
        target_args (list[str]): The arguments passed to the target.
        verbose (bool): Whether to print verbose output.
        config (DebugDojoConfig): The configuration object.

    """
    if verbose:
        rich_print(f"[blue]Installing debugging tools for {target_name}.[/blue]")
        rich_print(f"[blue]Arguments for target: {target_args}[/blue]")

    install_by_config(config)


def _get_runner_and_target(
    target_name: str, target_mode: ExecMode
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
        raise typer.Exit(1)

    return runpy.run_path, resolved_name


def _handle_exception(e: Exception, target_name: str, config: DebugDojoConfig) -> None:
    """Handle exceptions during execution, optionally entering post-mortem.

    Args:
        e (Exception): The exception that occurred.
        target_name (str): The name of the target being executed.
        config (DebugDojoConfig): The configuration object.

    Raises:
        typer.Exit: Always raises Exit(1) after handling.

    """
    rich_print(f"[red]Error while running {target_name}:[/red]\n{e}")
    rich_print(traceback.format_exc())
    if config.exceptions.post_mortem:
        import ipdb  # pyright: ignore[reportMissingTypeStubs]  # noqa: PLC0415, T100

        rich_print("[blue]Entering post-mortem debugging session...[/blue]")
        ipdb.post_mortem(e.__traceback__)  # pyright: ignore[reportUnknownMemberType]
    raise typer.Exit(1) from e


def _safe_execute(
    runner: Runner,
    target_name: str,
    config: DebugDojoConfig,
) -> None:
    """Execute the target safely, handling specific exceptions.

    Args:
        runner (Runner): The function to run the target.
        target_name (str): The name of the target.
        config (DebugDojoConfig): The configuration object.

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
        if e.code:
            rich_print(f"[red]Script exited with code {e.code}.[/red]")
    except Exception as e:  # noqa: BLE001
        _handle_exception(e, target_name, config)


def execute_with_debug(
    target_name: str,
    target_args: list[str],
    *,
    target_mode: ExecMode,
    verbose: bool,
    config: DebugDojoConfig,
) -> None:
    """Execute a target script or module with installed debugging tools.

    Args:
        target_name (str): The name of the script, module, or executable to run.
        target_args (list[str]): Arguments to pass to the target.
        target_mode (ExecMode): The execution mode (FILE, MODULE, or EXECUTABLE).
        verbose (bool): If True, print verbose output.
        config (DebugDojoConfig): The debug-dojo configuration.

    Raises:
        typer.Exit: If the target file is not found, or if an import error occurs,
                    or if the script exits with a non-zero code.

    """
    _configure_sys_argv(target_name, target_args)
    _install_debug_tools(target_name, target_args, verbose=verbose, config=config)
    runner, resolved_target = _get_runner_and_target(target_name, target_mode)
    _safe_execute(runner, resolved_target, config)
