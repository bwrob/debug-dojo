---
description: >-
  Guide for mutmut fast AST mutation testing in Python.
  Use when measuring test suite assertiveness, finding surviving mutants in local loops, and optimizing mutant kill rates.
  Triggers: mutmut, mutation testing, mutation, survivor, mutants, kill mutants.
name: tool-mutmut
version: 1.0.0
---

# mutmut Mutation Testing (`tool-mutmut`)

`mutmut` is a fast AST mutation testing framework for Python. It modifies
source code syntax trees directly in memory and local source files to introduce
small code defects. It executes tests against each mutant and identifies
surviving mutants that tests failed to catch.

This project uses `mutmut` for fast developer test loops on macOS and Linux.

---

## 1. Core CLI Commands

Use these commands to run mutations, inspect surviving mutants, and generate
reports:

```bash
uv run poe test-mutation          # Run fast mutation analysis across package source
uv run mutmut show <mutant_id>    # Show diff of surviving mutant
uv run mutmut html                # Generate HTML report in html/
uv run mutmut result-ids survived # List IDs of all surviving mutants
```

---

## 2. Platform Compatibility

> [!WARNING] Windows Limitation
> `mutmut` does not support Windows. It relies on POSIX process handling and
> filesystem mechanisms that cause failures on Windows.
>
> On Windows machines or cross-platform CI matrix runners, use `cosmic-ray`:
>
> ```bash
> uv run poe test-mutation-cosmic
> ```

---

## 3. Configuration Location

Configure `mutmut` in **`pyproject.toml`** at the project root under the
`[tool.mutmut]` table:

```toml
[tool.mutmut]
runner       = "pytest"
source_paths = ["src/"]
```

### Configuration Keys

- **`runner`**: Command used to run tests against each mutant (`pytest`).
- **`source_paths`**: List of directory paths containing source code to mutate.

---

## 4. Killing Surviving Mutants

When `mutmut` reports surviving mutants:

1. Identify the mutant ID from the terminal output:

   ```bash
   uv run mutmut result-ids survived
   ```

2. Inspect the exact code modification applied by `mutmut`:

   ```bash
   uv run mutmut show <mutant_id>
   ```

3. Trace the function and write a targeted unit test or property test in `tests/`
   that specifically asserts the mutated behavior.

4. Re-run `mutmut` targeting the specific mutant ID to verify the kill:

   ```bash
   uv run mutmut run --paths-to-mutate <file_path>
   ```
