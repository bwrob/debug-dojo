---
diataxis: reference
purpose: Chronological record of user-facing changes, features, and deprecations across releases.
---

# Changelog

All notable changes to the **debug-dojo** project will be documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to
[Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Added

- Built-in `dpdb` (Dojo Pdb) interactive terminal debugger powered by IPython and Rich with colored syntax highlighting, tab completion, and adaptive source context ([#146](https://github.com/bwrob/debug-dojo/pull/146), [#147](https://github.com/bwrob/debug-dojo/pull/147)).
- Inline frame context banner displaying modified locals (`Δ Changed:`), active-line variable values (`↳ Line:`), return values (`↩ Return:`), and watched expressions (`👁 Watch:`) on every step ([#146](https://github.com/bwrob/debug-dojo/pull/146)).
- Rich inspection commands in `dpdb`: call stack tables (`w`), function argument inspector (`a`), expression watches (`display` / `undisplay`), and rich object inspection (`pinfo`, `whatis`, `psource`) ([#146](https://github.com/bwrob/debug-dojo/pull/146)).
- Zero-configuration runner with automatic target resolution for scripts, executable commands in `.venv` or `PATH`, and importable modules without flags ([#147](https://github.com/bwrob/debug-dojo/pull/147), [#148](https://github.com/bwrob/debug-dojo/pull/148)).
- Command-line breakpoint seeding via `-b` / `--break` supporting line numbers, `file:line`, or function names prior to execution ([#146](https://github.com/bwrob/debug-dojo/pull/146), [#148](https://github.com/bwrob/debug-dojo/pull/148)).

### Changed

- Replaced heavy `typer` and `click` dependencies with a lightweight standard library argument parser styled exclusively with Rich, achieving sub-10ms startup latency and zero argument-passthrough interference ([#148](https://github.com/bwrob/debug-dojo/pull/148)).
- Relocated public interface to package root (`debug_dojo`, `debug_dojo.install`, `debug_dojo.cli`) and isolated subsystems under `debug_dojo._core` ([#149](https://github.com/bwrob/debug-dojo/pull/149)).
- Decomposed monolithic debugger module into modular subpackage `debug_dojo._core.debugger` (`views`, `breakpoints`, `debugger`, `session`) ([#149](https://github.com/bwrob/debug-dojo/pull/149)).

### Fixed

- Added `UV_NO_SOURCES_PACKAGE: taplo` in Docs deployment workflow to prevent local directory resolution failures during GitHub Pages builds ([#150](https://github.com/bwrob/debug-dojo/pull/150)).

### Removed

- Removed file-based configuration loading and models (`dojo.toml`, `pyproject.toml`, `_config.py`, and `_config_models.py`) in favor of zero-configuration operation ([#145](https://github.com/bwrob/debug-dojo/pull/145)).
- Removed `dojo config` and `dojo belt` CLI commands, along with legacy gamification mechanics ([#145](https://github.com/bwrob/debug-dojo/pull/145)).
- Removed `dacite`, `tomlkit`, `typer`, and `click` runtime dependencies ([#145](https://github.com/bwrob/debug-dojo/pull/145), [#148](https://github.com/bwrob/debug-dojo/pull/148)).

## V0.9.0 (2026-11-01)

### Added

- Migration to modern Zenith infrastructure and toolchain (`uv`, `poethepoet`, `prek`, `rumdl`, `taplo`, `typos`, `pyrefly`, `zizmor`, `tach`, `zensical`).
- 100% test coverage gate enforced via `fail_under = 100` and Pyrefly strict type checking.
- Syrupy snapshot testing for CLI outputs with deterministic ANSI stripping and box corner normalization across platforms.
- Animated terminal widgets powered by Python `termynal` package and Zensical Markdown integration with inlined assets.
- Resilient Taplo CI fallback supporting both PyPI packages and local monorepos.

### Changed

- Streamlined AI coding assistant setup exclusively for Antigravity (AGY), OpenAI Codex, and Claude Code.
- Replaced legacy JSON `TypeAlias` with modern PEP 695 `type JSON = ...`.
- Updated minimum runtime dependency bounds: `dacite>=1.8.0`, `tomlkit>=0.12.0`, `ipdb>=0.13.13`.

### Removed

- Deprecated legacy gamification references and obsolete manual static terminal assets.

## V0.8.0 (2026-01-31)

### Features

- **Dojo Belts Gamification**: Track your debugging experience and earn belts!
- **Restructured CLI**: New `run` and `belt` subcommands for better organization.
- **Minutes-based Progression**: Belt progression is now based on total debugging time (in minutes) and session count.
- Added `gamification` toggle in configuration.

### Improvements

- Lowered belt thresholds for better early-game feel.
- Improved CLI help and documentation.
- Refined code quality (linting, types, formatting).

## V0.7.0 (2025-11-27)

*release tag*: [v0.5.0](https://github.com/bwrob/debug-dojo/releases/tag/v0.7.0)

### Features

- Added 'all-debuggers' optional dependency.

### Improvements

- Added banner.

## V0.6.0 (2025-10-20)

*release tag*: [v0.5.0](https://github.com/bwrob/debug-dojo/releases/tag/v0.7.0)

### Features

- Integrate tach for architecture management.
- Widen dependency version ranges.
- Add 3.14 to supported Python versions.
- Switching to dacite for config loading.

### Improvements

- Gemini generated docs improvements.
- Project has 90% coverage.
- Precommit update-hooks.

## V0.5.0 (2025-08-23)

*release tag*: [v0.5.0](https://github.com/bwrob/debug-dojo/releases/tag/v0.5.0)

### Features

- CLI tests.
- Fixes to configuration reading.
- Post-mortem debugging support with `ipdb`.
- Added `--exec` option to `dojo` command -- debug dojo can now run arbitrary commands.

### Improvements

- Project and docs cleanup.
- UV build.
- PyProject cleanup.
- Testing the CLI with typer's CLI runner and pytest fixtures.
- README and docs index alignment.
- Pre-commit CI and extending pre-commit config.
- Set up Dependabot.
- CI improvements.

## V0.4.1 (2025-08-10)

*release tag*: [v0.4.1](https://github.com/bwrob/debug-dojo/releases/tag/v0.4.1)

### Improvements

- Mkdocs documentation at [debug dojo](https://bwrob.github.io/debug-dojo).

## V0.4.0 (2025-08-10)

*release tag*: [v0.4.0](https://github.com/bwrob/debug-dojo/releases/tag/v0.4.0)

### Features

- New configuration model `DebugDojoConfig` for better structure.
- Added support for `debugger` configuration in `dojo.toml`.
- Updated `dojo` command to include debugger type in command call.
- Configuration versioning allows for in-flight migration of old configurations.

### Improvements

- Improved error handling in configuration loading.
- Improved catching errors from target execution.

## V0.3.2 (2025-07-28)

*release tag*: [v0.3.2](https://github.com/bwrob/debug-dojo/releases/tag/v0.3.2)

### Features

- New logo for the project.
- Typer used for CLI implementation.
- Dojo is configured via `dojo.toml` or `pyproject.toml`.
- Support for `debugpy` and `ipdb` for debugging.

### Bug Fixes

- Fixed documentation and history.

## V0.2.0 (2025-07-20)

*release tag*: [v0.2.0](https://github.com/bwrob/debug-dojo/releases/tag/v0.2.0)

### Features

- Added `dojo` command for easy debugging setup.
- Added `p()` function for rich printing.
- Added history file for tracking changes.

### Improvements

- Moved to `hatch` for building and packaging.
- Fixed `pyproject.toml` to point to GitHub repository as the homepage.

## V0.1.0 (2025-07-19)

*release tag*: [v0.1.0](https://github.com/bwrob/debug-dojo/releases/tag/v0.1.0)

### Features

- Initial module to install debugging tools.
- Debug mode utilities for PuDB, rich tracebacks, and object inspection.
