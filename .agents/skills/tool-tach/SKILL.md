---
description: >-
  Guide for Tach modular architecture and layer boundary tool.
  Use when validating module boundaries, preventing circular imports, and defining layer hierarchies.
  Triggers: tach, architecture, layers, boundaries, circular imports, tach.toml.
name: tool-tach
version: 1.0.0
---


# Tach Architecture & Boundary Linter (`tool-tach`)

`tach` is a fast architectural linter and dependency graph visualizer for
Python, written in Rust. It enforces modular boundaries, defines public
module interfaces, and guarantees that low-level domain layers never import
from high-level presentation or CLI layers.

This project configures `tach` to enforce clean acyclic layer separation and block
circular imports.

---

## 1. Core CLI Commands

Use these commands to check boundaries, show trees, and generate reports.

```bash
uv run tach check                  # Check internal module boundaries
uv run tach check --exact          # Fail on unused module dependencies
uv run tach show                   # Print terminal architecture tree
uv run tach show --mermaid         # Export dependency graph in Mermaid
uv run tach sync                   # Sync tach.toml to existing imports
uv run tach report                 # Generate health report
```

---

## 2. Configuration Location

Configure Tach through **`tach.toml`** at the project root:

```toml
# Source roots for Python import resolution
source_roots = ["src"]

# Boundary enforcement rules & ignore governance
exact = true
forbid_circular_dependencies = true
ignore_type_checking_imports = true

[rules]
unused_ignore_directives = "error"
require_ignore_directive_reasons = "error"

# Layer hierarchy (ordered from top to bottom)
# Higher layers can import from lower layers; lower cannot import upward.
layers = [
    "cli",
    "core",
]

# Module definitions and allowed dependencies
[[modules]]
path = "my_app.cli"
depends_on = ["my_app.core"]
layer = "cli"

[[modules]]
path = "my_app.core"
depends_on = []
layer = "core"
```

---

## 3. Common Configuration Changes During Development

Manage architectural layers, module dependencies, and public interfaces with these
patterns. Use Deptry for `pyproject.toml` dependency hygiene. The `dependencies` Poe
task runs both Tach and Deptry.

### A. Adding a New Architectural Layer

To add a new layer (such as `domain`, `adapters`, or `storage`):

1. Define the layer in the `layers` array in order of hierarchy:

   ```toml
   layers = [
       "cli",
       "services",
       "core",
   ]
   ```

2. Any module assigned to `cli` can import from `services` and `core`.
3. Modules in `services` can import from `core`, but never from `cli`.
4. Modules in `core` cannot import from `services` or `cli`.

### B. Adding a New Internal Module

When creating a new package or module inside `src/`:

```toml
[[modules]]
path = "my_app.storage"
depends_on = ["my_app.core"]
layer = "core"
```

### C. Declaring Public Interfaces (`[[modules.interfaces]]`)

To prevent external modules from importing private implementation details:

```toml
[[modules]]
path = "my_app.core"
depends_on = []
layer = "core"

[[modules.interfaces]]
expose = ["my_app.core.get_greeting", "my_app.core.GreetingConfig"]
```

Any attempt to import an unexposed symbol from outside `my_app.core` will
trigger a Tach interface violation error.

### D. Exporting Mermaid Architecture Diagrams to Documentation

This project defines a built-in task in `poe_tasks.toml` to export the current
dependency graph directly as a Mermaid diagram:

```bash
uv run poe dependency-graph
```

This generates `docs/dependency_graph.mmd`, which you can embed in docs.

### E. Suppressing False Positives or Temporary Migration Exceptions

When transitioning legacy code or handling dynamic runtime imports, always provide
an explicit architectural reason (enforced by `require_ignore_directive_reasons = "error"`):

```python
# tach-ignore(legacy-bridge): dynamic runtime import during migration
from my_app.cli import format_output
```

Or ignore a specific module path with reason:

```python
from my_app.cli import (
    format_output,
)  # tach-ignore[my_app.cli](circular-hook): deferred CLI hook
```

---

## 4. Architecture Guidelines

Follow these architecture guidelines:

- **Check boundaries with Poe**: Always run `uv run poe dependencies` before merging. The
  task runs Tach for internal boundaries and Deptry for declared dependencies.
- **Top-Down Only**: Imports must flow downwards through layers (`cli` $\to$
  `services` $\to$ `core`). Never allow `core` to import anything from `cli`.
- **Acyclic Enforcement**: Tach prevents circular dependency
  cycles. If Tach detects a cycle, extract shared interfaces into a lower-level
  protocol module.
