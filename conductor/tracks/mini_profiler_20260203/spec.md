# Specification: Mini-Profiler

## Overview
Implement a lightweight profiling option that wraps `cProfile`. This allows users to quickly check the performance of the script they are debugging without setting up complex external profiling tools.

## Requirements
- Add a CLI flag (e.g., `--profile`) to the main execution entry point.
- When enabled, run the target script under `cProfile`.
- Dump stats to a file or print a summary table using `rich` at the end of execution.
- Allow sorting/filtering of stats via config.
