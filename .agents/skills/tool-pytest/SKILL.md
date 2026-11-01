---
description: >-
  Guide for the pytest testing stack and plugins.
  Use when writing, running, debugging, or configuring unit, property, and snapshot tests.
  Triggers: pytest, testing, coverage, xdist, syrupy, hypothesis, pytest-cov.
name: tool-pytest
version: 1.0.0
---

# pytest Testing Stack (`tool-pytest`)

This project equips `pytest` with these testing tools:

- **Parallel Execution**: `pytest-xdist` (`-n auto`) for multi-core speed.
- **Flakiness Detection**: `pytest-randomly` for randomized execution order.
- **Visual Progress & Fast Feedback**: `pytest-sugar` for real-time progress.
- **Snapshot Testing**: `syrupy` for clean, declarative snapshot assertions.
- **Property-Based Testing**: `hypothesis` for generative edge-case discovery.
- **Branch Coverage**: `pytest-cov` enforcing 100% statement and branch coverage.

---

## 1. Core CLI Commands

Run tests across the suite, single files, or in parallel:

```bash
uv run pytest                         # Run all tests with coverage
uv run pytest -n auto                 # Run tests in parallel across cores
uv run pytest path/to/test_file.py    # Run a specific test file
uv run pytest -k "test_greeting"      # Run tests matching expression
uv run pytest -m "not slow"           # Run tests excluding markers
uv run pytest --snapshot-update       # Update syrupy snapshot files (.ambr)
uv run pytest --cov --cov-report=html # Generate HTML coverage in htmlcov/
```

Run tasks through Poe:

```bash
uv run poe test                 # Run tests with coverage and doctests
uv run poe test-fast            # Run tests in parallel with xdist
uv run poe test-lowest          # Verify against lowest-direct bounds
uv run poe test-dist            # Run tests against wheel distribution
uv run poe test-snapshot-update # Update Syrupy snapshots
uv run poe coverage             # Generate HTML coverage report
```

---

## 2. Configuration Files

Configure pytest and coverage in root configuration files.

### `pytest.ini`

```ini
[pytest]
addopts =
    --verbose -ra -p no:legacypath --doctest-modules
    --import-mode=importlib --strict-config --strict-markers --snapshot-warn-unused
# Uncomment when using pytest-asyncio (0.24+) to configure default fixture loop scope:
# asyncio_default_fixture_loop_scope = function
collect_imported_tests = false
console_output_style   = classic
log_format             = %(asctime)s [%(levelname)8s] %(name)s: %(message)s
log_level              = DEBUG
minversion             = 9.0
strict                 = true
testpaths              = tests src
xfail_strict           = true
filterwarnings         =
    error
    default::EncodingWarning
    error::EncodingWarning:my_package.*
doctest_optionflags    =
    DONT_ACCEPT_TRUE_FOR_1
    NORMALIZE_WHITESPACE
    ELLIPSIS
```

> [!TIP]
> Setting `-p no:legacypath` disables pytest's legacy `py.path.local` plugin, enforcing
> standard `pathlib.Path` across test fixtures (`tmp_path`). Setting `log_level = DEBUG`
> without `log_cli = true` captures `DEBUG` logs in memory. pytest prints them
> **only when a test fails**, keeping passing test runs quiet.
> When using `pytest-asyncio` 0.24+, set `asyncio_default_fixture_loop_scope = function` to
> silence event loop scoping warnings.

### `.coveragerc`

Coverage uses Python 3.12+'s low-overhead PEP 669 `sys.monitoring` engine (`core = sysmon`).
It tracks subprocesses and `os._exit()` calls automatically (`patch = subprocess, _exit`).
It monitors both `src/` and `tests/` so that pytest catches untested helper functions
or fixture branches immediately:

```ini
[run]
branch = true
core = sysmon
patch =
    subprocess
    _exit
source =
    src
    tests
omit =
    */__snapshots__/*
    */site-packages/*

[report]
fail_under = 80
show_missing = true
exclude_also =
    pragma: no cover
    def __repr__
    if TYPE_CHECKING:
    raise NotImplementedError
    return NotImplemented\b
    if __name__ == .__main__.:
    @overload
    @(typing\.)?overload
    (typing\.)?assert_never
    \.\.\.
```

---

## 3. Testing Paradigms

This project supports snapshot, property-based, and randomized tests.

### A. Snapshot Testing with `syrupy` (or `inline-snapshot` + `dirty-equals`)

Use `syrupy` snapshot assertions for complex data structures, rendered strings,
or payloads:

```python
def test_greeting_snapshot(snapshot):
    result = get_greeting("Developer")
    assert result == snapshot
```

Syrupy stores snapshots in `tests/__snapshots__/<test_file>.ambr`.
To update snapshots after intentional code changes:

```bash
uv run poe test-snapshot-update
```

For inline Python AST snapshots paired with declarative dynamic matchers
(`IsUUID`, `IsNow`, `IsPartialDict`), you can also combine `inline-snapshot`
and `dirty-equals`.

### B. Property-Based Testing with `hypothesis`

Use `hypothesis` to test mathematical invariants across hundreds of random
inputs:

```python
from hypothesis import given
from hypothesis import strategies as st


@given(st.text(min_size=1))
def test_greeting_always_contains_name(name: str):
    clean = name.strip()
    result = get_greeting(name)
    if clean:
        assert clean in result
    else:
        assert result == "Hello, World!"
```

### C. Randomized & Work-Stealing Execution (`pytest-randomly` & `pytest-xdist`)

`pytest-randomly` runs tests in a different order on each run. If a test
fails only when run after another test, they share state (for example,
global variables, un-reset caches, or dirty file systems).

To reproduce a specific randomized run:

```bash
uv run pytest --randomly-seed=12345
```

