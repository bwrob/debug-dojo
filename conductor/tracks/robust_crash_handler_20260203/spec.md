# Specification: Robust Crash Handler

## Overview
Implement a unified, interactive crash handler. When a script run by `debug-dojo` crashes with an unhandled exception, the tool should catch it, display a rich traceback, and offer to launch the post-mortem debugger immediately.

## Requirements
- Catch unhandled exceptions from the target script.
- Render traceback using `rich`.
- Prompt user: "Debug this crash? [Y/n]".
- If Yes, launch the configured debugger (e.g., `pdb.post_mortem`).
