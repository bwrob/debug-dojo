# pytest-randomly Reference

`pytest-randomly` randomizes the execution order of test items across files,
classes, and functions. This exposes ordering dependencies and un-isolated
shared state before tests reach production or CI.

## 1. Core CLI Commands

Control randomization and reproduce specific execution sequences with these
flags.

```bash
uv run pytest                         # Run tests in randomized order
uv run pytest --randomly-seed=12345   # Replay exact test order from seed
uv run pytest -p no:randomly          # Temporarily disable randomization
uv run pytest --randomly-dont-reset-seed # Keep system random state
```

## 2. Seed Logging and Deterministic Reproduction

Every test run outputs its randomization seed in the pytest header:

```text
Using --randomly-seed=175382189
```

When a failure occurs that does not reproduce in isolation:

1. Copy the `--randomly-seed=...` argument from the failing test run header.
2. Re-run pytest with that explicit seed flag:

   ```bash
   uv run pytest --randomly-seed=175382189
   ```

3. Pytest will execute every test in the exact same sequence, faithfully
   reproducing the failure.

## 3. Supported Random Generators

`pytest-randomly` automatically resets seeds for common Python RNG libraries
before each test:

- Python standard library `random`
- `numpy.random` (when present)
- `faker` (when present)

This guarantees each test starts from a known, pseudo-random state rather than
accumulating entropy from preceding tests.

## 4. Diagnosing State Leakage

When a test fails under `pytest-randomly`:

- **Identify the polluter**: Run `pytest --randomly-seed=...` with `-k` or
  binary search across test files to locate which prior test modified state.
- **Common culprits**:
  - Un-reset global caches (for example, `functools.lru_cache`). Clear them in an
    autouse fixture:

    ```python
    import pytest
    from my_app.core import get_greeting


    @pytest.fixture
    def clean_cache():
        yield
        get_greeting.cache_clear()


    @pytest.mark.usefixtures("clean_cache")
    def test_with_clean_cache():
        assert get_greeting("Dev") == "Hello, Dev!"
    ```

  - Environment variables set via `os.environ` instead of `monkeypatch.setenv`.
  - Unclosed temporary files or mutated class-level attributes.
