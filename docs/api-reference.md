---
diataxis: reference
purpose: Document Python APIs, the dpdb debugger module, installer functions, execution engine, and comparison utilities.
---

# API Reference

::: debug_dojo

## Architecture Dependency Graph

The internal module boundaries and import hierarchy are strictly enforced by
[Tach](https://github.com/gauge-sh/tach):

```mermaid
--8<-- "docs/dependency_graph.mmd"
```

## Submodules

Detailed API documentation for internal modules:

### Debugger Submodule

::: debug_dojo._dpdb

### Installer Submodule

::: debug_dojo._installers

### Execution Submodule

::: debug_dojo._execution

### Comparison Submodule

::: debug_dojo._compare

### Command Line Interface Submodule

::: debug_dojo._cli
