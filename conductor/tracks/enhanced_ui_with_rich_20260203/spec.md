# Specification: Enhanced UI with Rich

## Overview
Refactor existing inspection tools to use `rich` components more extensively. This includes using Panels, Layouts, and Trees to display information during a debugging session, making the output cleaner and more professional.

## Requirements
- Replace print statements with `rich.console.Console` methods.
- Use `Panel` for grouping related info.
- Use `Tree` for nested object inspection.
- Ensure consistent color theme matching the "Dojo" aesthetic.
