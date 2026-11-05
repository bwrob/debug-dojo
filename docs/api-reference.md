---
diataxis: reference
purpose: Document Python APIs, the dpdb debugger module, installer functions, execution engine, and comparison utilities.
---

# API Reference

Technical reference for public modules, CLI commands, and internal core subsystems.

## Public Interface

Public modules and entrypoints designed for direct consumption:

### Package Root

::: debug_dojo

### In-Code Installer

::: debug_dojo.install

### Command Line Interface

::: debug_dojo.cli

## Architecture Dependency Graph

The internal module boundaries and import hierarchy are strictly enforced by
[Tach](https://github.com/gauge-sh/tach):

```mermaid
--8<-- "docs/dependency_graph.mmd"
```

## Internal Core Subsystems

Detailed API documentation for internal modules isolated under `debug_dojo._core`:

### Debugger Subsystem

::: debug_dojo._core.debugger.debugger

::: debug_dojo._core.debugger.breakpoints

::: debug_dojo._core.debugger.session

::: debug_dojo._core.debugger.views

### Installer Subsystem

::: debug_dojo._core.installers

### Execution Subsystem

::: debug_dojo._core.execution

### Comparison Subsystem

::: debug_dojo._core.compare
