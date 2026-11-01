# pytest-sugar Reference

`pytest-sugar` is a visual test reporting plugin for pytest. It transforms the
default dot-based test output into an informative, real-time progress bar with
instant failure notifications.

## 1. Key Features

`pytest-sugar` improves local development ergonomics in several ways:

- **Instant Failure Reporting**: When a test fails, `pytest-sugar` outputs the
  traceback and assertion details immediately, without waiting for the entire
  test suite to finish.
- **Real-Time Progress Bar**: Shows percentage completion, elapsed execution
  time, and active test paths.
- **Visual Status Glyphs**: Uses clean Unicode glyphs (✓ for passed, ✗ for
  failed, s for skipped) and ANSI colors.

## 2. Core CLI Usage

`pytest-sugar` activates automatically upon installation.

```bash
uv run pytest                         # Standard execution with sugar progress
uv run pytest -p no:sugar             # Disable pytest-sugar (standard output)
uv run pytest -v                      # Detailed test listing with sugar bar
```

## 3. Interaction with Other Plugins

`pytest-sugar` composes cleanly with the project testing tools:

- **`pytest-xdist`**: Renders aggregate progress across all parallel worker
  processes.
- **`pytest-cov`**: Shows coverage statistics after the final test completes
  without graphical glitches.
- **`hypothesis`**: Shows shrinking and falsifying examples with full colored
  tracebacks.
- **`syrupy`**: Prints diff comparisons on snapshot mismatches instantly upon
  failure.

## 4. Disabling in Headless CI Environments

In CI workflows or logs without animation support, disable `pytest-sugar`
from the command line:

```bash
# In CI workflow step
uv run pytest -p no:sugar
```

Or configure via `pytest.ini`:

```ini
[pytest]
addopts =
    -p no:sugar
    --strict-markers
```
