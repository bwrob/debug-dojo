---
diataxis: reference
purpose: Detail configuration schema, options, file resolution order, and defaults for dojo.toml and pyproject.toml.
---

# Configuration

You can configure Debug Dojo using a standalone `dojo.toml` file or inside your
project's `pyproject.toml` under the `[tool.debug_dojo]` table.

## Configuration Resolution Order

`debug-dojo` checks for configuration files in the following precedence order:

1. File path specified by the `--config` / `-c` CLI flag.
2. `dojo.toml` in the current working directory.
3. `pyproject.toml` in the current working directory (`[tool.debug_dojo]`).
4. Default configuration values (`DebugDojoConfigV3`).

<!-- termynal -->
```console
# Inspect resolved configuration from a local dojo.toml
$ dojo config -c dojo.toml

Using configuration file: /workspace/dojo.toml.
Using configuration model: DebugDojoConfigV3.
Current configuration model DebugDojoConfigV3.
Using debug-dojo configuration:
DebugDojoConfigV3(exceptions=ExceptionsConfig(locals_in_traceback=False,
post_mortem=True, rich_traceback=True),
debuggers=DebuggersConfig(default=<DebuggerType.IPDB: 'ipdb'>,
prompt_name='debug-dojo> '), features=FeaturesConfig(breakpoint='b',
comparer='c', rich_inspect='i', rich_print='p'))
```

## Configuration File Examples

=== "dojo.toml"

```toml
[debuggers]
    default = "ipdb"
    prompt_name = "debug-dojo> "

    [debuggers.debugpy]
        host = "localhost"
        log_to_file = false
        port = 1992
        wait_for_client = true

    [debuggers.ipdb]
        context_lines = 20

[exceptions]
    locals_in_traceback = false
    post_mortem = true
    rich_traceback = true

[features]
    breakpoint = "b"     # Global shortcut for setting breakpoints
    comparer = "c"       # Global shortcut for side-by-side comparison
    rich_inspect = "i"   # Global shortcut for Rich inspection
    rich_print = "p"     # Global shortcut for Rich pretty printing
```

=== "pyproject.toml"

```toml
[tool.debug_dojo.debuggers]
    default = "ipdb"
    prompt_name = "debug-dojo> "

    [tool.debug_dojo.debuggers.debugpy]
        host = "localhost"
        log_to_file = false
        port = 1992
        wait_for_client = true

    [tool.debug_dojo.debuggers.ipdb]
        context_lines = 20

[tool.debug_dojo.exceptions]
    locals_in_traceback = false
    post_mortem = true
    rich_traceback = true

[tool.debug_dojo.features]
    breakpoint = "b"
    comparer = "c"
    rich_inspect = "i"
    rich_print = "p"
```

## Configuration Reference

The tables below define each configuration section, key, data type, and default value.

### `[debuggers]`

Controls debugger selection and shared REPL properties.

| Key           | Type   | Default          | Description                                                            |
| :------------ | :----- | :--------------- | :--------------------------------------------------------------------- |
| `default`     | String | `"ipdb"`         | Default debugger backend: `"ipdb"`, `"pudb"`, `"pdb"`, or `"debugpy"`. |
| `prompt_name` | String | `"debug-dojo> "` | Prompt string displayed in debugger REPL.                              |

#### `[debuggers.debugpy]`

Settings for VS Code / remote debugging integration with Debugpy.

| Key               | Type    | Default       | Description                                                    |
| :---------------- | :------ | :------------ | :------------------------------------------------------------- |
| `host`            | String  | `"localhost"` | Host address for `debugpy` to listen on.                       |
| `port`            | Integer | `1992`        | TCP port for `debugpy` communication.                          |
| `log_to_file`     | Boolean | `false`       | When `true`, write `debugpy` diagnostic logs to a file.        |
| `wait_for_client` | Boolean | `true`        | When `true`, pause execution until a debugger client attaches. |

#### `[debuggers.ipdb]`

Settings for IPython Debugger integration.

| Key             | Type    | Default | Description                                                       |
| :-------------- | :------ | :------ | :---------------------------------------------------------------- |
| `context_lines` | Integer | `20`    | Number of context lines shown around the current execution frame. |

#### `[debuggers.pdb]` & `[debuggers.pudb]`

Standard library `pdb` and visual full-screen console `pudb` use default backend
settings.

### `[exceptions]`

Controls traceback rendering and post-mortem failure handling.

| Key                   | Type    | Default | Description                                                                          |
| :-------------------- | :------ | :------ | :----------------------------------------------------------------------------------- |
| `rich_traceback`      | Boolean | `true`  | When `true`, render exceptions with Rich colorized tracebacks.                       |
| `post_mortem`         | Boolean | `true`  | When `true`, enter an interactive post-mortem debugging session on unhandled errors. |
| `locals_in_traceback` | Boolean | `false` | When `true`, display local variable dictionaries in traceback frames.                |

### `[features]`

Customizes global shortcut names injected into Python's `builtins`. Set any key to an
empty string (`""`) to disable that shortcut.

| Key            | Type   | Default | Injected Function                                       |
| :------------- | :----- | :------ | :------------------------------------------------------ |
| `breakpoint`   | String | `"b"`   | Set breakpoint using configured backend (`b()`).        |
| `comparer`     | String | `"c"`   | Side-by-side object comparison table (`c(obj1, obj2)`). |
| `rich_inspect` | String | `"i"`   | Rich object inspection with methods (`i(obj)`).         |
| `rich_print`   | String | `"p"`   | Rich pretty-printing (`p(obj)`).                        |
