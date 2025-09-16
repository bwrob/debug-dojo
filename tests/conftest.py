"""Provide constants for tests."""

import pytest
from typer.testing import CliRunner

from debug_dojo._config_models import DebugDojoConfig


@pytest.fixture
def config() -> DebugDojoConfig:
    """Provide a default config for tests."""
    return DebugDojoConfig()


@pytest.fixture
def test_config_path() -> str:
    """Provide a path to a test config file."""
    return "tests/assets/config.toml"


@pytest.fixture
def test_target_inspect() -> str:
    """Provide a path to a test target file for inspection."""
    return "tests/assets/main_inspect.py"


@pytest.fixture
def test_target_exception() -> str:
    """Provide a path to a test target file for exception testing."""
    return "tests/assets/main_exception.py"


@pytest.fixture
def test_target_breakpoint() -> str:
    """Provide a path to a test target file for breakpoint testing."""
    return "tests/assets/main_breakpoint.py"


@pytest.fixture
def expected_dict_output() -> str:
    """Provide the expected output of the example_dict inspection."""
    return "{'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}"


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Typer CLI runner fixture."""
    return CliRunner()


@pytest.fixture
def test_string() -> str:
    """Provide a test string."""
    return "This is a test string."


@pytest.fixture
def another_test_string() -> str:
    """Provide another test string."""
    return "This is another test string."
