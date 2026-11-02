---
diataxis: reference
purpose: Document command-line syntax, flags, interactive dpdb commands, and exit codes for debug-dojo.
---

# CLI Reference

The `debug-dojo` (and `dojo`) command-line interface runs Python scripts, modules, or
commands with the `dpdb` interactive debugger and Rich inspection helpers pre-installed.

<!-- termynal -->
```console
$ debug-dojo --help

<b>Usage: </b><b>debug-dojo [OPTIONS] [TARGET]</b>

Run a Python script, module, or command with the dpdb debugger.

╭─ Arguments ──────────────────────────────────────────────────────────────────╮
│   target      [target]  The target script, module, or command to debug.      │
╰──────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────╮
│ --break  -b  TEXT  Set a breakpoint (line, file:line, or function)           │
│ --help             Show this message and exit.                               │
╰──────────────────────────────────────────────────────────────────────────────╯
```

## Invocation

Execute any script, executable command, or Python module with opinionated debugging
helpers (`b()`, `p()`, `i()`, `c()`), Rich tracebacks, and `dpdb` post-mortem exception
handling pre-injected:

```console
uvx debug-dojo [OPTIONS] [TARGET] [TARGET_ARGS]...
dojo [OPTIONS] [TARGET] [TARGET_ARGS]...
```

### Arguments

| Argument      | Type              | Description                                                         |
| :------------ | :---------------- | :------------------------------------------------------------------ |
| `TARGET`      | String (Optional) | Path to script, executable command on `PATH`, or module name.       |
| `TARGET_ARGS` | List of Strings   | Optional trailing arguments forwarded to the target via `sys.argv`. |

### Options

| Option    | Flag | Type        | Default | Description                                                                |
| :-------- | :--- | :---------- | :------ | :------------------------------------------------------------------------- |
| `--break` | `-b` | `list[str]` | `None`  | Set a breakpoint (`line`, `file:line`, or function name) before execution. |
| `--help`  |      | Flag        |         | Show help message and exit.                                                |

### Automatic Target Resolution

`debug-dojo` automatically detects how to run `TARGET` without extra flags:

```console
# 1. File path
uvx debug-dojo script.py arg1 arg2

# 2. Executable command in project .venv or PATH
uvx debug-dojo pytest -k "test_feature"

# 3. Importable Python module
uvx debug-dojo my_package.worker --workers 4
```

## Interactive Debugger Commands

Inside a `dpdb>` session, standard `pdb` / IPython debugger commands are enhanced with
Rich visual formatting:

| Category           | Command                      | Description                                                                 |
| :----------------- | :--------------------------- | :-------------------------------------------------------------------------- |
| **Execution**      | `n` / `next`                 | Execute the current line and step to the next line in the current frame.    |
|                    | `s` / `step`                 | Step into the function called on the current line.                          |
|                    | `c` / `cont` / `continue`    | Continue execution until the next breakpoint or exception.                  |
|                    | `r` / `return`               | Continue execution until the current function returns.                      |
|                    | `unt` / `until [line]`       | Continue until a line greater than the current line (or `line`) is reached. |
|                    | `j` / `jump <line>`          | Set the next line that will be executed.                                    |
|                    | `q` / `quit`                 | Abort debugging and exit the program cleanly.                               |
| **Stack & Source** | `w` / `where` / `bt`         | Render the call stack as a Rich table with active-frame highlighting.       |
|                    | `u` / `up [count]`           | Move up `count` frames (default `1`) toward older caller frames.            |
|                    | `d` / `down [count]`         | Move down `count` frames (default `1`) toward newer callee frames.          |
|                    | `l` / `list [first[, last]]` | List source code around the current line.                                   |
|                    | `ll` / `longlist`            | List the entire source code of the current function or frame.               |
|                    | `context <n>`                | Set the number of source context lines shown when entering a frame.         |
| **Inspection**     | `p <expr>`                   | Evaluate `<expr>`, pretty-print with Rich, and bind the result to `_`.      |
|                    | `pp <expr>`                  | Evaluate `<expr>`, expand all nested structures with Rich, and bind to `_`. |
|                    | `pinfo [expr]`               | Inspect `<expr>` (or all frame locals when omitted) in a Rich panel.        |
|                    | `pinfo2 [expr]`              | Deep-inspect `<expr>` (or all frame locals including private attributes).   |
|                    | `a` / `args`                 | Display current function parameters, types, shapes/lengths, and values.     |
|                    | `whatis <expr>`              | Show type, module, signature, shape/length, MRO, and docstring summary.     |
|                    | `psource <expr>`             | Render syntax-highlighted source code for any module, class, or callable.   |
|                    | `display [expr]`             | Watch `<expr>` in the inline context banner (or list watched expressions).  |
|                    | `undisplay [expr]`           | Remove `<expr>` (or all expressions) from the watch list.                   |
| **Breakpoints**    | `b` / `break [loc[, cond]]`  | List breakpoints in a Rich table, or set a breakpoint at `loc` or callable. |
|                    | `tbreak [loc[, cond]]`       | Set a temporary breakpoint that is removed after its first hit.             |
|                    | `cl` / `clear [bp...]`       | Clear specified breakpoints (or all breakpoints).                           |
|                    | `enable` / `disable <bp...>` | Enable or disable breakpoints by number.                                    |
| **Session**        | `interact`                   | Start an interactive IPython shell in the current frame's scope.            |
|                    | `run` / `restart [args]`     | Restart the target program while preserving active breakpoints.             |
| **Help**           | `h` / `help [cmd]`           | Show the categorized `dpdb` command reference table or help for `cmd`.      |

## Exit Codes

| Code | Condition                                                                                                |
| :--- | :------------------------------------------------------------------------------------------------------- |
| `0`  | Target executed successfully, or debugging session terminated cleanly (`BdbQuit` / `KeyboardInterrupt`). |
| `1`  | Import error, mutually exclusive arguments, or unhandled exception during target execution.              |
| `2`  | Invalid CLI invocation syntax or option parsing error.                                                   |
