# Specification: Custom Object Inspector (i)

## Overview
Develop a custom object inspection engine for the `i` helper, replacing the dependency on `rich.inspect`. This new engine will combine the visual power of `rich` with the structural clarity and ergonomics of the `wat` package, adhering strictly to the "Dojo" aesthetic and providing more granular control over output.

## Functional Requirements
1.  **Categorized Output:**
    -   Group object members into logical sections: "Attributes/Properties", "Methods", "Dunder Methods" (if enabled), and "MRO/Type Info".
2.  **Detailed Member Info:**
    -   For each member, show the name, type, and a concise one-line signature/docstring preview.
    -   Optionally show a safe "value preview" for simple properties.
3.  **Privacy Control:**
    -   **Hide by Default:** Private members (starting with `_`) and dunder methods must be hidden by default.
    -   Provide a flag (e.g., `i(obj, all=True)`) to toggle visibility.
4.  **Recursive Inspection:**
    -   Default to showing one level of nesting for containers (list, dict, set).
    -   Support a `depth` parameter (e.g., `i(obj, depth=2)`) to control recursion.
5.  **Type Identity:**
    -   Prominently display the object's full type path and Method Resolution Order (MRO).

## Non-Functional Requirements
-   **Aesthetics:** Use `rich` for formatting, ensuring colors and layout match the "Dojo" theme (readability first).
-   **Performance:** The inspection logic must be efficient and handle large objects without significant delay.
-   **Robustness:** Gracefully handle objects that raise exceptions during attribute access.

## Out of Scope
-   Interactive TUI elements (handled by the "Custom Responsive Internal Debugger" track).
-   Side-by-side comparison (handled by the "Specialized Comparers" track).
