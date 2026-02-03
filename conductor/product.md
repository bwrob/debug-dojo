# Initial Concept

## Overview
**debug-dojo** is a powerful Python package designed to streamline the debugging workflow directly from the terminal. It acts as a wrapper around existing debuggers, enhancing them with a unified interface, beautiful output, and a unique gamification system. The project aims to make "zen debugging" accessible, efficient, and even enjoyable for developers.

## Target Audience
The primary users are **Python developers** who prefer or require terminal-based workflows and are looking for a more interactive, readable, and feature-rich debugging experience than what standard tools (like `pdb` or raw `debugpy`) offer out of the box.

## Core Value Proposition
-   **Unified Interface:** A consistent CLI for launching scripts with various backends (`debugpy`, `pudb`, `pdb`, `ipdb`).
-   **Enhanced Visibility:** leverages `rich` to provide syntax-highlighted code, clear tracebacks, and pretty-printed object inspection.
-   **Gamification (Dojo Belts):** A novel approach to encouraging debugging best practices and tracking developer proficiency.
-   **Utility:** Built-in tools for deep object inspection and side-by-side comparison.

## Key Features
-   **Debugger Unification:** Launch scripts seamlessly with different debuggers via simple CLI flags.
-   **Visual Inspection:** "Rich" capabilities for displaying complex data structures and code.
-   **Gamified Progression:** A system of "belts" that rewards usage and mastery of debugging tools.
-   **Comparison Tools:** Utilities to diff and inspect Python objects during runtime.
-   **Easy Breakpoints:** Simplified helpers for inserting breakpoints in code.
