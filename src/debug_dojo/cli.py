"""Command-line interface for running Python scripts or modules with debugging tools."""

import os
import runpy
import sys
from pathlib import Path

from rich import print as rich_print

from .installers import install_all


def execute_with_debug(target_name: str, args_for_target: list[str]) -> None:
    """Execute a target script or module with installation of debugging tools."""
    sys.argv = [target_name, *args_for_target]

    install_all()

    if (
        Path(target_name).exists()
        or target_name.endswith(".py")
        or os.sep in target_name
    ):
        if not Path(target_name).exists():
            sys.exit(1)
        runner = runpy.run_path
    else:
        runner = runpy.run_module

    _ = runner(target_name, run_name="__main__")


def main() -> None:
    """Run the command-line interface."""
    if len(sys.argv) < 2:
        rich_print(
            "[red]No target specified. Example usage: \n"
            + "dojo target_to_debug.py --some-input-to-target[/red]"
        )
        sys.exit(1)

    target_name = sys.argv[1]
    args_for_target = sys.argv[2:]

    execute_with_debug(target_name, args_for_target)
