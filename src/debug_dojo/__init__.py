"""Opinionated Python debugger and runner powered by `dpdb` and Rich.

Importing `debug_dojo.install` injects debugging tools into Python's builtins:

```python
import debug_dojo.install

b()
```

This configures `dpdb` as the active debugger, installs debugging helpers
(`b()`, `p()`, `i()`, `c()`), and triggers a breakpoint.

You can also invoke `set_trace()`, `post_mortem()`, or `pm()` directly:

```python
import debug_dojo

debug_dojo.set_trace()
```

Or run target scripts, modules, or commands directly from the CLI:

```console
$ uvx debug-dojo target_script.py value_1
```
"""

from __future__ import annotations

from debug_dojo._core.debugger import pm, post_mortem, set_trace

__version__ = "0.10.0"
__all__ = ["__version__", "pm", "post_mortem", "set_trace"]
