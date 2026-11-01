---
description: >-
  Guide for Coverage.py and branch coverage enforcement in Python.
  Use when measuring test coverage, inspecting missed branches, or configuring .coveragerc.
  Triggers: coverage, coverage.py, branch coverage, fail_under, coveragerc, htmlcov.
name: tool-coverage
version: 1.0.0
---

# Coverage.py Code Coverage (`tool-coverage`)

`Coverage.py` measures statement execution and branch coverage across Python
packages. It monitors program execution during test runs and evaluates
conditional branching outcomes.

This project uses `Coverage.py` to enforce a strict invariant: **100% statement and
branch test coverage**.

---

## 1. Core CLI Commands

Use these commands to measure test coverage and inspect missed branches:

```bash
uv run poe test             # Run test suite and enforce 100% coverage
uv run coverage report -m   # Display terminal summary with missed line numbers
uv run coverage html        # Generate interactive HTML report in htmlcov/
uv run coverage xml         # Generate machine-readable coverage.xml for CI
```

---

## 2. Configuration Location

Configure `Coverage.py` in **`.coveragerc`** at the project root:

```ini
[run]
branch = true
source =
    src/
    tests/
omit =
    tests/*
    .venv/*

[report]
fail_under = 100
show_missing = true
skip_covered = false
exclude_also =
    pragma: no cover
    def __repr__
    if self\.debug:
    raise AssertionError
    raise NotImplementedError
    if TYPE_CHECKING:
```

### Configuration Keys

- **`branch = true`**: Enables conditional branch coverage tracking.
- **`fail_under = 100`**: Fails the test run if total coverage is below 100%.
- **`show_missing = true`**: Prints exact line numbers of unexecuted code.
- **`exclude_also`**: Lists regex patterns and pragmas excluded from metrics.

---

## 3. Resolving Missed Coverage

When `Coverage.py` reports coverage below 100%:

1. Check the terminal output to identify the file and line numbers:

   ```bash
   uv run coverage report -m
   ```

2. Generate the HTML report to inspect conditional branches visually:

   ```bash
   uv run poe coverage
   ```

   Open `htmlcov/index.html` in a web browser to view highlighted lines.

3. Write targeted unit tests in `tests/` that assert the missing paths.

4. If a branch represents unreachable defensive code, mark it with an approved
   exclusion pragma:

   ```python
   if TYPE_CHECKING:  # pragma: no cover
       from typing import Any
   ```
