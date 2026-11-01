---
diataxis: explanation
purpose: Introduce Debug Dojo, its core features, and provide an interactive terminal preview of enhanced Python debugging.
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

**debug-dojo** enhances Python debugging in the terminal. It pairs
[`rich`](https://github.com/Textualize/rich) terminal rendering with drop-in
shortcuts for side-by-side object comparison, formatted tracebacks, and
seamless switching between `ipdb`, `pudb`, `pdb`, and `debugpy`.

<!-- termynal -->
```console
# Install debug-dojo with all supported debuggers
$ uv add "debug-dojo[all-debuggers]"
---> 100%

# Run any script with zero imports - helpers b(), p(), i(), c() are ready
$ dojo run app.py

Using configuration model: DebugDojoConfigV3.
Using debug-dojo configuration:
DebugDojoConfigV3(debugger=ipdb, rich_traceback=True)

╭─────────────────────────────── <class 'dict'> ───────────────────────────────╮
│ {'service': 'api', 'port': 8080, 'active': True}                            │
╰──────────────────────────────────────────────────────────────────────────────╯

# Breakpoints stop directly in your configured debugger
ipdb> n
> /workspace/app.py(12)<module>()
-> result = handle_request(service)
ipdb> c
```

## Key Features

- **Zero-Boilerplate CLI (`dojo run`)**: Run any Python script, module, or test
  runner with debugging tools active without editing code.
- **Injected Debugging Helpers**: Call `b()` (breakpoint), `p()` (pretty print),
  `i()` (inspect object), and `c()` (side-by-side compare) anywhere in your session.
- **Side-by-Side Object Comparison**: Compare two objects side-by-side in formatted
  Rich tables to spot subtle differences instantly.
- **Multiple Debugger Backends**: Switch between IPDB, PuDB, PDB, or Debugpy (VS Code
  remote attach) via configuration or CLI flags.
- **Rich Tracebacks & Post-Mortem**: Format unhandled exceptions with highlighted
  source context and jump directly into a post-mortem REPL.
- **Declarative Configuration**: Configure default backends, tracebacks, and helper
  mnemonics through `dojo.toml` or `pyproject.toml`.

## Quick Start

### 1. Run with the CLI

Execute scripts, modules, or test runners directly:

```console
# Run a Python script
dojo run script.py

# Run a Python module
dojo run -m my_package.worker

# Run an executable tool with debugging tools active
dojo run -e pytest
```

Override configuration on demand:

```console
dojo run --debugger ipdb --verbose script.py
```

### 2. In-Code Activation

Import `debug_dojo.install` anywhere in your code to inject helper tools into Python's
`builtins`:

```python
import debug_dojo.install

# Inspect, compare, and break
data_a = {"user": "alice", "roles": ["admin"]}
data_b = {"user": "alice", "roles": ["viewer"]}

p(data_a)  # Pretty print with Rich
i(data_a)  # Inspect attributes and methods
c(data_a, data_b)  # Side-by-side comparison table
b()  # Trigger preconfigured debugger breakpoint
```

### Injected Helper Functions

| Shortcut        | Description             | Underlying Implementation                           |
| :-------------- | :---------------------- | :-------------------------------------------------- |
| `b()`           | Trigger breakpoint      | `sys.breakpointhook` configured to selected backend |
| `p(obj)`        | Pretty-print object     | `rich.print(obj)`                                   |
| `i(obj)`        | Detailed inspection     | `rich.inspect(obj, methods=True)`                   |
| `c(obj1, obj2)` | Side-by-side comparison | `debug_dojo._compare.inspect_objects_side_by_side`  |

## Installation

Install using `uv`:

```console
uv add debug-dojo
```

For all debugger backends (`debugpy`, `ipdb`, `pudb`), install the `all-debuggers`
extra:

```console
uv add "debug-dojo[all-debuggers]"
```

Using standard `pip`:

```console
pip install "debug-dojo[all-debuggers]"
```

> [!NOTE]
> Install `debug-dojo` in your project's active virtual environment rather than
> globally via `pipx` or `uvx`, so that it can resolve and import project dependencies.
