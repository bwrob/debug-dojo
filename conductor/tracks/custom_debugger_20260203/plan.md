# Implementation Plan: Custom Responsive Internal Debugger

## Phase 1: Core Engine and Research
- [ ] Task: Research `pdb.Pdb` extension patterns and `Textual` layout responsiveness.
- [ ] Task: Create a prototype that wraps `pdb` and captures execution state without a UI.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Core Engine and Research' (Protocol in workflow.md)

## Phase 2: Responsive TUI Layout
- [ ] Task: Write Tests for layout resizing logic (mock terminal dimensions).
- [ ] Task: Implement the base `Textual` App with responsive panes (Source, Vars, Stack).
- [ ] Task: Implement "Narrow Mode" logic (Vertical stacking / Auto-hiding).
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Responsive TUI Layout' (Protocol in workflow.md)

## Phase 3: Variable Explorer and Helpers
- [ ] Task: Write Tests for variable tree generation and expansion.
- [ ] Task: Implement the Interactive Variable Explorer pane.
- [ ] Task: Integrate `i()` and `c()` helpers into the TUI context.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Variable Explorer and Helpers' (Protocol in workflow.md)

## Phase 4: Breakpoints and Shell
- [ ] Task: Write Tests for breakpoint toggling and persistence logic.
- [ ] Task: Implement the Breakpoint Management panel.
- [ ] Task: Implement the "Drop to Shell" feature using a nested REPL.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Breakpoints and Shell' (Protocol in workflow.md)

## Phase 5: Polishing and Integration
- [ ] Task: Finalize keybindings and "Dojo" aesthetic styling.
- [ ] Task: Integrate the new debugger as a backend option in the main CLI.
- [ ] Task: Conductor - User Manual Verification 'Phase 5: Polishing and Integration' (Protocol in workflow.md)
