# debug-dojo

**debug-dojo** is a Python package providing utilities for enhanced debugging and inspection in the terminal. It leverages [`rich`](https://github.com/Textualize/rich) for beautiful output and offers helpers for side-by-side object comparison, improved tracebacks from `rich`, and easy integration with PuDB. All tools can be installed at once or individually, allowing for flexible debugging setups.

## Features

- **Simple API:** Install all tools or only what you need.
- **PuDB integration:** Quickly enable the PuDB TUI debugger.
- **Rich tracebacks:** Get readable, colorized tracebacks for easier debugging.
- **Side-by-side object inspection:** Visually compare Python objects, their attributes, and methods in the terminal.

## Installation

```sh
pip install debug-dojo
```

## Usage

### Install all debugging tools

In the `PuDB` style, you can install all debugging tools and enter the debugging mode with a single command:

```python
import debug_dojo.all; b()
```

Where`b()` is a builtin-injected function that sets a breakpoint using PuDB's `set_trace()`.
In the PuDB interface, you can use the following functions:

- `i(object_1)` to inspect an object.
- `c(object_1, object_2)` to compare two objects side-by-side.


### Use individual tools

```python
from debug_dojo import install_inspect, use_pudb, use_rich_traceback

install_inspect()         # Enable object inspection helpers
use_pudb()                # Set up PuDB as the debugger
use_rich_traceback()      # Enable Rich tracebacks
```

### Compare objects side-by-side

```python
from debug_dojo.compareres import inspect_objects_side_by_side

a = {"foo": 1, "bar": 2}
b = [1, 2, 3]
inspect_objects_side_by_side(a, b)
```

## Development

### Run tests

```sh
pytest
```

### Lint and type check

```sh
ruff check src/debug_dojo --fix
basedpyright src/debug_dojo
```

## License

MIT License

---

*Debugging made delightful!*