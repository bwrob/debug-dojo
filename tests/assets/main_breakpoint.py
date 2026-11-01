"""Example script demonstrating breakpoint handling."""

from __future__ import annotations


def main() -> None:
    """Run the command-line interface."""
    example_dict = {  # ruff: ignore[unused-variable] -- target test asset inspecting local variables in breakpoint scope
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
    }

    breakpoint()  # ruff: ignore[debugger] -- intentionally trigger breakpoint for integration testing


if __name__ == "__main__":
    main()
