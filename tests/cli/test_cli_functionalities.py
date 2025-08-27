"""Tests for debug-dojo CLI config print command."""

from typer.testing import CliRunner

from debug_dojo._cli import cli


def _breakpoint_ipdb(  # noqa: PLR0913
    runner: CliRunner,
    test_config_path: str,
    test_target_breakpoint: str,
    test_string: str,
    another_test_string: str,
    expected_dict_output: str,
) -> None:
    """Test breakpoint with ipdb from CLI.

    Only testing ipdb here since pdb is caught by pytest runner and does not behave as
    expected.
    """
    args = ["-d", "ipdb", "-c", test_config_path, test_target_breakpoint]
    inputs = [
        "inspect(example_dict)",
        f"print('{test_string}')",
        f"compare('{test_string}','{another_test_string}')",
        "c",
        "\n",
    ]
    result = runner.invoke(cli, args, input="\n".join(inputs))

    assert result.exit_code == 0
    # ipdb prompt
    assert "ipdb>" in result.output
    # breakpoint line in code context
    assert "breakpoint" in result.output
    # inspected dict output through prompt
    assert expected_dict_output in result.output
    # printed test string through prompt
    assert test_string in result.output
    # compare with two strings through prompt
    assert another_test_string in result.output


def _test_post_mortem(
    runner: CliRunner,
    test_config_path: str,
    test_target_exception: str,
) -> None:
    """Test post-mortem with ipdb from CLI.

    Only testing ipdb here since pdb is caught by pytest runner and does not behave as
    expected.
    """
    args = ["-d", "ipdb", "-c", test_config_path, test_target_exception]
    inputs = ["raise", "c", "\n"]

    result = runner.invoke(cli, args, input="\n".join(inputs))

    assert result.exit_code != 0
    # ipdb prompt
    assert "ipdb>" in result.output
    # post-mortem line in code context
    assert "post-mortem" in result.output
