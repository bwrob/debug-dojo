"""Debugging tools for Python.

This module provides functions to set up debugging tools like PuDB and Rich Traceback.
It checks for the availability of these tools and configures them accordingly.
"""

from .installers import install_inspect, use_pudb, use_rich_traceback

ii = install_inspect
pudb = use_pudb
rt = use_rich_traceback

__all__ = [
    "ii",
    "install_inspect",
    "pudb",
    "rt",
    "use_pudb",
    "use_rich_traceback",
]
