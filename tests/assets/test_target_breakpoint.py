"""Example script demonstrating cl argument printing and inspection."""

import sys

from rich import print as rich_print


def main() -> None:
    """Run the command-line interface."""
    if len(sys.argv) > 1:
        rich_print(sys.argv[1::])

    example_dict = {  # noqa: F841
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
    }

    breakpoint()  # noqa: T100


if __name__ == "__main__":
    main()
