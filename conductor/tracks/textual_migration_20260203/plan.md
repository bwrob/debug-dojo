# Implementation Plan: Migrate CLI to Textual App

## Phase 1: Textual Foundation
- [x] Task: Research Textual's app lifecycle and Typer integration patterns.
- [x] Task: Create the base `Textual` App class and a placeholder "Main" screen.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Textual Foundation' (Protocol in workflow.md)

## Phase 2: Dojo Dashboard UI
- [x] Task: Write Tests for Dashboard UI components (mocking state).
- [x] Task: Implement the Two-Section layout (History on one side, Config on the other).
- [x] Task: Implement the "Session History" list widget with auto-selection of the last run.
- [x] Task: Implement the "Run Configuration" widget for viewing and editing settings.
- [x] Task: Implement the "Belt Progress" widget (stats display).
- [x] Task: Conductor - User Manual Verification 'Phase 2: Dojo Dashboard UI' (Protocol in workflow.md)

## Phase 3: History and Launch Logic
- [x] Task: Write Tests for history loading and session launching logic.
- [x] Task: Integrate existing history persistence into the Textual components.
- [x] Task: Implement the logic to populate the Config widget based on History selection.
- [x] Task: Implement the "Quick Launch/Re-practice" feature with support for tweaked settings.
- [x] Task: Conductor - User Manual Verification 'Phase 3: History and Launch Logic' (Protocol in workflow.md)

## Phase 4: CLI Handoff & Integration
- [x] Task: Write Tests for CLI argument parsing and app routing.
- [x] Task: Refactor the main entry point to launch the Textual App.
- [x] Task: Implement "Direct Launch" mode (bypassing dashboard via CLI args).
- [x] Task: Conductor - User Manual Verification 'Phase 4: CLI Handoff & Integration' (Protocol in workflow.md)
