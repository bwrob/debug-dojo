# Specification: Remote Debugging

## Overview
Simplify the configuration and launch process for remote debugging with `debugpy`. Users should be able to start a `debug-dojo` session that listens for incoming connections or connects to a remote adapter with minimal flag friction.

## Requirements
- Add CLI flags for `--listen` and `--connect`.
- Configure `debugpy` accordingly.
- Display clear connection info (host/port) in the terminal.
