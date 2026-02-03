# Specification: PuDB Breakpoint Management

## Overview
Enable management of `pudb`'s saved breakpoints through `debug-dojo`'s configuration or CLI. `pudb` stores breakpoints in a separate file, and users currently have to manage them manually within the UI. This feature allows programmatic or config-based definition of persistent breakpoints.

## Requirements
- Read/Write `pudb` breakpoint file.
- Allow defining persistent breakpoints in `debug-dojo` config.
- Sync config breakpoints to `pudb` before execution.
