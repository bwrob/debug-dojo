"""Example script demonstrating exception handling and post-mortem debugging."""

from __future__ import annotations


def main() -> None:
    """Run the command-line interface.

    Raises:
        ValueError: Always raised to test post-mortem debugging.

    """
    msg = "This is a test exception for post-mortem debugging."
    raise ValueError(msg)


if __name__ == "__main__":
    main()
