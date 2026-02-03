# Specification: Direct IPython Integration

## Overview
Refactor the `ipdb` backend execution logic. Currently, it might be relying on subprocess calls that limit interactivity or control. The goal is to integrate directly with `IPython`'s embedding and debugging APIs to provide a smoother experience.

## Requirements
- Research IPython's embedding API.
- Replace subprocess call with direct python API usage where feasible.
- Ensure `debug-dojo` helpers are still injected correctly.
