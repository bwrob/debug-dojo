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

[**debug-dojo**](https://bwrob.github.io/debug-dojo/) is a powerful Python package designed to streamline your debugging workflow directly from the terminal. It integrates seamlessly with popular debuggers and enhances your inspection capabilities with beautiful, readable output.

## ✨ Features

*   **Unified Debugging Interface:** Easily launch your scripts or modules with your preferred debugger (`debugpy`, `pudb`, `pdb`, `ipdb`).
*   **Enhanced Output with Rich:** Leverages [`rich`](https://github.com/Textualize/rich) for stunning, syntax-highlighted code, pretty-printed objects, and improved tracebacks.
*   **Side-by-Side Object Comparison:** Quickly identify differences between two Python objects.
*   **Interactive Object Inspection:** Dive deep into object structures with a powerful `inspect` utility.
*   **Simplified Breakpoints:** Set breakpoints effortlessly with a concise helper function.

## 🚀 Installation

Install `debug-dojo` using `pip`:

```bash
pip install debug-dojo
```

For full debugger support, you might want to install optional dependencies:

```bash
pip install "debug-dojo[all-debuggers]"
```

## 💻 CLI Usage

Run your Python script or module with `debug-dojo`:

```console
dojo my_script.py
```

Specify a debugger, configuration file, or enable verbose output:

```console
dojo --debugger ipdb --config dojo.toml --verbose --module my_module
```

Run an executable command with debugging tools:

```console
dojo --exec pytest
```

## 🐍 Usage in Code

Integrate `debug-dojo` directly into your Python code for on-demand debugging and inspection utilities:

```python
import debug_dojo.install

# Set a breakpoint and enter the debugger
# debug_dojo.install.b() # Equivalent to breakpoint()

object_1 = {"foo": 1, "bar": 2}
object_2 = [1, 2, 3]

# Pretty print an object with Rich
debug_dojo.install.p(object_1)

# Inspect an object using Rich
debug_dojo.install.i(object_1)

# Compare two objects side-by-side
debug_dojo.install.c(object_1, object_2)

# Enter the debugger (e.g., ipdb, pudb, pdb, debugpy based on config)
# debug_dojo.install.b()
```

## 📚 Documentation

For comprehensive instructions on installation, configuration, advanced usage, and API reference, please visit the [official documentation](https://bwrob.github.io/debug-dojo/).

## 🤝 Contributing

Contributions are welcome! Please refer to the [development guidelines](https://bwrob.github.io/debug-dojo/development/) for details on how to set up your development environment and submit changes.
