"""Example script demonstrating cl argument printing and inspection."""


def main() -> None:
    """Run the command-line interface.

    Raises:
        ValueError: Always raised to test post-mortem debugging.

    """
    msg = "This is a test exception for post-mortem debugging."
    raise ValueError(msg)


if __name__ == "__main__":
    main()
