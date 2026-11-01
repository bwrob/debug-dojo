---
description: >-
  Guide for using Astral uv to manage packages and environments.
  Use when adding dependencies, syncing environments, locking packages, running commands, or building distributions.
  Triggers: uv, packages, dependencies, virtual environment, lockfile, uv.lock.
name: tool-uv
version: 1.0.0
---


# uv Package & Environment Manager (`tool-uv`)

`uv` is a fast, Rust-based Python package and project manager
developed by Astral. It replaces `pip`, `poetry`, and `virtualenv`.

In this project, `uv` is the exclusive manager for dependencies,
virtual environments, lockfiles, and package builds.

---

## 1. Core CLI Commands

Use these commands to manage project environments, packages, and builds.

### Environment & Dependency Synchronization

```bash
uv sync                      # Install all default groups from uv.lock
uv sync --all-groups         # Install every group defined in pyproject.toml
uv sync --only-group <group> # Install strictly one group (e.g., in CI)
uv sync --no-dev             # Install strictly runtime dependencies
uv sync --frozen             # Sync without updating lockfile
```

### Managing Dependencies

```bash
uv add <package>                     # Add runtime dependency
uv add --group <group> <package>     # Add dependency to specific group
uv add --dev <package>               # Shorthand for --group dev
uv remove <package>                  # Remove runtime dependency
uv remove --group <group> <package>  # Remove dependency from a group
```

### Running Commands in Virtual Environment

```bash
uv run <command>             # Run CLI command or task in project venv
uv run python script.py      # Run script with project dependencies
uv run -p 3.13 <command>     # Run with a specific Python version
uvx <tool>                   # Run isolated tool without adding to project
```

### Lockfile, Security Audit, & Build Commands

```bash
uv lock                              # Update uv.lock without installing
uv lock --upgrade                    # Upgrade all packages to latest
uv lock --upgrade-package <pkg>      # Upgrade a single package
uv audit                             # Scan uv.lock against security advisories
uv build                             # Build source distribution and wheel
uv publish                           # Publish distributions to PyPI
```

---

## 2. Configuration Location

Configure `uv` primarily through `pyproject.toml` in the project root:

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.12"
license = "MIT"
license-files = ["LICENSE"]
dependencies = [
    "typer>=0.15.0",
]

[dependency-groups]
dev = [
    "poethepoet>=0.42.0",
    { include-group = "test" },
    { include-group = "lint" },
    { include-group = "docs" },
]
test = [
    "poethepoet>=0.42.0",
    "pytest>=9.0.0",
    "hypothesis>=6.125.0",
]
lint = [
    "ruff>=0.17.0",
    "pyrefly>=1.3.0",
]
docs = [
    "zensical>=0.0.70",
    "mkdocstrings[python]>=0.28.0",
]

[tool.uv]
package = true
default-groups = ["dev", "test", "lint", "docs"]

[build-system]
build-backend = "uv_build"
requires = ["uv_build>=0.12.7,<0.13.0"]
```

---

## 3. Common Configuration Changes During Development

Follow these patterns to change `pyproject.toml` during development.

### A. Adding a New Dependency Group (PEP 735)

When adding a specialized group (for example, `benchmark` or `typing`):

1. Declare the group under `[dependency-groups]`:

   ```toml
   [dependency-groups]
   benchmark = [
       "pytest-benchmark>=5.1.0",
   ]
   ```

2. If the group must install automatically during local `uv sync`, add it to
   `default-groups`:

   ```toml
   [tool.uv]
   default-groups = ["dev", "test", "lint", "docs", "benchmark"]
   ```

3. Run `uv sync` to lock and install.

### B. Changing Minimum Python Version

When raising or lowering the supported Python target:

1. Update `requires-python` in `pyproject.toml`:

   ```toml
   [project]
   requires-python = ">=3.13"
   ```

2. Re-resolve dependencies for the new minimum:

   ```bash
   uv lock --upgrade
   uv sync
   ```

### C. Pinning or Constraining an Indirect or Build Dependency

Use `constraint-dependencies` as a transitive CVE floor ledger when `uv audit`
reports a vulnerability. This keeps `project.dependencies` clean of indirect packages.
Use `override-dependencies` or `build-constraint-dependencies` when an upstream release breaks:

```toml
[tool.uv]
# Transitive security floor ledger (keeps [project.dependencies] clean)
constraint-dependencies = [
    "urllib3>=2.6.3",      # CVE-2026-XXXXX remediation floor
    "cryptography>=46.0.5",
]
override-dependencies = [
    "problematic-pkg==1.2.3",
]
build-constraint-dependencies = [
    "setuptools>=75.0.0",
]
required-version = ">=0.7.0"
```

### D. Configuring Private or Alternative Package Indexes

To pull proprietary packages or PyPI mirrors:

```toml
[[tool.uv.index]]
name = "internal"
url = "https://pypi.company.internal/simple"
explicit = true

[tool.uv.sources]
my-private-package = { index = "internal" }
```

### E. Packaging Mode (`package = true` Versus `package = false`)

- **Libraries & CLI apps** (`package = true`): Installs the current project
  in editable mode (`-e .`) into `.venv`.
- **Scripts & Monorepo roots** (`package = false`): Treats directory solely
  as an environment container without building a root wheel.

### F. Supply Chain Protection with `exclude-newer` & `exclude-newer-package`

Astral `uv` supports an `exclude-newer` cutoff. It limits package resolution to
releases published before a given timestamp or relative age.
Use `exclude-newer-package` for package exemptions or exact RFC 3339 timestamps:

1. **In `pyproject.toml`**: Enforce a rolling stabilization window.
   Add exemptions (`false`) for internal packages or RFC 3339 timestamps for
   upstream hotfixes:

   ```toml
   [tool.uv]
   exclude-newer = "7 days"
   exclude-newer-package = {
       "my-internal-sdk" = false,
       "fast-moving-dep" = "2026-10-08T00:00:00Z",
   }
   ```

2. **In CI Workflows (`UV_EXCLUDE_NEWER`)**: Prevent zero-hour PyPI index propagation
   lag and guard against newly compromised releases:

   ```bash
   # Dynamic 1-hour cutoff in CI
   export UV_EXCLUDE_NEWER="1 hour ago"
   uv sync --only-group test
   ```

3. **In Ad-hoc CLI Operations**:

   ```bash
   uv lock --exclude-newer "7 days"
   ```

---

## 4. Guidelines and Gotchas

Follow these guidelines when you use `uv`:

- **Never edit versions directly in `uv.lock`**: Always update
  `pyproject.toml` and run `uv lock` or `uv add`.
- **Never invoke `pip` inside `uv` projects**: Running `pip install`
  bypasses `uv.lock` and creates un-reproducible environments.
- **Scope CI installs with `--only-group`**: In CI test matrices, run
  `uv sync --only-group test`. This prevents downloading documentation or
  linter binaries in test runners.
- **Audit dependencies regularly**: Run `uv run poe audit` (`uv audit`) to
  check `uv.lock` against published security advisories.
- **Group inclusions**: Use `{ include-group = "..." }` in composite groups
  like `dev` to keep logical tool sets modular and decoupled.
