# CLI Reference

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

::: mkdocs-typer2
    :module: debug_dojo._cli
    :name: dojo
    :pretty: true

[target]: #
