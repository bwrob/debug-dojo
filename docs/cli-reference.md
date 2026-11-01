# CLI Reference

Command line interface reference and usage guide for `dojo`.

## Usage

Run your Python script with debugging tools enabled using the
`dojo run` command:

``` console
dojo run my_script.py
```

Check your progress and current belt with:

``` console
dojo belt
```

You can optionally set configuration, verbose mode, and specify the
debugger type. Both script files and modules are supported:

``` console
dojo run --debugger ipdb --config dojo.toml --verbose --module my_module
```

## Commands

The following subcommands are available:

### `dojo run`

Run a Python script or module with debugging tools installed.

```console
dojo run [OPTIONS] [TARGET]
```

**Options:**

- `-c, --config PATH`: Path to configuration file.
- `-d, --debugger [debugpy|ipdb|pdb|pudb]`: Specify debugger backend.
- `-v, --verbose`: Enable verbose output.
- `-m, --module`: Run target as a Python module.
- `-e, --exec`: Execute target string directly.

### `dojo config`

Show current configuration.

```console
dojo config
```
