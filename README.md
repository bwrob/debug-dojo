#

<p align="center">
  <img src="https://github.com/bwrob/debug-dojo/blob/main/docs/logo/banner.png?raw=true" alt="debug dojo" style="width:100%;"/>
</p>

<p align="center">
<em>🏣 debug dojo, a place for zen debugging</em>
</p>

<p align="center">
  <a href="https://pypi.org/project/debug-dojo">
    <img src="https://img.shields.io/pypi/v/debug-dojo.svg?style=flat-square" alt="PyPi Version">
  </a>
  <a href="https://pypi.org/pypi/debug-dojo/">
    <img src="https://img.shields.io/pypi/pyversions/debug-dojo.svg?style=flat-square" alt="PyPI pyversions">
  </a>
  <a href="https://pepy.tech/project/debug-dojo">
    <img src="https://static.pepy.tech/badge/debug-dojo/month" alt="downloads">
  </a>
  <a href="https://github.com/bwrob/debug-dojo/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/bwrob/debug-dojo.svg" alt="license">
  </a>
  <a href="https://results.pre-commit.ci/latest/github/bwrob/debug-dojo/main">
    <img src="https://results.pre-commit.ci/badge/github/bwrob/debug-dojo/main.svg" alt="pre-commit.ci status">
  </a>
</p>

[**debug-dojo**](https://bwrob.github.io/debug-dojo/) is a standalone,
zero-configuration Python debugger and runner built around `dpdb`—an IPython-powered
interactive debugger with [`rich`](https://github.com/Textualize/rich) terminal panels,
inline variable diffs, and built-in object inspection.

## ✨ Features

- **Zero-Install & Zero-Config:** Run any script directly with
  `uvx debug-dojo script.py`. Automatically discovers your project's `.venv` and leaves
  no configuration, cache, or history files behind.
- **Opinionated `dpdb` Debugger:** Combines IPython tab completion and syntax
  highlighting with Rich tables (`w`, `a`, `b`, `display`, `h`), panels (`whatis`,
  `psource`, `pinfo`), adaptive source context, and an inline frame context banner
  (`Δ Changed`, `↳ Line`, `↩ Return`, `👁 Watch`).
- **Automatic Post-Mortem:** Unhandled exceptions render a Rich traceback and drop
  directly into a `dpdb` post-mortem session at the failing frame.
- **Built-in Inspection Shortcuts:** Injects `b()` (breakpoint), `p(obj)` (Rich print),
  `i(obj)` (Rich inspect), and `c(obj1, obj2)` (side-by-side comparison) into
  `builtins`.

## 🚀 Quick Start

Run any Python script directly with `uvx`:

```bash
uvx debug-dojo my_script.py
```

Or install `debug-dojo` into an environment with `uv`:

```bash
uv pip install debug-dojo
```

## 💻 CLI Usage

Run a Python script, executable command, or module directly with `debug-dojo` (or the
`dojo` alias), optionally seeding breakpoints from the command line without editing the
file:

```console
debug-dojo my_script.py arg1 arg2
debug-dojo -b 42 -b process_data my_script.py
debug-dojo pytest -k test_feature
debug-dojo my_package.my_module
```

## 🐍 Usage in Code

Import `debug_dojo.install` in your Python code to configure `dpdb` and inject helpers
(`b`, `p`, `i`, `c`) into `builtins`:

```python
import debug_dojo.install

object_1 = {"foo": 1, "bar": 2}
object_2 = [1, 2, 3]

# Pretty print an object with Rich
p(object_1)

# Inspect an object using Rich
i(object_1)

# Compare two objects side-by-side
c(object_1, object_2)

# Enter the dpdb debugger
# b()
```

Or use the standard `pdb` / `ipdb`-compatible top-level functions and
`PYTHONBREAKPOINT` hook directly:

```python
import debug_dojo

debug_dojo.set_trace()
# debug_dojo.post_mortem()
# debug_dojo.pm()
```

## 📚 Documentation

For CLI flags, `dpdb` interactive commands, and API reference, visit the
[official documentation](https://bwrob.github.io/debug-dojo/).

## 🤝 Contributing

Contributions are welcome! Refer to the
[development guidelines](https://bwrob.github.io/debug-dojo/getting-started/#development-workflow)
for instructions on setting up the development environment and running verification
checks.
