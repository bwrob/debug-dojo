---
diataxis: tutorial
purpose: Guide developers through running their first debug session with Debug Dojo, using dpdb commands, and inspecting objects.
---

# Getting Started

This tutorial guides you through running a Python script with **Debug Dojo**, inspecting
state inside the `dpdb` interactive debugger, and using injected helper functions.

## Prerequisites

Ensure you have Python 3.12+ and [`uv`](https://docs.astral.sh/uv/) installed.

## 1. Zero-Install CLI Debugging

With `debug-dojo`, you can execute any Python script via `uvx` while automatically
configuring `dpdb` and injecting inspection shortcuts into Python's `builtins`.

Create a sample script named `debug_demo.py`:

```python
"""Sample script demonstrating Debug Dojo builtins and dpdb."""

config_payload = {
    "server": "us-east-1",
    "retries": 3,
    "features": ["auth", "caching", "metrics"],
}

# Injected helpers are available without importing!
p(config_payload)
i(config_payload)
b()
```

Run the script using `uvx debug-dojo` (or `dojo` when installed):

<!-- termynal -->
```console
$ uvx debug-dojo debug_demo.py

# Output formatted by Rich pretty-print
{'server': 'us-east-1', 'retries': 3, 'features': ['auth', 'caching', 'metrics']}

# Output formatted by Rich inspect
╭─────────────────────────────── <class 'dict'> ───────────────────────────────╮
│ dict() -> new empty dictionary                                               │
│                                                                              │
│ ╭──────────────────────────────────────────────────────────────────────────╮ │
│ │ {'server': 'us-east-1', 'retries': 3, 'features': ['auth', 'caching'... │ │
│ ╰──────────────────────────────────────────────────────────────────────────╯ │
│                                                                              │
│      clear = def clear(...) D.clear() -> None.  Remove all items from D.     │
│       copy = def copy(...) D.copy() -> a shallow copy of D                   │
│      items = def items(...) D.items() -> a set-like object providing a view  │
│       keys = def keys(...) D.keys() -> a set-like object providing a view    │
╰──────────────────────────────────────────────────────────────────────────────╯

# b() stops execution in dpdb
dpdb> p config_payload['server']
'us-east-1'
dpdb> c
```

## 2. Comparing Objects Side-by-Side

Use the `c(obj1, obj2)` helper to compare two dictionaries, objects, or data models.
Differences are displayed in a formatted side-by-side terminal table.

<!-- termynal -->
```console
$ python -c "import debug_dojo.install; c({'a': 1, 'b': 2}, {'a': 1, 'b': 3})"

┌───────────────────────────────────────┬──────────────────────────────────────┐
│ ╭───────────────────────────────────╮ │ ╭──────────────────────────────────╮ │
│ │ <class 'dict'>                    │ │ │ <class 'dict'>                   │ │
│ │                                   │ │ │                                  │ │
│ │ Value:                            │ │ │ Value:                           │ │
│ │   {'a': 1, 'b': 2}                │ │ │   {'a': 1, 'b': 3}               │ │
│ │                                   │ │ │                                  │ │
│ │ No attributes or methods to       │ │ │ No attributes or methods to      │ │
│ │ display for this type.            │ │ │ display for this type.           │ │
│ ╰───────────────────────────────────╯ │ ╰──────────────────────────────────╯ │
└───────────────────────────────────────┴──────────────────────────────────────┘
```

## 3. In-Code Activation

When running tests or scripts where you do not use the `debug-dojo` CLI runner, import
`debug_dojo.install` once in your module or test fixture:

```python
import debug_dojo.install

# The following helpers are now globally accessible:
# - b(): Enter the dpdb debugger
# - p(obj): Rich pretty-print
# - i(obj): Rich object inspection
# - c(obj1, obj2): Side-by-side comparison table
```

You can also use the `pdb` / `ipdb`-compatible top-level API or set
`PYTHONBREAKPOINT=debug_dojo.set_trace`:

```python
import debug_dojo

debug_dojo.set_trace()
```

## 4. Automatic Post-Mortem Debugging

When `debug-dojo` encounters an unhandled exception, it renders the traceback and crash
banner with Rich and enters a `dpdb` post-mortem debugging session at the exact frame
where the failure occurred:

<!-- termynal -->
```console
$ uvx debug-dojo failing_script.py

<b>Error while running failing_script.py:</b>
ZeroDivisionError: division by zero

Traceback (most recent call last):
  File "/workspace/failing_script.py", line 4, in <module>
    compute(0)
  File "/workspace/failing_script.py", line 2, in compute
    return 100 / divisor
           ^^^^^^^^^^^^^
ZeroDivisionError: division by zero

<b>Entering post-mortem debugging session...</b>
╭──────────── Dojo Post-Mortem — ZeroDivisionError ────────────╮
│ ZeroDivisionError: division by zero                          │
│ Location: /workspace/failing_script.py:2 in compute()        │
╰──────────────────────────────────────────────────────────────╯
> /workspace/failing_script.py(2)compute()
----> 2     return 100 / divisor
  ↳ Line: divisor=0
dpdb> p divisor
0
dpdb> q
```

## Architecture & Lifecycles

The diagrams below describe how `debug-dojo` sets up the debugging environment,
executes targets, and manages failure states.

### Component Architecture

```mermaid
flowchart TD
    CLI["debug-dojo / dojo CLI"] --> INSTALLER["Installers (_installers.py)"]
    INSTALLER --> BUILTINS["Python builtins (b, p, i, c)"]
    INSTALLER --> HOOK["sys.breakpointhook (dpdb.set_trace)"]
    CLI --> EXEC["Target Execution (_execution.py)"]
    BUILTINS --> EXEC
    HOOK --> EXEC
    EXEC -->|Unhandled Exception| PM["dpdb Post-Mortem (dpdb.post_mortem)"]
```

### Execution Lifecycle

```mermaid
sequenceDiagram
    autonumber
    actor Dev as Developer
    participant CLI as debug-dojo CLI
    participant Inst as Tool Installer
    participant Target as Target Script
    participant Dpdb as dpdb Debugger

    Dev->>CLI: uvx debug-dojo script.py
    CLI->>Inst: install_tools()
    Inst->>Inst: Inject b, p, i, c into builtins
    Inst->>Dpdb: Configure sys.breakpointhook
    CLI->>Target: Execute via runpy
    Target->>Dpdb: b() or breakpoint() triggered
    Dpdb-->>Dev: Interactive dpdb> Prompt
```

### State Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Initializing: Invoke debug-dojo
    Initializing --> InjectingTools: Install b, p, i, c & dpdb hook
    InjectingTools --> RunningTarget: Execute script / module / exec
    RunningTarget --> Completed: Script exits successfully
    RunningTarget --> PostMortem: Unhandled exception raised
    PostMortem --> Terminated: Developer exits dpdb
    Completed --> [*]
    Terminated --> [*]
```

## Development Workflow

To contribute to Debug Dojo, clone the repository and synchronize the environment:

```console
git clone https://github.com/bwrob/debug-dojo.git
cd debug-dojo
uv sync
```

Run tests and verification tasks using Poe the Poet:

```console
# Run unit tests with coverage
uv run poe test

# Run all code quality checks
uv run poe code-quality

# Preview documentation locally
uv run poe docs-serve
```

> [!TIP]
> When browsing docs, press ++slash++ or ++cmd+k++ (or ++ctrl+k++ on Linux/Windows) to
> search documentation symbols and pages. Hovering internal links activates floating
> previews.
