"""Utilities for side-by-side inspection and comparison of Python objects using Rich.

This module provides functions to display attributes and methods of two objects
in a visually appealing, side-by-side format in the terminal.
"""

from __future__ import annotations

import contextlib

from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.text import Text


def _get_object_attributes(obj: object) -> list[str]:
    """Extract and format non-callable attributes of an object.

    Args:
        obj: The object to inspect.

    Returns:
        A list of strings, each representing an attribute in 'name=value' format.

    """
    attributes: list[str] = []
    for attr_name in sorted(dir(obj)):
        # Safely get attribute, returning None if it doesn't exist
        attr = getattr(obj, attr_name, None)
        # Exclude dunder methods and callable attributes
        if not attr_name.startswith("__") and not callable(attr):
            with contextlib.suppress(AttributeError):
                # Use !r for robust string representation of the attribute value
                attributes.append(f"{attr_name}={attr!r}")
    return attributes


def _get_object_methods(obj: object) -> list[str]:
    """Extract and format public callable methods of an object.

    Args:
        obj: The object to inspect.

    Returns:
        A list of strings, each representing a method name.

    """
    methods: list[str] = []
    for method_name in sorted(dir(obj)):
        # Safely get attribute, returning None if it doesn't exist
        attr = getattr(obj, method_name, None)
        # Exclude private/protected methods (starting with '_') and non-callables.
        if not method_name.startswith("_") and callable(attr):
            methods.append(method_name)
    return methods


def _get_simplified_object_info(obj: object) -> list[Text]:
    """Generate a simplified, Rich-formatted inspection output for an object.

    Handles basic Python types by displaying their value directly. For other
    objects, it lists their attributes and public methods.

    Args:
        obj: The object to generate info for.

    Returns:
        A list of Rich Text objects, each representing a line of information.

    """
    info_lines: list[Text] = []
    obj_type: str = type(obj).__name__
    info_lines.append(Text(f"<class '{obj_type}'>", style="cyan bold"))
    info_lines.append(Text(""))

    # Handle basic data types by displaying their value directly
    if isinstance(obj, (str, int, float, list, dict, tuple, set, bool)) or obj is None:
        info_lines.append(Text("Value:", style="bold"))
        info_lines.append(Text(f"  {obj!r}", style="yellow"))
        info_lines.append(Text(""))
        info_lines.append(
            Text("No attributes or methods to display for this type.", style="dim")
        )
        return info_lines

    # For other objects, list attributes
    attributes = _get_object_attributes(obj)
    if attributes:
        info_lines.append(Text("Attributes:", style="bold"))
        info_lines.extend([Text(f"  {attr}") for attr in attributes])
    else:
        info_lines.append(Text("No attributes found.", style="dim"))
    info_lines.append(Text(""))

    # List methods
    methods = _get_object_methods(obj)
    if methods:
        info_lines.append(Text("Methods:", style="bold"))
        info_lines.extend([Text(f"  {method}()") for method in methods])
    else:
        info_lines.append(Text("No public methods found.", style="dim"))

    return info_lines


def inspect_objects_side_by_side(
    obj1: object,
    obj2: object,
) -> None:
    """Display two Python objects side-by-side in the terminal using Rich.

    Showing their attributes and methods in a simplified, aligned format.
    """
    main_console: Console = Console()

    lines1: list[Text] = _get_simplified_object_info(obj1)
    lines2: list[Text] = _get_simplified_object_info(obj2)

    # Determine the maximum number of lines to ensure consistent height
    max_lines: int = max(len(lines1), len(lines2))

    # Pad the shorter list of lines with empty Text objects to match the height
    if len(lines1) < max_lines:
        lines1.extend([Text("")] * (max_lines - len(lines1)))
    if len(lines2) < max_lines:
        lines2.extend([Text("")] * (max_lines - len(lines2)))

    # Join the padded lines into a single Text object for the Panel content
    padded_inspect_text1: Text = Text("\n").join(lines1)
    padded_inspect_text2: Text = Text("\n").join(lines2)

    panel1: Panel = Panel(padded_inspect_text1, border_style="green", expand=True)
    panel2: Panel = Panel(padded_inspect_text2, border_style="green", expand=True)

    main_console.print(Columns([panel1, panel2]))
