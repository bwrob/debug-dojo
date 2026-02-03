# Specification: Custom Responsive Internal Debugger

## Overview
Implement a custom, responsive TUI (Terminal User Interface) debugger for `debug-dojo`, built upon the foundation of Python's `pdb`. The primary goal is to provide a "Zen" debugging experience that remains functional and aesthetic across all screen sizes, including mobile devices and narrow vertical terminal splits.

## Functional Requirements
1.  **Core Debugging Engine:** Extend `pdb.Pdb` to handle execution control while providing a hook for the custom TUI.
2.  **Responsive TUI (Resizing):**
    -   Implement a layout that adapts to terminal dimensions.
    -   **Narrow Width (< 80 chars):** Automatically switch to a vertical stack or hide secondary panels (Variables/Stack) to prioritize source code visibility.
    -   **Wide Width:** Display source code, variable explorer, and stack trace in a multi-pane layout.
3.  **Interactive Variable Explorer:**
    -   Expandable/collapsible view of complex data structures.
    -   Integration with `debug-dojo`'s `i()` and `c()` helpers for deep inspection and comparison.
4.  **Persistent Breakpoint Management:**
    -   A dedicated panel to view, toggle, and delete breakpoints.
    -   Syncing of breakpoints with `debug-dojo` configuration.
5.  **Embedded Shell:**
    -   Easily drop into an interactive shell (e.g., `IPython` if available, or a `rich`-enhanced REPL) at the current frame.
6.  **Custom Keybindings:**
    -   Provide intuitive, single-key commands for stepping (Next, Step, Continue, Return).

## Non-Functional Requirements
-   **Performance:** The UI must be lightweight and responsive, even with large variable structures.
-   **Aesthetics:** Adhere to the "Dojo" visual identity using `rich` and `Textual` (if applicable).
-   **Robustness:** Graceful fallback to standard `pdb` if the TUI fails to initialize.

## Out of Scope
-   Remote debugging integration (handled by a separate track).
-   Memory profiling (handled by a separate track).
