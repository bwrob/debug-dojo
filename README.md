# debug dojo

<p align="center">
  <img src="https://github.com/bwrob/debug-dojo/blob/main/docs/logo/logo_python.png?raw=true" alt="debug dojo" style="width:50%; max-width:350px;"/>
</p>

<p align="center">
<em>🏣 debug dojo, a place for zen debugging</em>
</p>

[![PyPi Version](https://img.shields.io/pypi/v/debug-dojo.svg?style=flat-square)](https://pypi.org/project/debug-dojo)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/debug-dojo.svg?style=flat-square)](https://pypi.org/pypi/debug-dojo/)
[![downloads](https://static.pepy.tech/badge/debug-dojo/month)](https://pepy.tech/project/debug-dojo)
[![license](https://img.shields.io/github/license/bwrob/debug-dojo.svg)](https://github.com/bwrob/debug-dojo/blob/main/LICENSE)

[**debug-dojo**](https://bwrob.github.io/debug-dojo/) is a Python package providing utilities for enhanced debugging and inspection in the terminal.
It leverages [`rich`](https://github.com/Textualize/rich) for beautiful output and offers helpers for side-by-side object comparison, improved tracebacks from `rich`, and easy integration with different debuggers -- `debugpy`, `pudb`, `pdb`, and `ipdb`.

## CLI usage

Run your Python script with debugging tools enabled using the `debug-dojo` command:

```console
dojo my_script.py
```

You can optionally set configuration, verbose mode, and specify the debugger type. Both script files and modules are supported:

```console
dojo --debugger ipdb --config dojo.toml --verbose --module my_module
```

## From the code

In the `PuDB` style, you can install all debugging tools and enter the debugging mode with a single command:

```python
object_1 = {"foo": 1, "bar": 2}
object_2 = [1, 2, 3]

import debug_dojo.install; b()

p(object_1)             # Pretty print an object with Rich.
i(object_1)             # Inspect an object using Rich.
c(object_1, object_2)   # Compare two objects side-by-side.

```

## Documentation

For instructions regarding installation, configuration and usage please visit [documentation](https://bwrob.github.io/debug-dojo/).
