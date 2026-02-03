# Implementation Plan: Operator-Based Inspection and Comparison

## Phase 1: Prototype and Class Structure
- [ ] Task: Research implementation details for singleton classes with `__truediv__` and `__call__`.
- [ ] Task: Create a prototype for the `Inspector` class that supports both `i(obj)` and `i / obj`.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Prototype and Class Structure' (Protocol in workflow.md)

## Phase 2: Implementation of Inspector (i)
- [ ] Task: Write Tests for `i` supporting `__call__`, `__truediv__`, and `__rtruediv__`.
- [ ] Task: Refactor the existing `i` function in `_execution.py` (or relevant module) to a class instance.
- [ ] Task: Implement "Zen" error handling for invalid operations.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implementation of Inspector (i)' (Protocol in workflow.md)

## Phase 3: Implementation of Comparer (c)
- [ ] Task: Write Tests for `c` supporting `__call__` and operator syntax.
- [ ] Task: Refactor the existing `c` function to a class instance.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Implementation of Comparer (c)' (Protocol in workflow.md)

## Phase 4: Integration and Verification
- [ ] Task: Verify that both helpers are correctly injected into the debugger namespace.
- [ ] Task: Final manual verification in an interactive session (simulating up-arrow + `/ i`).
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Integration and Verification' (Protocol in workflow.md)
