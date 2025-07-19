"""Install all debugging tools for the debug_dojo package."""

from .installers import (
    install_breakpoint,
    install_compare,
    install_inspect,
    use_pudb,
    use_rich_traceback,
)


def install_all() -> None:
    """Install debugging tools."""
    use_pudb()
    use_rich_traceback()

    install_inspect()
    install_compare()
    install_breakpoint()


install_all()
