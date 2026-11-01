---
description: >-
  Guide for linting and formatting Python with Astral Ruff.
  Use when linting code, auto-fixing violations, formatting source files, or configuring rules.
  Triggers: ruff, lint, format, ruff.toml, code style.
name: tool-ruff
version: 1.2.0
---


# Ruff Linter & Formatter (`tool-ruff`)

`ruff` is a fast Python linter and code formatter written in Rust by
Astral. It replaces Flake8, Black, isort, pydocstyle, pyupgrade, and autoflake.

This project configures `ruff` via `ruff.toml` with `select = ["ALL"]`
and targeted exceptions.

---

## 1. Core CLI Commands

Use these commands to lint, format, and inspect code violations across the
codebase.

### Linting & Fixing

```bash
uv run ruff check .                      # Check all files in repository
uv run ruff check path/to/file.py        # Check a specific file or folder
uv run ruff check --fix .                # Automatically apply safe fixes
uv run ruff check --fix --unsafe-fixes . # Apply safe and unsafe fixes
uv run ruff check --diff .               # Show proposed fixes without editing
uv run ruff check --watch .              # Continuous linting on file change
```

### Formatting

```bash
uv run ruff format .                     # Format all files in place
uv run ruff format --check .             # Check formatting without modifying
uv run ruff format --diff .              # Show formatting diffs
uv run ruff format path/to/file.py       # Format a single file
```

### Explaining Rules

```bash
uv run ruff rule E501                    # Display explanation for a rule
```

---

## 2. Configuration Location

This project configures Ruff via a standalone **`ruff.toml`** at the
repository root. The project pins Python to 3.13+ through `pyproject.toml`
tool configuration:

```toml
exclude     = [".venv", "site", "dist"]
line-length = 88

[lint]
    # Enable all rules on preview.
    preview = true
    select  = ["ALL"]
    ignore  = [
        "blank-line-before-class",
        "incorrect-blank-line-before-class",
        "missing-copyright-notice",
        "missing-trailing-comma",
        "multi-line-summary-second-line",
    ]

    [lint.flake8-bugbear]
        extend-immutable-calls = ["typer.Argument", "typer.Option"]

    [lint.flake8-tidy-imports]
        ban-relative-imports = "all"

    [lint.flake8-type-checking]
        exempt-modules = ["typing", "typing_extensions"]

    [lint.isort]
        combine-as-imports = true
        required-imports   = ["from __future__ import annotations"]

    # Per-file relaxations. Patterns are resolved relative to the directory
    # containing ruff.toml — NOT the process working directory.
    [lint.per-file-ignores]
        "scripts/*" = ["suspicious-subprocess-import"]
        "tests/*"   = ["assert", "suspicious-subprocess-import"]

[format]
    docstring-code-format = true
```

---

## 3. Common Configuration Changes During Development

Use these patterns to adjust rule selections, relaxations, and exceptions.

### A. Ignoring a Specific Rule Globally

If a rule is noisy or conflicts with domain design:

1. Add the rule **name** (rule-name form, not letter-digit codes) to
   `lint.ignore` in `ruff.toml` with a rationale comment:

   ```toml
   [lint]
   ignore = [
       "any-explicit",  # typing.Any tolerated in test fixtures
   ]
   ```

### B. Relaxing Rules for Specific Subtrees (`per-file-ignores`)

Tests and maintenance scripts often require rule exceptions. Keep
`src/` strictly enforced and scope relaxations per subtree:

```toml
[lint.per-file-ignores]
# pytest idioms: assertion-driven tests.
"tests/*" = ["assert", "suspicious-subprocess-import"]

# Maintenance scripts: subprocess drives repo-owned tooling.
"scripts/*" = ["suspicious-subprocess-import"]
```

Two resolution facts cost hours in real debugging:

- **Patterns are relative to the config file's directory**, not to the
  process cwd. Passing `--config /path/to/ruff.toml` from another directory
  makes relative patterns like `tests/*` fail to match. Run `ruff` from the
  directory that contains `ruff.toml`.
- **CLI `--exclude` replaces the config's `exclude` list** (it does not
  extend it). If you must override, restate the config values plus your
  additions.

### C. Inline Rule Suppression (`# ruff: ignore`)

When you need an exception on a single line rather than an entire file, use a
Ruff suppression directive — **never** a `# noqa` comment:

```python
# Suppress a single rule with the rule's full name
result = evaluate_untrusted_input(payload)  # ruff: ignore[suspicious-eval-usage]

# Suppress multiple rules in one directive
secret_token = fetch_token()
# ruff: ignore[hardcoded-password-default, hardcoded-password-string]
```

Placement rules for file-level diagnostics:

- Some rules fire on the module as a whole (for example
  `implicit-namespace-package`, `module-imports-not-top`).
  For these rules, place the directive on the **first line of the file**,
  before the module docstring:

  ```python
  # ruff: ignore[implicit-namespace-package]
  # Standalone maintenance script, not an importable package.
  """Module docstring goes after the directive."""
  ```

  A standalone `# ruff: ignore[...]` comment placed further down the file
  reports an unused-suppression error.
- Trailing directives target per-line diagnostics: put `# ruff: ignore[name]`
  on the line the diagnostic points at. When the diagnostic spans multiple
  candidate lines (formatter re-joins can shift them), do one of these:
  - place the directive on the last line of the expression
  - hoist the value into a named variable so the directive line becomes
    unambiguous

Naming rules:

- Always specify the rule by its full lowercase name:
  `# ruff: ignore[rule-name]`.
  Letter-digit codes such as `S603` fail the check.
- Pair suppressed rules with a justification comment unless the reason is
  obvious from the code itself.

Shell-vs-subprocess trap:

- `subprocess.run(cmd, shell=False)` does **not** silence
  `suspicious-subprocess-without-shell-equals-true`.
- Handle the family together:
  - silence the `S404` sibling `suspicious-subprocess-import` through
    `per-file-ignores` for repo-owned scripts
  - add the explicit `check=` argument to each call

Example: a maintenance script that must silence a module-level rule:

```python
# ruff: ignore[implicit-namespace-package]
# Standalone verification script; not an importable package.
"""Verify the package CLI entry points."""

from __future__ import annotations
```

### D. Enabling Unsafe Fixes for Specific Rules

By default, `ruff check --fix` applies only safe fixes. To enable automated
fixes for rules that Ruff marks as unsafe:

```toml
[lint]
extend-safe-fixes = ["enforce-iterable-allocation"]
```

### E. Future Annotations Enforcement

This project requires `from __future__ import annotations` in all Python source
files through `lint.isort.required-imports`. Ruff triggers rule
`required-imports (I002)` if this import is missing:

```bash
uv run ruff check --fix .  # Automatically inserts the required import
```

---

## 4. Guidelines and Gotchas

Follow these guidelines:

- **Always run check and format together**: A file is clean only when both
  `ruff check` and `ruff format` succeed.
- **Never fight the formatter**: If `ruff format` breaks lines across multiple
  rows, adjust structure or simplify expressions instead of patching the
  formatted output back together.
- **Formatter re-join hazard**: The formatter collapses implicit string
  concatenations and reflows f-string continuations. A directive pinned to a
  line the formatter rewrites will silently move.
  Hoist such values into a named constant so the directive line becomes
  stable.
- **Scope fixes to edited code**: Avoid running `--unsafe-fixes` across an
  entire codebase. Inspect diffs with `--diff` first.
