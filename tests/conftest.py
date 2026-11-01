"""Provide constants and fixtures for tests."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


@pytest.fixture
def test_target_inspect() -> str:
    """Provide a path to a test target file for inspection.

    Returns:
        str: The path to a test target script for inspection.

    """
    return str(ASSETS_DIR / "main_inspect.py")


@pytest.fixture
def test_target_breakpoint() -> str:
    """Provide a path to a test target file for breakpoint testing.

    Returns:
        str: The path to a test target script for breakpoint testing.

    """
    return str(ASSETS_DIR / "main_breakpoint.py")


@pytest.fixture
def test_target_exception() -> str:
    """Provide a path to a test target file for exception testing.

    Returns:
        str: The path to a test target script for exception testing.

    """
    return str(ASSETS_DIR / "main_exception.py")


@pytest.fixture
def expected_dict_output() -> str:
    """Provide the expected output of the example_dict inspection.

    Returns:
        str: The expected output string for dictionary inspection.

    """
    return "{'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}"


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Typer CLI runner fixture configured without ANSI color codes.

    Returns:
        CliRunner: A Typer CLI runner object.

    """
    return CliRunner(env={"NO_COLOR": "1", "TERM": "dumb"})
