
# Development and contributing

Project uses `poe` for defining and speeding up developer tasks.

## Environment setup

It's recommended to use `uv` for managing virtual environments. You can create a new environment with:

```console
uv sync
```

This will create a new virtual environment in `.venv` folder and install all dependencies from `pyproject.toml`.

You can activate the environment with:

```console
./.venv/Scripts/activate  # Windows
source .venv/bin/activate  # Linux / macOS
```

If for some reason you don't want to use `uv`, there's a `requirements.txt` file generated from `pyproject.toml` that you can use to install dependencies with `pip`:

```console
pip install -r requirements.txt
```

The environment is kept up to date by dependabot, but you can also update dependencies manually with:

```console
uv sync --upgrade
```

## Lint and type check

We're using `ruff` as formatter and linter and `basedpyright` for static type checking.
You can run all three with simple command:

```console
poe code-quality
```

## Pre-commit hooks

Its recommended setting up `pre-commit` hooks to run quality checks before committing code.

```console
pre-commit install
```

The project uses `pre-commit.ci` to automatically run checks on pull requests. If you don't have `pre-commit` installed locally, the checks will still run on the CI and possibly edit the code. This can lead to confusing situations where your code is modified after the PR is created.

## Tests

`Pytest` is used for testing. Tests include:

- docstring tests
- unit tests for internal functions
- integration tests for command line interface using `CLI Runner` from `Typer`.

You can run all tests with:

```console
poe test
```

(this is just a shortcut for `pytest` with some additional options).

## Contributing

You're welcome to contribute both new features and fixes. The above quality checks need to pass for a contribution to be accepted to `debug-dojo`. This is tested with Pull Requests job hook.
