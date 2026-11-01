---
diataxis: reference
purpose: Document command-line syntax, flags, subcommands, and exit codes for the dojo CLI.
---

# CLI Reference

The `dojo` command-line interface provides an opinionated, plug-and-play runner to
execute Python code with debugging tools pre-installed.

<!-- termynal -->
```console
$ dojo --help

<b>Usage: </b><b>dojo [OPTIONS] COMMAND [ARGS]...</b>

Run a Python script or module with debugging tools installed.

╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --install-completion          Install completion for the current shell.      │
│ --show-completion             Show completion for the current shell.         │
│ --help                        Show this message and exit.                    │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ───────────────────────────────────────────────────────────────────╮
│ run     Run a Python script or module with debugging tools installed.        │
╰──────────────────────────────────────────────────────────────────────────────╯

# Display help for the run command
$ dojo run --help

<b>Usage: </b><b>dojo run [OPTIONS] [TARGET]</b>

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   target      <str>  The target script or module to debug.                   │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --debugger  -d      <debugpy|ipdb|pdb|pudb>  Specify the debugger to use     │
│ --verbose   -v                               Enable verbose output           │
│ --module    -m                               Run a module                    │
│ --exec      -e                               Run a command                   │
│ --help                                       Show this message and exit.     │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Commands

The section below describes the `run` command supported by `dojo`.

### `dojo run`

Execute a target with opinionated debugging helpers (`b()`, `p()`, `i()`, `c()`), Rich
tracebacks, and post-mortem exception hooks pre-injected.

```console
dojo run [OPTIONS] [TARGET] [TARGET_ARGS]...
```

#### Arguments

| Argument      | Type              | Description                                                         |
| :------------ | :---------------- | :------------------------------------------------------------------ |
| `TARGET`      | String (Optional) | Path to script, module name, or executable name.                    |
| `TARGET_ARGS` | List of Strings   | Optional trailing arguments forwarded to the target via `sys.argv`. |

#### Options

| Option       | Flag | Type   | Default | Description                                                       |
| :----------- | :--- | :----- | :------ | :---------------------------------------------------------------- |
| `--debugger` | `-d` | Choice | `None`  | Debugger backend (`debugpy`, `ipdb`, `pdb`, `pudb`).              |
| `--verbose`  | `-v` | Flag   | `False` | Enable verbose output.                                            |
| `--module`   | `-m` | Flag   | `False` | Treat `TARGET` as a Python module (runs with `runpy.run_module`). |
| `--exec`     | `-e` | Flag   | `False` | Treat `TARGET` as an executable command (e.g. `pytest`).          |
| `--help`     |      | Flag   |         | Show help message and exit.                                       |

> [!WARNING]
> `--module` (`-m`) and `--exec` (`-e`) are mutually exclusive. Passing both flags
> causes `dojo run` to exit with an error.

#### Execution Modes

```console
# Mode 1: File Execution (Default)
dojo run script.py arg1 arg2

# Mode 2: Module Execution (-m)
dojo run -m my_package.worker --workers 4

# Mode 3: Executable Execution (-e)
dojo run -e pytest -k "test_feature"
```

## Exit Codes

| Code | Condition                                                                                                |
| :--- | :------------------------------------------------------------------------------------------------------- |
| `0`  | Target executed successfully, or debugging session terminated cleanly (`BdbQuit` / `KeyboardInterrupt`). |
| `1`  | Import error, mutually exclusive arguments, or unhandled exception during target execution.              |
| `2`  | Invalid CLI invocation syntax (handled by Typer).                                                        |
