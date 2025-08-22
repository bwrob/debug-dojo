"""Tests for debug-dojo CLI config print command."""

from typer.testing import CliRunner

from debug_dojo._cli import cli
from tests.constants import TEST_TARGET_INSPECT

runner = CliRunner()

__EXPECTED_DICT_OUTPUT = "{'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}"


def test_file_target() -> None:
    """Test running a file target from CLI."""
    args = [TEST_TARGET_INSPECT]
    result = runner.invoke(cli, args)

    print(result.output)

    assert result.exit_code == 0
    assert __EXPECTED_DICT_OUTPUT in result.output


def test_module_target() -> None:
    """Test running a module target from CLI.

    Test uses -m to run the debug_dojo module, which then runs the target script.
    """
    args = ["-m", "debug_dojo", TEST_TARGET_INSPECT]
    result = runner.invoke(cli, args)

    print(result.output)

    assert result.exit_code == 0
    assert __EXPECTED_DICT_OUTPUT in result.output


def test_executable_target() -> None:
    """Test running an executable target from CLI.

    Test uses -e to run the debug_dojo executable, which then runs the target script.
    """
    args = ["-e", "dojo", TEST_TARGET_INSPECT]
    result = runner.invoke(cli, args)

    print(result.output)

    assert result.exit_code == 0
    assert __EXPECTED_DICT_OUTPUT in result.output
