"""Tests for debug-dojo CLI config print command."""

import pytest
from typer.testing import CliRunner

from debug_dojo._cli import cli


@pytest.mark.parametrize(
    "run_args",
    [
        pytest.param([], id="file"),
        pytest.param(["-m", "debug_dojo", "run"], id="module"),
        pytest.param(["-e", "dojo", "run"], id="executable"),
    ],
)
def test_target(
    run_args: list[str],
    runner: CliRunner,
    test_target_inspect: str,
    expected_dict_output: str,
) -> None:
    """Test running a file target from CLI."""
    args = ["run", *run_args, test_target_inspect]
    result = runner.invoke(cli, args)

    assert result.exit_code == 0
    assert expected_dict_output in result.output
