# Gemini Context: debug-dojo

This document provides context for the `debug-dojo` project, a Python-based command-line tool designed to enhance the debugging workflow.

## Project Overview

`debug-dojo` is a powerful Python package that streamlines debugging directly from the terminal. It acts as a unified interface for popular debuggers like `debugpy`, `pudb`, `pdb`, and `ipdb`. The project leverages the `rich` library to provide syntax-highlighted code, pretty-printed objects, and improved tracebacks for a "zen debugging" experience.

Key features include:

- A CLI tool named `dojo` to run scripts or modules with a specified debugger.
- In-code helper functions for setting breakpoints (`b()`), pretty-printing (`p()`), inspecting objects (`i()`), and comparing objects (`c()`).
- Configuration via `pyproject.toml` or a local `dojo.toml` file.

The project is structured as a standard Python package with its source code in the `src/debug_dojo` directory. It uses `typer` for the CLI, `poethepoet` as a task runner, and `uv` for dependency and environment management.

## Building and Running

The project uses `uv` for dependency management and `poethepoet` for running tasks.

### 1. Installation

To set up the development environment, install all dependencies using `uv`:

```bash
uv sync --locked --dev
```

### 2. Running Tests

Tests are written with `pytest` and can be run using the `poe` task runner:

```bash
poe test
```

To generate a coverage report:

```bash
poe coverage
```

### 3. Running the CLI Locally

The main entry point is the `dojo` command. You can run it via `uv run` to test local changes:

```bash
dojo --help
dojo my_script.py
```

## Development Conventions

The project enforces a strict set of development conventions through linting, formatting, and type-checking. These are primarily managed by `ruff` and `basedpyright`.

### Key Commands

All quality checks are defined as `poe` tasks in `pyproject.toml` and are run in CI.

- **Linting:** Check for code style and errors with `ruff`.

  ```bash
  poe lint
  ```

- **Formatting:** Check code formatting with `ruff`.

  ```bash
  poe format
  ```

- **Auto-Fixing:** Automatically fix formatting and linting issues.

  ```bash
  poe fix
  ```

- **Type-Checking:** Run static type analysis with `basedpyright`.

  ```bash
  poe type-check
  ```

- **All Checks:** Run the full pre-commit suite.

  ```bash
  poe precommit
  ```

- **Testing:** Run tests with coverage reporting.

  ```bash
  poe test
  poe coverage
  ```

- **Dependency Checking:** Ensure dependencies are as intended.

  ```bash
  poe dependencies
  ```
