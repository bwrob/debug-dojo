---
description: Authoritative usage guidelines, patterns, and conventions for Debug Dojo. Use when writing, refactoring, or reviewing code using Debug Dojo.
name: debug-dojo
version: 0.9.0
---

# Debug Dojo Developer Guidelines

Authoritative engineering guidelines for working with `debug_dojo`.

## API Conventions

- Import debugging utilities directly from `debug_dojo.install`:
  ```python
  import debug_dojo.install

  # b() -> trigger configured breakpoint
  # p(obj) -> pretty-print object with Rich
  # i(obj) -> inspect object with Rich
  # c(obj1, obj2) -> side-by-side object comparison
  ```
- Command-line execution:
  ```bash
  dojo run my_script.py
  dojo run -m my_module
  dojo run -e pytest
  dojo run -d ipdb my_script.py
  ```
- Use strict typing across all function boundaries.
- Adhere to the core architectural patterns defined in `AGENTS.md`.

## Integration with AI Coding Assistants

This library bundles official agent skills directly inside its package distribution.
To discover and synchronize skills from this and other installed dependencies in your project:

```bash
uvx library-skills --all -y
```
