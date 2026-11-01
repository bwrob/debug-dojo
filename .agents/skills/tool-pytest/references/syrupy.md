# syrupy Reference

`syrupy` is a zero-dependency snapshot testing library designed for pytest.
It captures complex data structures, rendered strings, or API responses and
stores them as serialized Amber (`.ambr`) snapshot files.

## 1. Core CLI Commands

Execute and update snapshot tests with these commands.

```bash
uv run pytest                         # Run tests and verify existing snapshots
uv run pytest --snapshot-update       # Update snapshots with current output
uv run pytest --snapshot-warn-unused  # Warn if snapshots exist with no test
```

Manage snapshots through Poe:

```bash
uv run poe test-snapshot-update       # Re-record snapshots after changes
```

## 2. Basic Snapshot Testing Workflow

Use the `snapshot` fixture in any pytest test function:

```python
from my_app.core import get_greeting


def test_greeting_snapshot(snapshot):
    result = get_greeting("Developer")
    assert result == snapshot
```

On the initial test run, `syrupy` creates a snapshot file at:

```text
tests/__snapshots__/test_core.ambr
```

Subsequent test runs compare the actual return value against the stored
snapshot content. If they diverge, pytest outputs a detailed unified diff.

## 3. Multiple Assertions in One Test

A single test can assert multiple snapshots by passing distinct identifiers:

```python
def test_multiple_outputs(snapshot):
    first_output = {"status": "ok", "step": 1}
    assert first_output == snapshot(name="step_1")

    second_output = {"status": "complete", "step": 2}
    assert second_output == snapshot(name="step_2")
```

## 4. Snapshot File Management & Git

- **Commit snapshot files**: Always commit `tests/__snapshots__/*.ambr` to
  version control alongside test code.
- **Review diffs carefully**: Never run `uv run poe test-snapshot-update`
  blindly. Inspect `git diff` to check that snapshot changes are intentional.
- **Spell-checker exclusion**: Include `*.ambr` in `extend-exclude` in
  `typos.toml`, as serialized hash IDs can trigger false-positive spelling

  warnings.
