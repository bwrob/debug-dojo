# Development Plan

## Project Goals

`debug-dojo` aims to provide a unified, "zen" debugging experience for Python developers. By abstracting the differences between various backend debuggers (`pdb`, `ipdb`, `pudb`, `debugpy`) and injecting useful runtime helpers (`p`, `c`, `i`, `b`), it allows developers to focus on the problem at hand rather than the toolchain configuration.

## Current Architecture

The project is organized as a standard Python package with a CLI entry point.

### Core Components

- **CLI (`src/debug_dojo/_cli.py`)**: The main entry point using `typer`. It handles command-line arguments and orchestrates the debugging session.
- **Configuration (`src/debug_dojo/_config.py`)**: Manages user preferences via `pyproject.toml` or `dojo.toml`. It supports versioning and schema migration.
- **Installers (`src/debug_dojo/_installers.py`)**: The heart of the application. It modifies the runtime environment to:
    - Set the appropriate `sys.breakpointhook`.
    - Install `rich` tracebacks.
    - Inject helper functions into `builtins`.
- **Runpy Wrapper**: The CLI uses `runpy` to execute the target script or module within the modified environment.

### Tooling

- **Dependency Management**: `uv`
- **Task Runner**: `poethepoet` (configured in `poe_tasks.toml`)
- **Build System**: `hatchling` (via `pyproject.toml`)

## Roadmap

The development roadmap is driven by GitHub issues. Below is the prioritized list of planned work.

### Features & Enhancements

- **[#85] Feature: Enhanced UI with Rich**: Leverage `rich` more extensively for interactive inspection tools during debugging sessions (e.g. better object inspectors, panels).
- **[#86] Feature: Plugin System**: Design and implement a plugin system to allow users to define their own helper functions or integrations.
- **[#87] Feature: Remote Debugging**: Simplify the setup for remote debugging scenarios using `debugpy`.
- **[#33] Direct IPython Integration**: Refactor the `ipdb` backend to potentially use `IPython`'s debugger directly.
- **[#4] PuDB Breakpoint Management**: Add functionality to manage `pudb`'s saved breakpoints via tool configuration.
- **[#2] Specialized Comparers**: Improve the `c()` helper to provide clearer, structural diffs for `list` and `dict` types.

### Maintenance & Stability

- **[#82] Maintenance: Dependency Updates**: Keep dependencies updated, specifically ensuring compatibility with new versions of supported debuggers.
- **[#83] Stability: Environment Injection Tests**: Improve test coverage for edge cases in environment injection logic (`_installers.py`).
- **[#35] Coverage Enforcement**: Integrate coverage reporting into the CI pipeline to ensure code quality.

### Documentation & Infrastructure

- **[#84] Documentation: Advanced Usage**: Expand the documentation to include more examples of advanced configuration and usage scenarios.
- **[#19] Automated Publishing Workflow**: Verify and refine the GitHub Actions for publishing to PyPI and deploying GitHub Pages.

## Infrastructure and CI/CD

- **Continuous Integration/Continuous Deployment (CI/CD)**: All code changes are validated and releases are automated via GitHub Actions pipelines.
- **Publishing**: Package and documentation publishing are handled automatically through these pipelines.

## Release Process

Releases are automated via GitHub Actions, triggered by `poe publish`. The process includes:
1.  Running full code quality checks (`poe code-quality`).
2.  Building the package (`uv build`).
3.  Publishing to PyPI (`uv publish`).
4.  Deploying documentation (`poe publish-docs`).
