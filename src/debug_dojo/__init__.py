"""Debugging tools for Python.

This module provides utilities to configure debugging backends (IPDB, PuDB,
PDB, Debugpy) and enhanced terminal inspection tools.

Importing `debug_dojo.install` injects debugging tools into Python's builtins:

```python
import debug_dojo.install

b()
```

This installs debugging helpers (`b()`, `p()`, `i()`, `c()`) and triggers a breakpoint.

You can also run target scripts or modules using the `dojo` command-line interface:

```console
$ dojo run --verbose target_script.py value1
```
"""

from __future__ import annotations

__version__ = "0.9.0"
__all__ = ["__version__"]
