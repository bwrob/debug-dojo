
# Development and contributing

Project uses `poe` for defining developer tasks.

## Lint and type check

We're using `ruff` as formatter and linter and `basedpyright` for static type checking.
You can run all three with simple command:

```console
poe code-quality
```

## Tests

`Pytest` is used for testing. Currently only few example doc tests are set up.

```console
poe test
```

## Contributing

You're welcome to contribute both new features and fixes. The above quality checks need to pass for a contribution to be accepted to `debug-dojo`. This is tested with Pull Requests job hook.

It is recommended to set up a pre-commit hook based on the included config.

```console
pre-commit install
```
