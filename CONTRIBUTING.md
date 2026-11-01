# Contributing to Debug Dojo

Thank you for your interest in contributing to **Debug Dojo**! We
welcome contributions that maintain our high standards of type safety, performance, test
coverage, and clean architecture.

## 1. Governance & AI Policy

- **Human Accountability**: All contributors are responsible for the code they submit.
  Please review our [Code of Conduct](CODE_OF_CONDUCT.md).
- **AI Coding Assistants**: We support responsible AI assistance under strict conditions
  (mandatory human review, local testing verification, transparent disclosure, and no
  unattended bots). Consult [AI_POLICY.md](AI_POLICY.md) before submitting AI-assisted
  contributions.
- **Agent Guidelines**: Coding agents working in this repository must follow the
  conventions defined in [AGENTS.md](AGENTS.md).

## 2. Development Setup

We standardize on **`uv`** for dependency and environment management.

### Prerequisites

1. Python `3.12` or later.
2. `uv` (`curl -LsSf https://astral.sh/uv/install.sh | sh`).

### Bootstrap Environment

```bash
# Clone repository
git clone \
  https://github.com/bwrob/debug-dojo.git
cd debug-dojo

# Synchronize all dependency groups inside managed virtual environment
uv sync

# Install git pre-commit hooks
uv run prek install
```

## 3. Development Workflow & Tasks

Development commands are managed via **Poe the Poet**:

| Task                 | Command                   | Purpose                                                |
| :------------------- | :------------------------ | :----------------------------------------------------- |
| **Run Tests**        | `uv run poe test`         | Run pytest suite with coverage measurement             |
| **Fast Tests**       | `uv run poe test-fast`    | Run tests in parallel across CPU cores                 |
| **Run Quality Gate** | `uv run poe code-quality` | Run lint, format-check, types, complexity, typos, Tach |
| **Auto-Fix**         | `uv run poe fix`          | Auto-format with Ruff, fix typos, format markdown      |
| **Type Check**       | `uv run poe type-check`   | Static type analysis with Pyrefly                      |
| **Serve Docs**       | `uv run poe docs-serve`   | Launch live Zensical documentation preview             |
| **Interactive REPL** | `uv run poe repl`         | Launch Python REPL with package pre-imported           |

## 4. Branching & Commit Hygiene

- **Branch Naming**: Use descriptive prefixes: `feat/<name>`, `fix/<name>`,
  `docs/<name>`, `refactor/<name>`, or `chore/<name>`.
- **Conventional Commits**: Format commit messages according to the Conventional Commits
  specification:

  ```text
  <type>(<scope>): <short imperative description>

  [optional body explaining motivation and context]
  ```

- **Co-authorship**: If AI assistants contributed to code generation, credit them with
  standard git trailers:

  ```text
  Co-authored-by: Claude <noreply@anthropic.com>
  ```

## 5. Pre-Submission Verification Gate

Before pushing changes or opening a pull request, always ensure the complete
verification gate passes cleanly:

```bash
uv run poe test
uv run poe code-quality
uv run prek run --all-files
```

Pull requests will run the full CI matrix across Linux, macOS, and Windows.
