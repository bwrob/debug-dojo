# Style Guide & Development Conventions

To maintain high code quality and consistency, `debug-dojo` adheres to strict development conventions enforced by modern Python tooling.

## Core Principles

- **Strict Typing**: All code must be fully typed and pass `basedpyright` in strict mode.
- **Automated Formatting**: Code style is enforced by `ruff format` (Black-compatible, 88 char line limit).
- **Comprehensive Linting**: `ruff` is used with the `ALL` rule set (with minimal exceptions) to ensure code quality.
- **Test-Driven**: Changes must be accompanied by comprehensive tests using `pytest`.
- **Minimal Dependencies**: We strive for minimal and light dependencies. Larger or specialized dependencies should be offered as optional extras.

## Tooling & Workflow

The project uses `uv` for dependency management and `poethepoet` for task automation. Before submitting any changes, ensure all quality checks pass:

```bash
poe precommit
```

This command runs all essential checks: formatting, linting, and type checking. For auto-fixing issues:

```bash
poe fix
```

Individual checks can be run via:
- **Format**: `poe format`
- **Lint**: `poe lint`
- **Type Check**: `poe type-check`
- **Test**: `poe test` (for running tests) or `poe coverage` (for coverage report).

## Git Conventions

We follow a variation of **Conventional Commits**:

- **Format**: `type: subject`
- **Common Types**: `feat:`, `fix:`, `docs:`, `dev:`, `test:`, `refactor:`.

**Example**:
```text
docs: document 'all-debuggers' optional dependency
dev: separate tool configs
```
