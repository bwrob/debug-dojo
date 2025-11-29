# Development Plan

## Project Goals

`debug-dojo` aims to provide a unified, "zen" debugging experience for Python developers. By abstracting the differences between various backend debuggers (`pdb`, `ipdb`, `pudb`, `debugpy`) and injecting useful runtime helpers (`p`, `c`, `i`, `b`), it allows developers to focus on the problem at hand rather than the toolchain configuration.

## Roadmap

The development roadmap is driven by GitHub issues. Below is the prioritized list of planned work.

### Features & Enhancements

- **[#89] Zen Notifications**: System notifications for breakpoints and long-running tasks.
- **[#92] Dojo Belts (Gamification)**: Local stats tracking for usage (bugs crushed).
- **[#2] Specialized Comparers**: Improve the `c()` helper to provide clearer, structural diffs for `list` and `dict` types.
- **[#88] Specialized Object Inspectors**: Extend inspection tools for specialized objects (Pandas, NumPy, Pydantic).
- **[#90] Mini-Profiler**: Lightweight profiling option wrapping `cProfile`.
- **[#4] PuDB Breakpoint Management**: Add functionality to manage `pudb`'s saved breakpoints via tool configuration.
- **[#91] Robust Crash Handler**: Unified interactive crash handler ("Debug it? [Y/n]").
- **[#85] Enhanced UI with Rich**: Leverage `rich` more extensively for interactive inspection tools during debugging sessions (e.g. better object inspectors, panels).
- **[#33] Direct IPython Integration**: Refactor the `ipdb` backend to potentially use `IPython`'s debugger directly.
- **[#87] Remote Debugging**: Simplify the setup for remote debugging scenarios using `debugpy`.
- **[#86] Plugin System**: Design and implement a plugin system to allow users to define their own helper functions or integrations.

### Maintenance & Stability

- **[#82] Maintenance: Dependency Updates**: Keep dependencies updated, specifically ensuring compatibility with new versions of supported debuggers.
- **[#83] Stability: Environment Injection Tests**: Improve test coverage for edge cases in environment injection logic (`_installers.py`).
- **[#35] Coverage Enforcement**: Integrate coverage reporting into the CI pipeline to ensure code quality.

### Documentation & Infrastructure

- **[#84] Documentation: Advanced Usage**: Expand the documentation to include more examples of advanced configuration and usage scenarios.
- **[#19] Automated Publishing Workflow**: Verify and refine the GitHub Actions for publishing to PyPI and deploying GitHub Pages.
