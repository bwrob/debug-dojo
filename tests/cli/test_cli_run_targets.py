"""Tests for debug-dojo CLI config print command."""

from typing import TYPE_CHECKING

from typer.testing import CliRunner

from debug_dojo._cli import cli

if TYPE_CHECKING:
    from click.testing import Result


def test_file_target(
    runner: CliRunner, test_target_inspect: str, expected_dict_output: str
) -> None:
    """Test running a file target from CLI."""
    args: list[str] = [test_target_inspect]
    result: Result = runner.invoke(cli, args)

    print(result.output)

    assert result.exit_code == 0
    assert expected_dict_output in result.output


def test_module_target(
    runner: CliRunner, test_target_inspect: str, expected_dict_output: str
) -> None:
    """Test running a module target from CLI.

    Test uses -m to run the debug_dojo module, which then runs the target script.
    """
    args: list[str] = ["-m", "debug_dojo", test_target_inspect]
    result: Result = runner.invoke(cli, args)

    print(result.output)

    assert result.exit_code == 0
    assert expected_dict_output in result.output


def test_executable_target(
    runner: CliRunner, test_target_inspect: str, expected_dict_output: str
) -> None:
    """Test running an executable target from CLI.

    Test uses -e to run the debug_dojo executable, which then runs the target script.
    """
    args: list[str] = ["-e", "dojo", test_target_inspect]
    result: Result = runner.invoke(cli, args)

    print(result.output)

    assert result.exit_code == 0
    assert expected_dict_output in result.output
