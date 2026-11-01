---
description: >-
  Guide for complexipy cognitive complexity analyzer in Python.
  Use when checking, refactoring, or reducing cognitive and cyclomatic complexity.
  Triggers: complexipy, complexity, cognitive complexity, cyclomatic complexity.
name: tool-complexipy
version: 1.0.0
---

# complexipy Cognitive Complexity Analyzer (`tool-complexipy`)

`complexipy` is a cognitive complexity analyzer for Python written in Rust.
Legacy cyclomatic complexity only counts branches.
In contrast, **cognitive complexity** measures the mental effort
a reader needs to understand and maintain a function.

In this project, `complexipy` enforces a ceiling of **$\le 10$**
cognitive complexity per function across all source code.

---

## 1. Core CLI Commands

Analyze cognitive complexity across the repository or for specific files:

```bash
uv run complexipy src tests              # Check src and tests
uv run complexipy path/to/file.py        # Check a single file
uv run complexipy src -c 10              # Run with custom limit
uv run complexipy src --output-csv       # Export analysis to CSV
```

Run the check through Poe:

```bash
uv run poe complexity                    # Runs complexipy src tests
```

---

## 2. Configuration Location

Configure `complexipy` in `complexipy.toml` at the project root:

```toml
# Maximum cognitive complexity allowed per function (strict project threshold)
max_complexity = 10

# Paths and patterns to exclude from complexity analysis
exclude = [
    ".git",
    ".venv",
    "site",
    "dist",
    "build",
    "__snapshots__",
]
```

---

## 3. How Cognitive Complexity Increments

Cognitive complexity increments when code breaks the reader's linear flow:

1. **Structural increments**:
   - `if`, `elif`, `else` (+1)
   - `for`, `while` loops (+1)
   - `try`, `except` blocks (+1)
   - `match`, `case` statements (+1)
2. **Nesting penalties** (compounding cognitive load):
   - A conditional nested inside another conditional gains an extra +1
     for each nesting level.
   - Example: an `if` inside a `for` loop that is inside another `if` adds
     +3 (+1 base, +2 nesting).
3. **Boolean sequences**:
   - Chains of alternating boolean operators (`a and b or c`) increment
     complexity.

---

## 4. Refactoring Strategies to Satisfy $\le 10$ Limit

When `uv run poe complexity` fails on a function:

### Strategy 1: Early Returns / Guard Clauses

Flatten nested conditionals by returning early:

```python
# Low Complexity: Guard clauses keep complexity minimal
def process_user(user: User | None) -> str:
    if user is None:
        return "User not found"
    if not user.is_active:
        return "Inactive user"
    if not user.has_permission:
        return "Permission denied"
    return execute_action(user)
```

### Strategy 2: Extract Composable Helper Functions

Split nested sub-routines into focused, single-responsibility functions:

```python
def validate_record(item: dict[str, str]) -> bool:
    return bool(item.get("id"))


def parse_record(item: dict[str, str]) -> Record:
    return Record(id=item["id"])


def handle_records(records: list[dict[str, str]]) -> list[Record]:
    return [parse_record(r) for r in records if validate_record(r)]
```

### Strategy 3: Dictionary or Protocol Dispatch

Replace deep `if-elif-elif` chains or nested switches with a callable
mapping:

```python
HANDLERS: dict[str, ActionHandler] = {
    "create": handle_create,
    "update": handle_update,
    "delete": handle_delete,
}


def dispatch_action(action: str, payload: Payload) -> Result:
    handler = HANDLERS.get(action, handle_unknown)
    return handler(payload)
```

---

## 5. Common Configuration Changes

Adjust thresholds and exclusions in `complexipy.toml`:

### A. Adjusting Complexity Threshold

This project recommends a threshold of $\le 10$ for maintainability:

```toml
max_complexity = 12
```

### B. Adding Path Exclusions

To exclude generated files, migration scripts, or legacy modules:

```toml
exclude = [
    "src/legacy_adapter",
    "tests/fixtures",
]
```
