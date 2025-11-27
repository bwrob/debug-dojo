# debug dojo

<p align="center">
  <img src="https://github.com/bwrob/debug-dojo/blob/main/docs/logo/banner.png?raw=true" alt="debug dojo" style="width:100%; max-width:800px;"/>
</p>

<p align="center">
<em>🏣 debug dojo, a place for zen debugging</em>
</p>

[![PyPi Version](https://img.shields.io/pypi/v/debug-dojo.svg?style=flat-square)](https://pypi.org/project/debug-dojo)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/debug-dojo.svg?style=flat-square)](https://pypi.org/pypi/debug-dojo/)
[![downloads](https://static.pepy.tech/badge/debug-dojo/month)](https://pepy.tech/project/debug-dojo)
[![license](https://img.shields.io/github/license/bwrob/debug-dojo.svg)](https://github.com/bwrob/debug-dojo/blob/main/LICENSE)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/bwrob/debug-dojo/main.svg)](https://results.pre-commit.ci/latest/github/bwrob/debug-dojo/main)


**debug-dojo** is a Python package providing utilities for enhanced
debugging and inspection in the terminal. It leverages
[`rich`](https://github.com/Textualize/rich) for beautiful output and
offers helpers for side-by-side object comparison, improved tracebacks
from `rich`, and easy integration with different debuggers -- `debugpy`,
`pudb`, `pdb`, and `ipdb`.

## Features

- **Convenient CLI** Quickly run your code with debugging tools
    enabled.
- **Simple API:** Install all tools or only what you need.
- **Debugger integration:** Quickly enable Debugpy, PuDB, PDB, or IPDB
    as your default pre-configured debugger.
- **Rich tracebacks:** Get readable, colorized tracebacks for easier
    debugging.
- **Side-by-side object inspection:** Visually compare Python objects,
    their attributes, and methods in the terminal.
- **Configuration:** Easily configure the debugging tools using
    `dojo.toml` or `pyproject.toml`.

## Usage

### CLI

Run your Python script with debugging tools enabled using the
`debug-dojo` command:

``` console
dojo my_script.py
```

You can optionally set configuration, verbose mode, and specify the
debugger type. Both script files and modules are supported:

``` console
dojo --debugger ipdb --config dojo.toml --verbose --module my_module
```

dojo can let you debug into:

- any Python script -- `dojo my_script.py`
- any runnable module -- `dojo -m my_module`
- or even an executable, `dojo -e my_executable` (like `pytest`)

### From the code

In the `PuDB` style, you can install all debugging tools and enter the
debugging mode with a single command:

``` python
object_1 = {"foo": 1, "bar": 2}
object_2 = [1, 2, 3]

import debug_dojo.install; b()
p(object_1)  # Pretty print an object with Rich
```

### Features in debugging mode (when `debug_dojo.install` is used)

When you use `import debug_dojo.install; b()`, the following convenience functions are injected into Python's builtins, making them globally available within your debugging session:

- `b()`: Sets a breakpoint using the debugger configured in `debug-dojo`. This is equivalent to calling `breakpoint()` but respects your `debug-dojo` debugger settings.
- `p(obj)`: Pretty prints an object using `rich.print`, providing enhanced readability for complex data structures.
- `i(obj)`: Inspects an object using `rich.inspect`, offering a detailed, colorized view of its attributes and methods.
- `c(obj1, obj2)`: Compares two Python objects side-by-side using `debug-dojo`'s comparison utility, highlighting differences for easier debugging.

## Installation

The package is available on PyPI and can be installed using standard
Python package management tools.

``` console
pip install debug-dojo
```

For full debugger support, you might want to install optional dependencies:

```bash
pip install "debug-dojo[all-debuggers]"
```

You can also use `poetry` or `uv` to add it to your project:

``` console
poetry add debug-dojo
```

``` console
uv add debug-dojo
```

Note that dojo most likely will not work when installed via `pipx` or
`uvx`, as it relies on the current Python environment dependencies.
