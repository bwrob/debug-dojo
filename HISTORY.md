## v0.4.0 (2025-08-10)

*release tag*: [v0.4.0]

- New configuration model `DebugDojoConfig` for better structure.
- Added support for `debugger` configuration in `dojo.toml`.
- Updated `dojo` command to include debugger type in command call.
- Configuration versioning allows for in-flight migration of old configurations.
- Improved error handling in configuration loading.
- Improved catching errors from target execution.

## v0.3.2 (2025-07-28)

*release tag*: [v0.3.2]

- New logo for the project.
- Typer used for CLI implementation.
- Dojo is configured via `dojo.toml` or `pyproject.toml`.
- Support for `debugpy` and `ipdb` for debugging.
- Fixed documentation and history.

## v0.2.0 (2025-07-20)

*release tag*: [v0.2.0]

- Added `dojo` command for easy debugging setup.
- Added `p()` function for rich printing.
- Added history file for tracking changes.
- Moved to `hatch` for building and packaging.
- Fixed `pyproject.toml` to point to GitHub repository as the homepage.

## v0.1.0 (2025-07-19)

*release tag*: [v0.1.0]

- Initial module to install debugging tools.
- Debug mode utilities for PuDB, rich tracebacks, and object inspection.
