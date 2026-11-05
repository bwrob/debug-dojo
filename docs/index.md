---
diataxis: explanation
purpose: Introduce Debug Dojo, its standalone dpdb debugger, and provide an interactive terminal preview of Python debugging.
---

<p align="center">
  <img src="https://github.com/bwrob/debug-dojo/blob/main/docs/logo/banner.png?raw=true" alt="debug dojo" style="width:100%;"/>
</p>

<p align="center">
<em>🏣 debug dojo, a place for zen debugging</em>
</p>

[![PyPi Version](https://img.shields.io/pypi/v/debug-dojo.svg?style=flat-square)](https://pypi.org/project/debug-dojo)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/debug-dojo.svg?style=flat-square)](https://pypi.org/pypi/debug-dojo/)
[![downloads](https://static.pepy.tech/badge/debug-dojo/month)](https://pepy.tech/project/debug-dojo)
[![license](https://img.shields.io/github/license/bwrob/debug-dojo.svg)](https://github.com/bwrob/debug-dojo/blob/main/LICENSE)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/bwrob/debug-dojo/main.svg)](https://results.pre-commit.ci/latest/github/bwrob/debug-dojo/main)

**debug-dojo** is a standalone, opinionated Python debugger and script runner powered by
`dpdb`. It combines an IPython debugging shell with
[`rich`](https://github.com/Textualize/rich) terminal panels, inline variable change
tracking, post-mortem crash inspection, and built-in shortcuts for side-by-side object
comparison.

<!-- termynal -->
```console
# Run any script directly with uvx — zero configuration required
$ uvx debug-dojo app.py

╭─────────────────────────────── <class 'dict'> ───────────────────────────────╮
│ {'service': 'api', 'port': 8080, 'active': True}                            │
╰──────────────────────────────────────────────────────────────────────────────╯

# Breakpoints stop in dpdb with inline variable context
dpdb> n
> /workspace/app.py(12)<module>()
     10     service = {"service": "api", "port": 8080}
     11     b()
----> 12     result = handle_request(service)
  ↳ Line: service={'service': 'api', 'port': 8080}
dpdb> c
```

## Key Features

- **Zero-Config Runner (`uvx debug-dojo script.py`)**: Run scripts, modules, or commands
  immediately. Automatically discovers your project's `.venv` and leaves no
  configuration files, cache, or history behind.
- **Built-in `dpdb` Debugger**: Extends IPython's terminal debugger with Rich call
  stacks (`w`), function argument tables (`a`), object inspection (`pinfo`, `whatis`,
  `psource`), adaptive source context, and a live bottom keybinding toolbar.
- **Inline Frame Context Banner**: Displays modified local variables (`Δ Changed:`),
  active-line variable values (`↳ Line:`), return values (`↩ Return:`), and watched
  expressions (`👁 Watch:`) on every step.
- **Opinionated Debugging Helpers**: Call `b()` (breakpoint), `p()` (pretty print),
  `i()` (inspect object), and `c()` (side-by-side compare) anywhere in your code.
- **Rich Tracebacks & Post-Mortem**: Formats unhandled exceptions with highlighted
  source context and enters a `dpdb` post-mortem session at the crash location.

## Quick Start

### 1. Run with the CLI

Execute scripts, modules, or test runners directly:

```console
# Run a Python script with uvx
uvx debug-dojo script.py

# Run with the installed dojo alias
dojo script.py

# Run an importable Python module
dojo my_package.worker

# Run an executable command with debugging tools active
dojo pytest

# Set initial breakpoints from the CLI
dojo -b 42 -b handle_request app.py
```

### 2. In-Code Activation

Import `debug_dojo.install` anywhere in your code to configure `dpdb` and inject helper
tools into Python's `builtins`:

```python
import debug_dojo.install

# Inspect, compare, and break
data_a = {"user": "alice", "roles": ["admin"]}
data_b = {"user": "alice", "roles": ["viewer"]}

p(data_a)  # Pretty print with Rich
i(data_a)  # Inspect attributes and methods
c(data_a, data_b)  # Side-by-side comparison table
b()  # Trigger dpdb breakpoint
```

### Injected Helper Functions

| Shortcut        | Description             | Underlying Implementation                               |
| :-------------- | :---------------------- | :------------------------------------------------------ |
| `b()`           | Trigger breakpoint      | `debug_dojo.set_trace` via `breakpoint()`               |
| `p(obj)`        | Pretty-print object     | `rich.print(obj)`                                       |
| `i(obj)`        | Detailed inspection     | `rich.inspect(obj, methods=True, private=True)`         |
| `c(obj1, obj2)` | Side-by-side comparison | `debug_dojo._core.compare.inspect_objects_side_by_side` |

## Installation

Run directly without installation using `uvx`:

```console
uvx debug-dojo script.py
```

Or install into a virtual environment with `uv`:

```console
uv pip install debug-dojo
```
