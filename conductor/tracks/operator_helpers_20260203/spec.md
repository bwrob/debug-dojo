# Specification: Operator-Based Inspection and Comparison

## Overview
Enhance the user experience of the `i` (inspect) and `c` (compare) helpers by converting them from simple functions into classes that leverage overloaded binary operators. This will allow for more ergonomic usage in interactive debugging sessions, specifically supporting the `i / object` and `object / i` syntax, inspired by the `wat` package.

## Functional Requirements
1.  **Operator Overloading:**
    -   Convert `i` and `c` into singleton instances of classes (e.g., `Inspector` and `Comparer`).
    -   Implement `__truediv__` (for `i / object`) and `__rtruediv__` (for `object / i`) to trigger the inspection/comparison logic.
2.  **Dual Syntax Support:**
    -   Maintain support for the standard function call syntax: `i(object)` and `c(obj1, obj2)`.
3.  **Flexible Workflows:**
    -   Support both `i / object` (forward) and `object / i` (reverse). The latter is specifically designed to allow users to quickly inspect a variable they've already typed by simply appending `/ i`.
4.  **Error Handling:**
    -   Implement graceful fallback/error handling. If the operator is used in a way that doesn't make sense (e.g., with a type that cannot be inspected), the tool should print a "Zen" error message instead of a raw traceback.

## Non-Functional Requirements
-   **Performance:** The overhead of using a class instance instead of a function should be negligible.
-   **Consistency:** The visual output of `i / object` must be identical to `i(object)`.

## Out of Scope
-   Changing the internal inspection logic itself (handled by the "Enhanced UI with Rich" track).
-   Adding other operators (e.g., `+`, `-`, `*`) unless a clear use case is identified.
