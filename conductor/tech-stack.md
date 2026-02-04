# Technology Stack

## Core Language and Frameworks

- **Primary Language:** Python 3.10+
- **CLI Framework:** [Typer](https://typer.tiangolo.com/) - For building the command-line interface.
- **Data Modeling:**
  - [Pydantic](https://docs.pydantic.dev/) & [Dacite](https://github.com/konradhalas/dacite) - For configuration and internal data models.
  - [tomlkit](https://github.com/sdispater/tomlkit) - For style-preserving TOML parsing/editing.
- **Terminal UI & Formatting:**
  - [Rich](https://rich.readthedocs.io/) - For terminal formatting, syntax highlighting, and inspection.
  - [pyscn](https://github.com/bwrob/pyscn) - For visual scan/inspection utilities.
  - [Textual](https://textual.textualize.io/) - For TUI components and the interactive dashboard.

## Debugging Ecosystem

- **Backends:** Native integration with `debugpy`, `pudb`, `ipdb`, and standard `pdb`.
- **Instrumentation:** Custom wrappers for environment injection and execution control.

## Development & Quality Gate

- **Package Management:** [uv](https://github.com/astral-sh/uv) - Fast dependency management and workspace support.
- **Task Runner:** [Poe the Poet](https://poethepoet.natn.io/) - Centralized task management (`poe fix`, `poe type-check`).
- **Testing:** [pytest](https://docs.pytest.org/) with `pytest-cov` - High-coverage unit and integration testing.
- **Linting & Formatting:** [Ruff](https://beta.ruff.rs/) - Unified linter and formatter.
- **Static Analysis:** [basedpyright](https://github.com/DetachHead/basedpyright) - Strict type checking.
- **Architectural Guardrails:**
  - [tach](https://github.com/gauge-sh/tach) - Enforcing module boundaries and dependency rules.
  - [complexipy](https://github.com/pomponchic/complexipy) - Monitoring cognitive complexity.

## Documentation & Assets

- **Documentation:** [MkDocs](https://www.mkdocs.org/) with `mkdocs-material`.
- **CLI Docs:** `mkdocs-typer2` - Automatic reference generation.
- **Visuals:** [Typst](https://typst.app/) - For banner and asset generation.
