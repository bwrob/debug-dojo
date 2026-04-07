"""Provide constants for tests."""

import pytest
from typer.testing import CliRunner

from debug_dojo._config_models import DebugDojoConfig


@pytest.fixture
def config() -> DebugDojoConfig:
    """Provide a default config for tests.

    Returns:
        DebugDojoConfig: A default configuration object.

    """
    return DebugDojoConfig()


@pytest.fixture
def test_config_path() -> str:
    """Provide a path to a test config file.

    Returns:
        str: The path to a test configuration file.

    """
    return "tests/assets/config.toml"


@pytest.fixture
def test_target_inspect() -> str:
    """Provide a path to a test target file for inspection.

    Returns:
        str: The path to a test target script for inspection.

    """
    return "tests/assets/main_inspect.py"


@pytest.fixture
def expected_dict_output() -> str:
    """Provide the expected output of the example_dict inspection.

    Returns:
        str: The expected output string for dictionary inspection.

    """
    return "{'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}"


@pytest.fixture
def runner() -> CliRunner:
    """Provide a Typer CLI runner fixture.

    Returns:
        CliRunner: A Typer CLI runner object.

    """
    return CliRunner()
