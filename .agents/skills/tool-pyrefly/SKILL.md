---
description: >-
  Guide for Meta Pyrefly static type checker in Python 3.12+.
  Use when type checking, configuring types, fixing type errors, or optimizing generic models.
  Triggers: pyrefly, type check, static typing, pyrefly.toml, types.
name: tool-pyrefly
version: 1.0.0
---

# Pyrefly Static Type Checker (`tool-pyrefly`)

`pyrefly` is a static type checker and Language Server Protocol (LSP)
for Python, written in Rust. It enforces strict type safety, generic checking,
and zero implicit `Any` types.

This project configures `pyrefly` with the `strict` preset mode to
guarantee type coverage across the codebase.

---

## 1. Core CLI Commands

Use these commands to check static typing and type completeness across the
project:

```bash
uv run pyrefly check                                         # Check entire project config
uv run pyrefly check path/to/file.py                         # Check a specific file or module
uv run pyrefly coverage check src --fail-under 100 --strict  # Enforce 100% strict type coverage
uv run pyrefly coverage check src --public-only              # Check public API completeness
uv run pyrefly coverage report src > coverage.json           # Generate JSON coverage report
uv run pyrefly check --output-format json                    # Output machine-readable JSON
uv run pyrefly init                                          # Generate pyrefly.toml config
```

---

## 2. Type Coverage and Completeness Enforcement

`pyrefly coverage` measures and enforces type annotation coverage across your
codebase. It provides two subcommands:

- **`pyrefly coverage check`**: Fails when coverage falls below a specified
  threshold. This project uses this as an automated CI and code-quality gate.
- **`pyrefly coverage report`**: Emits a structured JSON report with per-module
  and per-symbol coverage metrics.

### How Pyrefly Measures Coverage

Pyrefly counts coverage over **typables**:
- Function parameters
- Function return types
- Module-level variables
- Class attributes

Each typable has one of three states:
1. **Typed**: Annotated, and the resolved type contains no `Any`.
2. **Any**: Annotated, but the resolved type contains `Any`.
3. **Untyped**: No type annotation is present.

This project uses the `--strict` flag. Under `--strict`, any annotation that resolves
to `Any` counts as untyped. Only sound, concrete types count as covered.

Only public symbols count toward coverage: names without a leading underscore,
plus anything declared in `__all__`. Pyrefly automatically excludes `self` and
`cls` method parameters.

With `--public-only`, Pyrefly checks only symbols reachable from public
modules through re-export chains (PEP 561 public API type completeness).

### Poe Tasks for Type Coverage

This project provides two pre-configured Poe tasks:

```bash
uv run poe type-coverage         # Enforce 100% strict coverage on src/
uv run poe type-coverage-report  # Generate JSON report for inspection
```

`type-coverage` executes automatically in the `uv run poe code-quality`
pipeline.

---

## 3. Configuration Location

Configure Pyrefly in `pyrefly.toml` at the project root with `kebab-case` keys:

```toml
# Only respect explicit # pyrefly: ignore[...] comments (bans bare # type: ignore)
enabled-ignores      = ["pyrefly"]
infer-with-first-use = false

# Preset modes: "strict", "recommended", or "lenient"
preset = "strict"

# Root paths and exclusions for project source code
project-excludes = ["**/.*", "**/site", "**/dist", "**/build", "**/.venv"]
project-includes = ["src", "tests"]

# Target Python version
python-version = "3.13.0"

# Extra module search paths (e.g. src, stubs)
search-path = ["src"]
```

---

## 4. Common Configuration Changes

Adjust type checking rules and module search paths using these standard
patterns:

### A. Suppressing Type Errors on a Specific Line

Because `enabled-ignores = ["pyrefly"]` is active, Pyrefly ignores generic
`# type: ignore` comments. Use `# pyrefly: ignore[error-code]`:

```python
# Suppress a specific error code
result = untyped_library.call()  # pyrefly: ignore[unknown-attribute]

# Suppress multiple errors
data = legacy_payload.parse()  # pyrefly: ignore[bad-arg, missing-attribute]
```

> [!NOTE]
> Always specify the exact error code inside brackets. Never use bare
> ignores. To remove stale ignore comments across the codebase,
> run `uv run pyrefly check --remove-unused-ignores`.

### B. Handling Untyped or Heavy Third-Party Imports

When a third-party dependency lacks type stubs (`py.typed`) or has slow
internal annotations:

1. **Ignore missing imports** (`ignore-missing-imports`):

   ```toml
   ignore-missing-imports = [
       "untyped_pkg.*",
   ]
   ```

2. **Skip following imports into heavy packages** (`replace-imports-with-any`):

   ```toml
   replace-imports-with-any = [
       "heavy_legacy_sdk.*",
   ]
   ```

3. **Provide custom `.pyi` stubs** in `stubs/` and add to `search-path`:

   ```toml
   search-path = ["src", "stubs"]
   ```

### C. Per-Directory Rule Overrides (`[[sub-config]]`)

To relax specific error codes in a subdirectory (such as `tests/**`)
while keeping `src/**` at full strictness:

```toml
[[sub-config]]
matches = "tests/**"

[sub-config.errors]
bad-return = false
```

### D. Adding a New Directory to Type Checking

When adding a new directory such as `scripts/` or `benchmarks/`:

```toml
project-includes = ["src", "tests", "scripts"]
```

### E. Toggling Presets

While the project defaults to `strict`, projects during active prototyping can
adjust the preset level:

- **`strict`**: Requires full type coverage, disallows implicit `Any`,
  enforces exhaustive matching and protocol variance.
- **`recommended`**: Balanced enforcement suitable for general applications.
- **`lenient`**: Minimal barrier to entry, warnings only for overt mismatches.

```toml
preset = "recommended"
```

---

## 5. Modern Python 3.12+ Typing Patterns for Pyrefly

Write typed code with standard library features:

### Native Generics (PEP 695)

Use Python 3.12+ type parameter syntax instead of legacy `TypeVar`:

```python
# Correct (PEP 695)
type Matrix[T] = list[list[T]]


def first[T](items: list[T]) -> T | None:
    return items[0] if items else None
```

```python
# Legacy syntax to avoid
from typing import Optional, TypeVar

T = TypeVar("T")
```

### Protocol Contracts over Nominal Inheritance

Define interfaces with structural typing:

```python
from typing import Protocol


class Greeter(Protocol):
    def greet(self, name: str) -> str: ...
```

---

## 6. Best Practices & Troubleshooting

Follow these guidelines when type checking code:

- **Check frequently with Poe**: Run `uv run poe type-check` and
  `uv run poe type-coverage` before committing code.
- **Avoid `typing.Any`**: Use specific union types, generics, or `object`
  with narrowing (`isinstance`).
- **Missing `py.typed`**: If an installed library warns of missing types,
  install its stub package (for example, `uv add --dev types-requests`).
