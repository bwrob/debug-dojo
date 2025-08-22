"""Tests for debug-dojo CLI config print command."""

import rich
from typer.testing import CliRunner

from debug_dojo._cli import cli
from tests.constants import TEST_TARGET_BREAKPOINT

runner = CliRunner()

__EXPECTED_DICT_OUTPUT = "{'key1': 'value1', 'key2': 'value2', 'key3': 'value3'}"
__TEST_STRING = "This is a test string."
__ANOTHER_TEST_STRING = "This is another test string."


def test_breakpoint_ipdb() -> None:
    """Test breakpoint with ipdb from CLI.

    Only testing ipdb here since pdb is caught by pytest runner and does not behave as
    expected.
    """
    args = ["-d", "ipdb", TEST_TARGET_BREAKPOINT]
    inputs = [
        "i(example_dict)",
        f"p('{__TEST_STRING}')",
        f"c('{__TEST_STRING}','{__ANOTHER_TEST_STRING}')",
        "c",
        "\n",
    ]
    result = runner.invoke(cli, args, input="\n".join(inputs))

    rich.print(result.output)

    assert result.exit_code == 0
    # ipdb prompt
    assert "ipdb>" in result.output
    # breakpoint line in code context
    assert "b()" in result.output
    # inspected dict output through prompt
    assert __EXPECTED_DICT_OUTPUT in result.output
    # printed test string through prompt
    assert __TEST_STRING in result.output
    # compare with two strings through prompt
    assert __ANOTHER_TEST_STRING in result.output
