"""Tests for debug-dojo CLI run targets."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from debug_dojo._cli import cli


@pytest.mark.parametrize(
    "run_args",
    [
        pytest.param([], id="file"),
        pytest.param(["debug_dojo"], id="module"),
        pytest.param(["dojo"], id="executable"),
    ],
)
def test_target(
    run_args: list[str],
    runner: CliRunner,
    test_target_inspect: str,
    expected_dict_output: str,
) -> None:
    """Test auto-detected file, module, and executable targets from CLI."""
    args = [*run_args, test_target_inspect]
    result = runner.invoke(cli, args)

    assert result.exit_code == 0
    assert expected_dict_output in result.output
