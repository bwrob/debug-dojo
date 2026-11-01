---
description: >-
  Guide for Griffe static analysis and API change detector in Python.
  Use when checking breaking API changes, parsing docstrings, or inspecting public signatures.
  Triggers: griffe, check-api, breaking changes, public api, docstrings, ast.
name: tool-griffe
version: 1.0.0
---

# Griffe Static Analysis & API Inspector (`tool-griffe`)

`griffe` is a fast static analysis tool for Python. It parses Python source code
into Abstract Syntax Trees (AST) without loading modules into the runtime. It
extracts signatures, type hints, docstrings, and public APIs.

This project uses `griffe` to generate API documentation and detect breaking changes in
public interfaces.

---

## 1. Core CLI Commands

Use these commands to inspect APIs and detect breaking changes.

```bash
uv run griffe check <package_name> --search src             # Check breaking changes against last tag
uv run griffe check <package_name> --search src -a origin/main  # Compare against a git branch
uv run griffe dump <package_name> --search src              # Dump API data as JSON to stdout
uv run griffe dump <package_name> --search src -o api.json  # Save API data to file
```

This project connects API verification to Poe:

```bash
uv run poe check-api    # Runs: griffe check <package_name> --search src
```

---

## 2. Breaking Change Detection (`griffe check`)

The `griffe check` command compares the current code against a git reference. It
reports breaking changes:

- Removed public functions, classes, or methods.
- Removed or renamed positional parameters.
- Added required parameters without default values.
- Changed type annotations that break caller compatibility.

### Common Invocations

Compare against the main branch:
```bash
uv run griffe check <package_name> --search src --against origin/main
```

Output GitHub Actions workflow error notices:
```bash
uv run griffe check <package_name> --search src -f github
```

---

## 3. Extension Configuration

This project configures `griffe` extensions inside `zensical.toml` under the
`[plugins.mkdocstrings]` section:

```toml
[plugins.mkdocstrings]
    handlers.python.paths = ["src"]
    handlers.python.options.extensions = ["griffe_warnings_deprecated"]
    handlers.python.options.show_source = true
    handlers.python.options.show_signature_annotations = true
```

The `griffe_warnings_deprecated` extension reads PEP 702 `@warnings.deprecated`
decorators and adds deprecation notices to documentation pages.

---

## 4. Guidelines and Troubleshooting

- **Safe AST Parsing**: `griffe` does not import Python modules. It is safe to run
  against modules with heavy or uninstalled runtime dependencies.
- **Private API Exclusion**: Names that start with an underscore (`_`) are private.
  `griffe check` ignores private members unless you pass `--verbose`.
- **Breaking Changes in Pull Requests**: When `poe check-api` flags breaking
  changes on a feature branch, restore compatibility. Add default parameter
  values, or add a breaking notice to the PR title (`feat!:`) and changelog.
