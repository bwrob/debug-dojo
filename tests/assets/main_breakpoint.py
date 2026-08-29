"""Example script demonstrating cl argument printing and inspection."""


def main() -> None:
    """Run the command-line interface."""
    example_dict = {  # ruff: ignore[unused-variable]
        "key1": "value1",
        "key2": "value2",
        "key3": "value3",
    }

    breakpoint()  # ruff: ignore[debugger]


if __name__ == "__main__":
    main()
