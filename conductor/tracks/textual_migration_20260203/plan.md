# Implementation Plan: Migrate CLI to Textual App

## Phase 1: Textual Foundation
- [ ] Task: Research Textual's app lifecycle and Typer integration patterns.
- [ ] Task: Create the base `Textual` App class and a placeholder "Main" screen.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Textual Foundation' (Protocol in workflow.md)

## Phase 2: Dojo Dashboard UI
- [ ] Task: Write Tests for Dashboard UI components (mocking state).
- [ ] Task: Implement the Two-Section layout (History on one side, Config on the other).
- [ ] Task: Implement the "Session History" list widget with auto-selection of the last run.
- [ ] Task: Implement the "Run Configuration" widget for viewing and editing settings.
- [ ] Task: Implement the "Belt Progress" widget (stats display).
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Dojo Dashboard UI' (Protocol in workflow.md)

## Phase 3: History and Launch Logic
- [ ] Task: Write Tests for history loading and session launching logic.
- [ ] Task: Integrate existing history persistence into the Textual components.
- [ ] Task: Implement the logic to populate the Config widget based on History selection.
- [ ] Task: Implement the "Quick Launch/Re-practice" feature with support for tweaked settings.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: History and Launch Logic' (Protocol in workflow.md)

## Phase 4: CLI Handoff & Integration
- [ ] Task: Write Tests for CLI argument parsing and app routing.
- [ ] Task: Refactor the main entry point to launch the Textual App.
- [ ] Task: Implement "Direct Launch" mode (bypassing dashboard via CLI args).
- [ ] Task: Conductor - User Manual Verification 'Phase 4: CLI Handoff & Integration' (Protocol in workflow.md)
