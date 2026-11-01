"""Example script demonstrating object inspection with injected helpers."""

from __future__ import annotations


def main() -> None:
    """Run the command-line interface."""
    example_dict = {
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
    }

    i(example_dict)  # pyrefly: ignore[unknown-name]


if __name__ == "__main__":
    main()
