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

[**debug-dojo**](https://bwrob.github.io/debug-dojo/) is a nimble, plug-and-play Python
package designed to streamline your debugging workflow directly from the terminal. Drop
it into any environment with `uv pip install debug-dojo`—with zero configuration files,
zero cache or history files left behind, and ready for any debugger.

## ✨ Features

- **Plug-and-Play & Zero Traces:** Add to any environment at any point. Leaves no
  configuration files, cache, or history behind.
- **Debugger Agnostic:** Ready for any debugger (`pdb`, `ipdb`, `pudb`, `debugpy`)
  without enforcing one.
- **CLI-Driven Control:** Pass all runtime options directly via command-line flags.
- **Enhanced Output with Rich:** Leverages [`rich`](https://github.com/Textualize/rich)
  for syntax-highlighted code, pretty-printed objects, and formatted tracebacks.
- **Side-by-side Object Comparison:** Quickly identify differences between two Python
  objects with `c(obj1, obj2)`.
- **Interactive Object Inspection & Breakpoints:** Inspect objects deeply with `i(obj)`,
  pretty-print with `p(obj)`, and trigger breakpoints effortlessly with `b()`.

## 🚀 Installation

Add `debug-dojo` to any environment using `uv`:

```bash
uv pip install debug-dojo
```

To install alongside optional third-party debuggers (`ipdb`, `pudb`, `debugpy`):

```bash
uv pip install "debug-dojo[all-debuggers]"
```

## 💻 CLI Usage

Run your Python script or module with `dojo run`:

```console
dojo run my_script.py
```

Specify a debugger or enable verbose output via CLI flags:

```console
dojo run --debugger ipdb --verbose --module my_module
```

Run an executable command with debugging tools:

```console
dojo run --exec pytest
```

## 🐍 Usage in Code

Import `debug_dojo.install` directly in your Python code to inject helpers (`b`, `p`,
`i`, `c`) into `builtins`:

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

# Enter the debugger
# b()
```

## 📚 Documentation

For comprehensive instructions on installation, CLI flags, advanced usage, and API
reference, please visit the
[official documentation](https://bwrob.github.io/debug-dojo/).

## 🤝 Contributing

Contributions are welcome! Please refer to the
[development guidelines](https://bwrob.github.io/debug-dojo/getting-started/#development-workflow)
for details on how to set up your development environment and submit changes.