When running in parallel (`uv run poe test-fast`), This project uses
`--dist=worksteal --max-worker-restart=0`. Slow property-based tests do not
bottleneck a single worker, and native worker crashes fail immediately instead of
hanging.

---

## 4. Common Configuration Changes

Register markers, tune coverage thresholds, or exclude lines with these
settings:

### A. Registering Custom Test Markers

When adding markers (for example, `@pytest.mark.integration`), register them in
`pytest.ini` to avoid errors under `strict = true`:

```ini
[pytest]
markers =
    integration: External network or integration tests
    gpu: Hardware-dependent GPU tests
```

### B. Adjusting Coverage Thresholds

To adjust the minimum branch coverage requirement in `.coveragerc`:

```ini
[report]
fail_under = 85
```

### C. Ignoring Untestable Lines from Coverage

Add exclusion regex patterns under `exclude_also` in `.coveragerc`:

```ini
exclude_also =
    pragma: no cover
    if self\.debug:
    raise AssertionError
```

### D. Strict Encoding Hygiene (`PYTHONWARNDEFAULTENCODING=1`)

Python 3.10+ introduced `EncodingWarning` (PEP 597) to identify calls to `open()`
and text streams that omit an explicit encoding argument. All test
tasks execute with `PYTHONWARNDEFAULTENCODING=1`.
Under `filterwarnings` in `pytest.ini`, `default::EncodingWarning` and
`error::EncodingWarning:<package_name>.*` turn missing `encoding="utf-8"` in
first-party code into a fatal failure. They also prevent unpinned third-party plugin
warnings from breaking CI.

### E. Distribution Artifact Testing (`poe test-dist`)

Running `pytest` directly against `src/` can mask missing files in
`pyproject.toml` package data, broken `py.typed` markers, or distribution
compilation errors. `uv run poe test-dist` runs
`python scripts/verify_wheel.py --run-tests`. This script:

1. Builds a `.whl` package with `uv build --wheel`.
2. Creates a temporary, isolated virtual environment.
3. Installs the compiled `.whl` and test dependencies.
4. Runs the full `pytest` suite against the installed distribution with
   `python -I -m pytest` (`src/` omitted from `sys.path`).

---

## 5. Agent Test Engineering & Anti-Slop Standards

Follow these engineering rules when authoring or refactoring tests:

1. **One Test File Per Unit Under Test, Not Per Change/PR**:
   Always place new tests in the canonical `tests/test_<module>.py` file for the
   unit under test. Never create grab-bag test files named after a bug ticket,
   PR, or refactor (for example, `test_issue_123.py` or `test_new_validation.py`), which
   fragment module coverage. Keep single-use helper classes or functions inline
   inside the test function. Extract them to module level only when shared by
   3 or more tests.
2. **Behavior-Sentence Naming & Single Behavior Per Test**:
   Test names must state the observable behavior (`test_<action>_when_<condition>`
   or `test_<subject>_<expected_outcome>`). Each test must verify one behavior
   following clear Arrange / Act / Assert separation.
3. **The Hollow-Proof Test & Transformation vs. Pass-Through Rule**:
   Before finalizing a test, ask: *"What production bug could pass this test?"*
   - If a hardcoded return value passes the test, tighten the assertion.
   - Assert **transformed/computed outputs**, not echoed pass-through inputs
     (for example, asserting `result.name == "foo"` when you pass `name="foo"` only
     tests assignment, not business logic).
   - Never weaken or delete an existing assertion just to make a failing test
     pass.
4. **Provenance Docstrings on Regression Tests**:
   Every test added for a bug fix must include a concise provenance docstring.
   This docstring prevents future contributors or agents from deleting or weakening
   the test during refactoring:

   ```python
   def test_empty_identifier_raises_value_error() -> None:
       """Bug: whitespace-only identifiers bypassed length validation.
       Root cause: len() was checked before strip().
       Fix: normalize identifier with strip() before validation.
       """
   ```

5. **Zero-`sleep()` Concurrency Synchronization Policy**:
   Never use `time.sleep()`, `asyncio.sleep()`, or `anyio.sleep()` as a
   synchronization primitive in concurrent or async tests. Always coordinate
   producer/consumer or background task readiness with explicit primitives
   (`threading.Event`, `asyncio.Event`, `anyio.Event`). For async codebases,
   consider `blockbuster` to detect accidental blocking I/O calls inside the
   event loop, and `pytest-run-parallel` for PEP 703 free-threading stress
   testing.
6. **Fresh-Process Import-Graph Budget Testing**:
   Verify PEP 562 lazy imports (`_lazy.py`) to keep entry points fast and lean.
   Spawn a clean `subprocess.run([sys.executable, "-c", ...])`.
   Assert that deferred modules are absent from `sys.modules`.
7. **Union & Registry Sync Tripwire Tests**:
   Runtime registries or CLI option lists often mirror a static `Literal` or `Union` type alias.
   Add a reflection tripwire test using `typing.get_args()`
   (for example, `assert set(REGISTRY) == set(get_args(ActionType))`).
   Adding a variant without registering its runtime handler then fails immediately in `pytest`.

---

## 6. Plugin Reference Guides

See guides for each plugin:

- [pytest-xdist](references/pytest-xdist.md): Parallel execution and worker
  distribution.
- [pytest-randomly](references/pytest-randomly.md): Randomized test ordering
  and seed control.
- [pytest-sugar](references/pytest-sugar.md): Real-time progress bars and
  instant failure reporting.
- [pytest-cov](references/pytest-cov.md): Coverage measurement, branch analysis,
  and thresholds.
- [syrupy](references/syrupy.md): Snapshot testing with Amber (`.ambr`)
  snapshots.
- [hypothesis](references/hypothesis.md): Property-based testing and generative
  strategies.
