---
description: >
  Sets up, bootstraps, or fixes the local Python development environment:
  a uv-managed virtual environment, dependency groups, pre-commit hooks, and
  initial verification runs. Runs only when explicitly requested.
  Use when asked to set up or fix a development checkout.
  Use to install project dependencies, fix a missing or broken .venv,
  or prepare a machine for contributing. Do not use for routine code editing
  or individual test runs.
disable-model-invocation: true
name: workflow-setup
version: 1.0.0
---

# Project Setup & Bootstrap (`workflow-setup`)

This skill defines the process to set up, configure, and fix
a local development environment for this Python project.

> [!IMPORTANT]
> This skill operates with `disable-model-invocation: true`. Execute these
> commands only when the user explicitly asks to set up or fix the environment.

---

## 1. Prerequisites

Before you set up the environment, check that required system tools are available:

1. **Python 3.12+**:
   ```bash
   python3 --version
   ```

2. **uv (Astral)**:
   ```bash
   uv --version
   ```
   If your system lacks `uv`, install it with the official script:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

---

## 2. Environment Bootstrap Procedure

Run these steps from the repository root:

### Step 1: Synchronize Virtual Environment & Dependencies

Install all declared dependency groups in a virtual environment with `uv`:

```bash
uv sync
```

This command creates `.venv/` and syncs all packages defined in `uv.lock`.

### Step 2: Install Git Prek Hooks

Install git hooks via prek to run verification before commits:

```bash
uv run prek install
```

### Step 3: Run Baseline Quality Verification

Check that all linters, static type checkers, and complexity checks pass cleanly:

```bash
uv run poe code-quality
```

### Step 4: Run Automated Test Suite

Run unit tests and check coverage thresholds:

```bash
uv run poe test
```

### Step 5: Check Wheel Artifact Pre-Flight

Check that packages build cleanly and all modules import in an isolated environment:

```bash
uv run poe verify-wheel
```

---

## 3. Essential Command Reference

| Workflow | Command | Purpose |
| :--- | :--- | :--- |
| **Sync Environment** | `uv sync` | Synchronize virtual environment with lockfile |
| **Add Runtime Dependency** | `uv add <pkg>` | Add package to `[project.dependencies]` |
| **Add Dev Dependency** | `uv add --group <group> <pkg>` | Add package to specific dependency group |
| **Run Poe Tasks** | `uv run poe <task>` | Run declared development tasks via Poe |
| **Format & Lint** | `uv run poe fix` | Auto-format with Ruff and fix typos |
| **Run Quality Gate** | `uv run poe code-quality` | Run full static verification pipeline |
| **Run Test Suite** | `uv run poe test` | Run pytest with coverage thresholds |
| **Smoke Test Wheel** | `uv run poe verify-wheel` | Check built wheel in isolated environment |
| **Preview Documentation** | `uv run poe docs-serve` | Run live Zensical docs server |

---

## 4. Troubleshooting & Recovery

### Missing or Corrupted Virtual Environment

If `.venv/` breaks or becomes inconsistent:

```bash
rm -rf .venv
uv sync
```

### Dependency Cache Desynchronization

If you must refresh the dependency cache from PyPI:

```bash
uv sync --refresh
```

### Prek Hook Cache Issues

To reset prek hook environments:

```bash
uv run prek clean
uv run prek install --install-hooks
```
