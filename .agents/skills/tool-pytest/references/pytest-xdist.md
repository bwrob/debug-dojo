# pytest-xdist Reference

`pytest-xdist` extends pytest with parallel test execution across multiple CPU
cores and distributed test running capabilities.

## 1. Core CLI Commands

Run tests concurrently using worker subprocesses.

```bash
uv run pytest -n auto                 # Distribute across all CPU cores
uv run pytest -n 4                    # Distribute across 4 worker cores
uv run pytest -n auto --dist loadscope # Group tests by module/class
uv run pytest -n auto --dist loadfile  # Group tests by test file
uv run pytest -f                      # Loop-on-fail: re-run on code change
```

Run parallel tests through the Poe task:

```bash
uv run poe test-fast                  # Executes pytest with -n auto
```

## 2. Distribution Modes (`--dist`)

The `--dist` option controls how xdist partitions tests across workers:

- **`--dist load`** (default): xdist dispatches tests to idle workers one by
  one. Maximizes CPU use across test suites.
- **`--dist loadscope`**: Assigns tests in the same module or class to the
  same worker. Ideal when class-level or module-level fixtures are
  expensive to initialize.
- **`--dist loadfile`**: All tests within a single test file execute on the
  same worker process.
- **`--dist loadgroup`**: Tests annotated with the `@pytest.mark.xdist_group`
  marker run together on the same worker:

  ```python
  import pytest


  @pytest.mark.xdist_group(name="shared_resource")
  def test_serial_a():
      assert True
  ```

## 3. Managing Shared State & Concurrency

When running in parallel, tests must not rely on shared global or disk state:

- **Temporary directories**: Use the `tmp_path` fixture (per test) or
  `tmp_path_factory` (per session) to isolate filesystem operations.
- **Worker identification**: Check the worker ID when setting up unique
  ports or database schemas:

  ```python
  def test_worker_env(worker_id: str):
      # worker_id is "gw0", "gw1", etc., or "master" when single-threaded
      assert worker_id.startswith("gw") or worker_id == "master"
  ```

## 4. Configuration in `pytest.ini`

To make parallel execution default for all `pytest` invocations, add `-n auto`
to `addopts`:

```ini
[pytest]
addopts =
    -n auto
    --dist loadscope
    --strict-markers
```
