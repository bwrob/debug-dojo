---
description: >-
  Guide for Cosmic Ray AST mutation testing in Python.
  Use when measuring test suite quality, finding survivor mutants, and verifying test assertion depth.
  Triggers: cosmic-ray, mutation testing, mutation, survivor, mutants, kill mutants.
name: tool-cosmic-ray
version: 1.0.0
---

# Cosmic Ray Mutation Testing (`tool-cosmic-ray`)

`cosmic-ray` is an AST mutation testing framework for Python. It modifies source
code syntax trees to introduce small defects. It runs tests against each
mutant and reports survivors that tests failed to catch.

This project uses `cosmic-ray` to verify that test suites test behavior, not only code
lines.

---

## 1. Core CLI Commands

Use these commands to initialize sessions, run mutations, and report results.

```bash
uv run cosmic-ray init cosmic-ray.toml session.sqlite   # Initialize mutation database
uv run cosmic-ray exec session.sqlite                   # Execute mutations across tests
uv run cosmic-ray dump session.sqlite                   # Print detailed JSON results
uv run cr-report session.sqlite                         # Generate summary survival report
```

This project connects distributed mutation testing to Poe:

```bash
uv run poe test-mutation-cosmic     # Run full distributed mutation suite
```

---

## 2. Configuration Location

Configure Cosmic Ray through **`cosmic-ray.toml`** at the project root:

```toml
[cosmic-ray]
module = "<package_name>"
python-version = "3.13"
timeout = 10.0
test-command = "pytest tests"

[cosmic-ray.distributor]
name = "local"
```

### Configuration Keys

- **`module`**: The top-level package to mutate.
- **`timeout`**: Maximum execution seconds allowed for each mutant before marking
  it killed.
- **`test-command`**: Command executed to test each mutant.
- **`distributor.name`**: Execution distributor engine (defaults to `local`).

---

## 3. Interpreting Mutation Results

Mutants fall into three primary outcomes:

- **Killed**: Tests failed when the mutant ran. The test caught the bug.
- **Survived**: Tests passed despite the defect. The test suite has a gap in its
  assertions.
- **Incompetent**: The mutant caused a syntax error or failed to load.

When mutants survive:
1. Identify the file and line number from `cr-report session.sqlite`.
2. Inspect the mutated operator (for example, inverted comparison or removed call).
3. Add a focused unit test that explicitly asserts the missing behavior.
