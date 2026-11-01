# pytest-cov Reference

`pytest-cov` integrates the `coverage` package into pytest, measuring line and
branch coverage across source code on every test execution.

## 1. Core CLI Commands

Measure, report, and enforce coverage thresholds with these commands.

```bash
uv run pytest --cov=src               # Measure coverage for src/ directory
uv run pytest --cov --cov-report=term-missing # Print missing line numbers
uv run pytest --cov --cov-report=html # Generate interactive HTML report
uv run pytest --cov --cov-report=xml  # Generate coverage.xml for CI
uv run pytest --cov-fail-under=80     # Fail if total coverage is below 80%
```

Run coverage tasks through Poe:

```bash
uv run poe test                       # Test with coverage and XML export
uv run poe coverage                   # Generate and inspect HTML report
```

## 2. Configuration via `.coveragerc`

This project configures coverage centrally using **`.coveragerc`** at the
root:

```ini
[run]
source = src
branch = true
omit =
    */tests/*
    */__snapshots__/*

[report]
fail_under = 80
show_missing = true
exclude_lines =
    pragma: no cover
    def __repr__
    if TYPE_CHECKING:
    raise NotImplementedError
    if __name__ == .__main__.:
```

### Key Options

- **`branch = true`**: Measures branch coverage (evaluating both `True` and
  `False` pathways for every conditional branch), not just simple line hits.
- **`fail_under = 80`**: Sets the minimum passing threshold percentage. If
  coverage falls below this number, the test process exits with non-zero code.
- **`omit`**: Excludes test fixtures, snapshots, and generated files.

## 3. Excluding Code from Coverage

When code is intentionally unreachable or purely defensive:

### Inline Exclusion

Add `# pragma: no cover` to individual lines or blocks:

```python
if unexpected_condition:
    raise RuntimeError("Defensive guard")  # pragma: no cover
```

### Block Exclusion

Any block matching patterns defined under `exclude_lines` in `.coveragerc`
is automatically skipped:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Skipped by 'if TYPE_CHECKING:' rule in .coveragerc
    from my_app.types import HeavyType
```

## 4. Best Practices for High Coverage

- **Test failure paths**: Do not only test happy paths. Assert error handling,
  exceptions, and validation edge cases.
- **Inspect `htmlcov/`**: Run `uv run poe coverage` and open
  `htmlcov/index.html` in a browser to see exact lines highlighted in red.
- **Do not abuse pragma**: Only mark code as `# pragma: no cover` if it is
  genuinely unreachable in standard test environments (for example, OS-specific
  fallbacks).
