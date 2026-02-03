# Specification: Migrate CLI to Textual App

## Overview
Migrate the core `debug-dojo` CLI from a standard `Typer` application to a full `Textual` TUI. This provides a unified "Zen" environment where users can manage their progress, review history, and launch debugging sessions.

**Architectural Note:** This follows a "Shell Wrapper" approach. While the Dashboard and Crash screens are full TUI applications, the target scripts will continue to run in the standard terminal environment to ensure 100% compatibility with interactive debuggers like IPython.

## Functional Requirements
1.  **Textual Application Foundation:**
    -   Implement the main `Textual` App class.
    -   Support command-line arguments via `Typer` to decide whether to launch the Dashboard or jump straight to a session.
2.  **Dojo Dashboard Screen:**
    -   **Belt Progress:** Display current belt and stats (bugs crushed, sessions).
    -   **Session History:** Interactive list of past debugging runs.
    -   **Quick Launch:** Ability to select a past run and "Re-practice" (re-run) it seamlessly.
3.  **Screen Management:**
    -   Implement a `Screen` stack to transition between the Dashboard and future features (like the Custom Debugger).
4.  **Responsive Layout:**
    -   Ensure the Dashboard remains usable on narrow terminals (e.g., vertical splits).

## Non-Functional Requirements
-   **Visual Identity:** Adhere strictly to the "Dojo" theme (Zen aesthetic, martial arts metaphors).
-   **User Flow:** Bypassing the dashboard with CLI arguments must be instantaneous.
-   **History Persistence:** Ensure debugging history is correctly loaded and updated.

## Out of Scope
-   Implementing the Custom Debugger logic (handled by a separate track).
-   Advanced search/filtering in history (can be added later).
