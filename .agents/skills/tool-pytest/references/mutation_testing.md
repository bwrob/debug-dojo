# Mutation Testing Reference (`mutmut` & `cosmic-ray`)

Mutation testing introduces deliberate synthetic faults (mutations) into source code to verify whether the test suite detects and fails on them. If a mutated statement does not cause at least one test to fail, the mutant **survived**, indicating a gap in test assertions.

This project supports both **`mutmut`** and **`cosmic-ray`**, each optimized for distinct operational needs.

---

## Tool Comparison: `mutmut` vs `cosmic-ray`

| Dimension | `mutmut` | `cosmic-ray` |
| :--- | :--- | :--- |
| **Primary Strength** | Fast developer iteration | Distributed, exhaustive test campaign |
| **Execution Model** | Direct AST mutation in local files/cache | SQLite-backed task distribution |
| **Dependencies** | Minimal (`parso`) | Extended (`sqlalchemy`, `libcst`, `aiohttp`) |
| **Configuration** | `[tool.mutmut]` in `pyproject.toml` | `cosmic-ray.toml` |
| **Best Used For** | Local TDD loops, pre-PR audits | Nightly builds, CI suites, large teams |
| **Poe Task** | `uv run poe test-mutation` | `uv run poe test-mutation-cosmic` |

---

## 1. `mutmut` Fast Mutation Testing

`mutmut` modifies Python AST trees and executes `pytest` targeting mutated modules.

### Configuration (`pyproject.toml`)

```toml
[tool.mutmut]
runner       = "pytest"
source_paths = ["src/"]
```

### Essential Commands

```bash
# Run mutation analysis against the entire package
uv run poe test-mutation

# Inspect surviving mutants
uv run mutmut show <mutant_id>

# Generate HTML report
uv run mutmut html
```

---

## 2. `cosmic-ray` Distributed Mutation Testing

`cosmic-ray` generates an explicit mutation plan inside an SQLite database and distributes mutant evaluations across independent worker processes.

### Configuration (`cosmic-ray.toml`)

```toml
[cosmic-ray]
module-path = "src/<package_name>"
timeout = 15.0
excluded-modules = []
test-command = "pytest"

[cosmic-ray.distributor]
name = "local"
```

### Essential Commands

```bash
# Initialize and execute full mutation run
uv run poe test-mutation-cosmic

# Generate terminal summary report
uv run cr-report session.sqlite

# Generate interactive HTML report
uv run cr-html session.sqlite > htmlcov/mutation.html
```

---

## Best Practices

1. **Target Core Modules**: Focus mutation testing on business logic and core mathematical algorithms (`src/<pkg>/core.py`) rather than CLI wrappers or boilerplate.
2. **Combine with Property Testing**: Pair `mutmut` with `hypothesis` property-based tests to achieve near-100% mutant kill rates on algorithmic transformations.
3. **Keep Timeouts Strict**: Ensure per-mutant execution timeouts (10–15s) prevent infinite loops in mutated conditional statements.
