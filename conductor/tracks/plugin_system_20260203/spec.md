# Specification: Plugin System

## Overview
Design and implement a plugin architecture. Users should be able to define custom helper functions (like `my_helper()`) that get injected into the debugging namespace alongside standard helpers like `i()` and `c()`. Plugins could also potentially hook into lifecycle events.

## Requirements
- Define a plugin interface/structure (entry points or file-based).
- specific directory for user plugins (e.g., `~/.debug-dojo/plugins`).
- Load and validate plugins at startup.
- Inject plugin callables into the debug context.
