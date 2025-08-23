"""Constants for tests."""

import pytest
from typer.testing import CliRunner


@pytest.fixture
def test_config_path() -> str:
    """Path to a test config file."""
    return "tests/assets/test_config.toml"


@pytest.fixture
def test_target_inspect() -> str:
    """Path to a test target file for inspection."""
    return "tests/assets/test_target_inspect.py"


@pytest.fixture
def test_target_exception() -> str:
    """Path to a test target file for exception testing."""
    return "tests/assets/test_target_exception.py"


@pytest.fixture
def test_target_breakpoint() -> str:
    """Path to a test target file for breakpoint testing."""
    return "tests/assets/test_target_breakpoint.py"


@pytest.fixture
def expected_dict_output() -> str:
    """Expect output of the example_dict inspection."""
    return "{'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}"


@pytest.fixture
def runner() -> CliRunner:
    """Typer CLI runner fixture."""
    return CliRunner()


@pytest.fixture
def test_string() -> str:
    """A test string."""
    return "This is a test string."


@pytest.fixture
def another_test_string() -> str:
    """Another test string."""
    return "This is another test string."
