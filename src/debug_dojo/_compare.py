"""Utilities for side-by-side inspection and comparison of Python objects.

This module provides functions to display attributes and methods of two objects in a
visually appealing, side-by-side format in the terminal.
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if TYPE_CHECKING:
    from collections.abc import Callable


def _get_members(
    obj: object,
    predicate: Callable[[str, Any], bool],  # pyright: ignore[reportExplicitAny]
    formatter: Callable[[str, Any], str],  # pyright: ignore[reportExplicitAny]
) -> list[str]:
    members: list[str] = []
    for name in sorted(dir(obj)):
        try:
            value = getattr(obj, name)  # pyright: ignore[reportAny]
        except Exception:  # noqa: S112, BLE001
            continue

        if predicate(name, value):
            with contextlib.suppress(Exception):
                members.append(formatter(name, value))
    return members


def get_object_attributes(obj: object) -> list[str]:
    """Extract and format non-callable attributes of an object.

    Args:
        obj (object): The object to extract attributes from.

    Returns:
        list[str]: A list of formatted strings, each representing an attribute.

    """
    return _get_members(
        obj,
        lambda n, v: not n.startswith("__") and not callable(v),  # pyright: ignore[reportAny]
        lambda n, v: f"{n}={v!r}",  # pyright: ignore[reportAny]
    )


def get_object_methods(obj: object) -> list[str]:
    """Extract and format public callable methods of an object.

    Args:
        obj (object): The object to extract methods from.

    Returns:
        list[str]: A list of method names.

    """
    return _get_members(
        obj,
        lambda n, v: not n.startswith("_") and callable(v),  # pyright: ignore[reportAny]
        lambda n, _v: n,  # pyright: ignore[reportAny]
    )


def _is_basic_type(obj: object) -> bool:
    """Check if the object is a basic Python type."""
    return (
        isinstance(obj, (str, int, float, list, dict, tuple, set, bool)) or obj is None
    )


def _get_basic_info(obj: object) -> list[Text]:
    """Get information for basic types."""
    return [
        Text("Value:", style="bold"),
        Text(f"  {obj!r}", style="yellow"),
        Text(""),
        Text("No attributes or methods to display for this type.", style="dim"),
    ]


def _format_section(title: str, items: list[str], empty_message: str) -> list[Text]:
    """Format a section of the inspection output."""
    lines: list[Text] = []
    if items:
        lines.append(Text(title, style="bold"))
        lines.extend([Text(f"  {item}") for item in items])
    else:
        lines.append(Text(empty_message, style="dim"))
    lines.append(Text(""))
    return lines


def _get_attributes_section(obj: object) -> list[Text]:
    """Get the attributes section for the object info."""
    return _format_section(
        "Attributes:",
        get_object_attributes(obj),
        "No attributes found.",
    )


def _get_methods_section(obj: object) -> list[Text]:
    """Get the methods section for the object info."""
    return _format_section(
        "Methods:",
        [f"{method}()" for method in get_object_methods(obj)],
        "No public methods found.",
    )


def get_simplified_object_info(obj: object) -> list[Text]:
    """Generate a simplified, Rich-formatted inspection output for an object.

    Handles basic Python types by displaying their value directly. For other objects, it
    lists their attributes and public methods.

    Args:
        obj (object): The object to generate info for.

    Returns:
        list[Text]: A list of Rich Text objects representing the object's information.

    """
    info_lines: list[Text] = []
    obj_type: str = type(obj).__name__
    info_lines.append(Text(f"<class '{obj_type}'>", style="cyan bold"))
    info_lines.append(Text(""))

    if _is_basic_type(obj):
        info_lines.extend(_get_basic_info(obj))
        return info_lines

    info_lines.extend(_get_attributes_section(obj))
    info_lines.extend(_get_methods_section(obj))

    return info_lines


def inspect_objects_side_by_side(
    obj1: object,
    obj2: object,
) -> None:
    """Display two Python objects side-by-side in the terminal using Rich.

    Showing their attributes and methods in a simplified, aligned format.

    Args:
        obj1 (object): The first object to display.
        obj2 (object): The second object to display.

    """
    main_console: Console = Console()

    # Get info for both objects
    lines1: list[Text] = get_simplified_object_info(obj1)
    lines2: list[Text] = get_simplified_object_info(obj2)

    # Convert list of Text to a single Renderable for Panel
    inspect_text1: Text = Text("\n").join(lines1)
    inspect_text2: Text = Text("\n").join(lines2)

    # Create Panels for each object's info
    panel1: Panel = Panel(inspect_text1, border_style="green", expand=True)
    panel2: Panel = Panel(inspect_text2, border_style="green", expand=True)

    # Use a Table to display panels side-by-side
    table = Table(show_header=False, show_lines=False, expand=True)
    table.add_column(width=main_console.width // 2 - 1)
    table.add_column(width=main_console.width // 2 - 1)
    table.add_row(panel1, panel2)

    main_console.print(table)
