# Technology Stack

## Core Language and Frameworks
- **Primary Language:** Python
- **CLI Framework:** [Typer](https://typer.tiangolo.com/) - For building the command-line interface.
- **Data Validation:** [Pydantic](https://docs.pydantic.dev/) - For configuration and internal data models.
- **Terminal UI & Formatting:**
    - [Rich](https://rich.readthedocs.io/) - For beautiful terminal formatting, syntax highlighting, and object inspection.
    - [Textual](https://textual.textualize.io/) - (Planned) For building sophisticated TUI (Terminal User Interface) components.

## Debugging Ecosystem
- **Backends:** Supports integration with `debugpy`, `pudb`, `ipdb`, and the built-in `pdb`.

## Development and Quality Assurance
- **Package Management:** [uv](https://github.com/astral-sh/uv) - For fast dependency management and execution.
- **Task Runner:** [Poe the Poet](https://poethepoet.natn.io/) - For managing development tasks.
- **Testing:** [pytest](https://docs.pytest.org/) - For unit and integration testing.
- **Linting and Formatting:** [Ruff](https://beta.ruff.rs/) - For high-performance linting and code formatting.
- **Static Analysis:** [basedpyright](https://github.com/DetachHead/basedpyright) - For enhanced static type checking and LSP support.
- **Documentation:** [MkDocs](https://www.mkdocs.org/) - For project documentation.
