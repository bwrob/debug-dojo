# Configuration

You can configure the debugging tools using a `dojo.toml` or
`pyproject.toml` file. The configuration allows you to specify which
debugger to use, enable or disable features, and set various options.

`debug-dojo` looks for configuration in the following order:

1.  A file specified by the `--config` CLI option.
2.  `dojo.toml` in the current working directory.
3.  `pyproject.toml` in the current working directory.
4.  `dojo.toml` in the user's config directory (e.g., `~/.config/dojo.toml`).

**Example `dojo.toml`:**

``` toml
[debuggers]
    default = "ipdb"
    prompt_name = "my-dojo> "

    [debuggers.debugpy]
        host = "localhost"
        log_to_file = false
        port = 1992
        wait_for_client = true

    [debuggers.ipdb]
        context_lines = 20

    # pdb and pudb have no specific configuration options currently

[exceptions]
    locals_in_traceback = false
    post_mortem = true
    rich_traceback = true

[features]
    breakpoint = "b" # Mnemonic for setting breakpoints
    comparer = "c"   # Mnemonic for side-by-side object comparison
    rich_inspect = "i" # Mnemonic for rich object inspection
    rich_print = "p"   # Mnemonic for rich pretty printing

    # To disable a feature, set its mnemonic to an empty string:
    # comparer = ""
```

## Configuration Sections

### `[debuggers]`

This section controls the behavior of the integrated debuggers.

-   `default` (string, default: `ipdb`): Specifies the default debugger to use when `debug-dojo` is invoked without a `--debugger` flag. Valid options are `debugpy`, `ipdb`, `pdb`, and `pudb`.
-   `prompt_name` (string, default: `debug-dojo> `): Sets the prompt string displayed in the debugger's REPL.

#### `[debuggers.debugpy]`

Specific settings for the `debugpy` debugger.

-   `host` (string, default: `localhost`): The host address for `debugpy` to listen on.
-   `log_to_file` (boolean, default: `false`): If `true`, `debugpy` will log its output to a file.
-   `port` (integer, default: `1992`): The port number `debugpy` will use for communication.
-   `wait_for_client` (boolean, default: `true`): If `true`, `debug-dojo` will pause execution and wait for a debugger client (e.g., VS Code) to connect before proceeding.

#### `[debuggers.ipdb]`

Specific settings for the `ipdb` debugger.

-   `context_lines` (integer, default: `20`): The number of context lines to display around the current line in `ipdb`.

#### `[debuggers.pdb]` and `[debuggers.pudb]`

Currently, `pdb` and `pudb` do not have specific configurable options beyond their default behavior.

### `[exceptions]`

This section configures how `debug-dojo` handles exceptions.

-   `locals_in_traceback` (boolean, default: `false`): If `true`, local variables will be included in the traceback output, providing more context for errors.
-   `post_mortem` (boolean, default: `true`): If `true`, `debug-dojo` will automatically enter a post-mortem debugging session (using the configured debugger) when an unhandled exception occurs.
-   `rich_traceback` (boolean, default: `true`): If `true`, tracebacks will be rendered using `rich`, providing colorized and more readable output.

### `[features]`

This section allows you to customize the mnemonics (short names) for the `debug-dojo` helper functions that are injected into builtins when `debug_dojo.install` is used. Setting a mnemonic to an empty string (`""`) will disable that feature.

-   `breakpoint` (string, default: `b`): The mnemonic for the breakpoint function. (e.g., `b()`)
-   `comparer` (string, default: `c`): The mnemonic for the object comparison function. (e.g., `c(obj1, obj2)`)
-   `rich_inspect` (string, default: `i`): The mnemonic for the rich object inspection function. (e.g., `i(obj)`)
-   `rich_print` (string, default: `p`): The mnemonic for the rich pretty printing function. (e.g., `p(obj)`)
