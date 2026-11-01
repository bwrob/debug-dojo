---
description: >-
  Guide for building modern type-safe CLIs with Typer and Rich in Python 3.12+.
  Use when designing command-line interfaces, parsing options, adding commands, or styling terminal output.
  Triggers: typer, cli, rich, arguments, options, commands.
name: tool-typer
version: 1.0.0
---


# Typer CLI Framework (`tool-typer`)

`typer` is the standard library for writing ergonomic, type-safe, and self-documenting
command-line interfaces (CLIs) in modern Python. It uses Python type hints to
provide automatic shell completion, parsing, validation, and rich terminal output.

In this project, `typer` and `rich` constitute the CLI layer (`src/<package>/cli.py`)
when you enable CLI generation.

---

## 1. Core Architecture & Philosophy

- **Type Hints as Single Source of Truth**: Typer derives CLI option names, arguments, types, defaults, and help menus directly from function signatures and docstrings.
- **Vendored Click (`typer._click`)**: Starting in Typer 0.26+, Typer vendors Click internally. Downstream applications must never import Click or rely on external Click extensions.
- **Explicit `Typer()` Apps**: Always instantiate an explicit `app = typer.Typer(...)` instance and register subcommands with `@app.command()`. Never use `typer.run()` in production applications.
- **Modern Configurations**:
  - `no_args_is_help=True`: Display the help message automatically when invoked without required arguments.
  - `rich_markup_mode="rich"`: Allow Rich tags (for example, `[bold green]...[/bold green]`) in command docstrings and parameter help text.

---

## 2. Modern Parameter Declaration with PEP 593 `Annotated`

This project enforces PEP 593 `typing.Annotated` for all Typer CLI parameters.

### Canonical Argument Syntax

```python
from typing import Annotated
import typer


@app.command()
def process(
    # Required Argument (no default assigned)
    input_file: Annotated[str, typer.Argument(help="Path to input dataset.")],
    # Optional Argument (default value assigned as Python standard default)
    output_dir: Annotated[str, typer.Argument(help="Destination directory.")] = "dist",
) -> None: ...
```

### Canonical Option Syntax

```python
@app.command()
def deploy(
    # Required Option
    token: Annotated[
        str,
        typer.Option("--token", "-t", help="API authentication token."),
    ],
    # Optional Flag / Option with short and long flags
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Enable verbose logging output."),
    ] = False,
    # Multi-value option
    tags: Annotated[
        list[str] | None,
        typer.Option("--tag", help="Deployment tags to associate."),
    ] = None,
) -> None: ...
```

### Legacy Antipatterns to Avoid

```python
# ❌ NEVER DO THIS: Deprecated legacy style causes Ruff B008 lint warnings
# and degrades static type checker inference.
@app.command()
def legacy(
    bad_arg: str = typer.Argument("default", help="..."),
    bad_req: str = typer.Argument(..., help="..."),
    bad_opt: bool = typer.Option(False, "--flag"),
) -> None: ...
```

### Deprecated Click-Inherited Parameters

Do not use Click parameters that modern Typer deprecates:
- `is_flag` (inferred automatically from `bool` type)
- `expose_value`
- `shell_complete`
- `show_choices`
- `prompt_required`
- `allow_from_autoenv`

---

## 3. Microsecond Cold-Startup & Lazy Loading

CLI applications must respond quickly (<50ms). Heavy imports executed at module load time degrade developer experience.

### Guidelines for Fast CLI Startup

1. **Defer Heavy Imports**: Do not import heavy libraries (for example, database drivers, machine learning frameworks, large data parsers) at the top of `cli.py`. Import them lazily inside the command body where they execute.
2. **Import Rich Utilities Inside Functions**: When using formatting or progress helpers,
   import lazily. Construct `Console()` instances within commands if startup latency is critical.
3. **Enforce with Ruff**: Use `flake8-tidy-imports` to detect and forbid premature top-level imports:
   ```toml
   [tool.ruff.lint.flake8-tidy-imports]
   banned-module-level-imports = ["typer.rich_utils"]
   ```

---

## 4. Rich Formatting & Terminal Output

Typer connects directly with `rich` for terminal formatting:

```python
from rich.console import Console
import typer

app = typer.Typer(rich_markup_mode="rich")
console = Console()


@app.command()
def status() -> None:
    """Check system health [bold green]status[/bold green]. :rocket:"""
    console.print("[bold green]✔ All systems operational[/bold green]")
```

### Testing Terminal Environment Overrides

When testing Typer CLI applications with pytest:
- Use `export TERMINAL_WIDTH=3000` to prevent unpredictable word-wrapping diffs in assertions across different terminal window sizes.
- Set `_TYPER_FORCE_DISABLE_TERMINAL=1` to ensure non-interactive, predictable outputs during automated test runs.

### Documentation Terminal Visualizations with Termynal (`.termy`)

Zensical configures interactive animated terminal widgets via Termynal (`docs/javascripts/termynal.js` and `docs/stylesheets/termynal.css`).

Wrap any console code block in `<div class="termy">` in your Markdown documentation:

```html
<div class="termy">

```console
$ uv run my-app greet "World"

✨ Hello, World!

// Inspect CLI options and help
$ uv run my-app --help

<b>Usage: </b><b>my-app [OPTIONS] COMMAND [ARGS]...</b>

╭─ Options ─────────────────────────────────────────╮
│ --version  -v        Show version and exit.       │
│ --help               Show this message and exit.  │
╰───────────────────────────────────────────────────╯
```

</div>
```

- Lines starting with `$ ` animate typing with a blinking cursor.
- Lines starting with `// ` format as styled callout comments (`💬 ...`).
- Supports Rich HTML colors (`<font color="...">`, `<b>`) and box-drawing characters.

---

## 5. Testing Architecture with `CliRunner`

Test Typer commands using `typer.testing.CliRunner`:

```python
from typer.testing import CliRunner
import pytest
from my_app.cli import app, main

runner = CliRunner()


def test_cli_help() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout


def test_cli_command_success() -> None:
    result = runner.invoke(app, ["greet", "Developer"])
    assert result.exit_code == 0
    assert "Hello, Developer!" in result.stdout


def test_cli_main_invocation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("sys.argv", ["my-app", "--help"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 0
```

---

## 6. Standard CLI Implementation Recipe

[examples/cli_recipe.py](./examples/cli_recipe.py) defines the standard layout.

Key implementation elements:
- Explicit `app = typer.Typer(no_args_is_help=True, rich_markup_mode="rich")`.
- Eager version flag callback (`version_callback`) raising `typer.Exit`.
- Subcommands registered via `@app.command()` with PEP 593 `Annotated` parameters.
- Top-level `main()` entry point callable directly by `__main__.py` and console scripts.
