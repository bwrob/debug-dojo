---
diataxis: reference
purpose: Document Python APIs, installer functions, comparison utilities, and configuration models.
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

### Installer Submodule

::: debug_dojo._installers

### Comparison Submodule

::: debug_dojo._compare

### Configuration Loader Submodule

::: debug_dojo._config

### Configuration Models Submodule

::: debug_dojo._config_models

### Command Line Interface Submodule

::: debug_dojo._cli
