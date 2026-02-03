# Specification: Direct IPython Integration

## Overview
Refactor the `ipdb` backend execution logic to use the direct `IPython` API. The primary driver is to remove the dependency on the poorly-maintained `ipdb` wrapper while gaining better control over how `debug-dojo` helpers are injected into the REPL.

## Requirements
- Research IPython's embedding API.
- Replace `ipdb` dependency with direct python API usage.
- Ensure `debug-dojo` helpers are still injected correctly.
