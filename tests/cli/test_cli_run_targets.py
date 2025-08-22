"""Tests for debug-dojo CLI config print command."""

from typer.testing import CliRunner

from debug_dojo._cli import cli

runner = CliRunner()


def test_file_target() -> None:
    """Test running a file target from CLI."""
    args = [
        "tests/assets/test_target.py",
    ]
    result = runner.invoke(cli, args)

    print(result.output)

    assert result.exit_code == 0
    assert "{'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}" in result.output


def test_module_target() -> None:
    """Test running a module target from CLI.

    Test uses -m to run the debug_dojo module, which then runs the target script.
    """
    args = ["-m", "debug_dojo", "tests/assets/test_target.py"]
    result = runner.invoke(cli, args)

    print(result.output)

    assert result.exit_code == 0
    assert "{'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}" in result.output


def test_executable_target() -> None:
    """Test running an executable target from CLI.

    Test uses -e to run the debug_dojo executable, which then runs the target script.
    """
    args = ["-e", "dojo", "tests/assets/test_target.py"]
    result = runner.invoke(cli, args)

    print(result.output)

    assert result.exit_code == 0
    assert "{'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}" in result.output
