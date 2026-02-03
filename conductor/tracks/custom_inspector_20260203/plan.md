# Implementation Plan: Custom Object Inspector (i)

## Phase 1: Logic and Data Extraction
- [ ] Task: Research `wat` and `rich.inspect` source code for attribute extraction best practices.
- [ ] Task: Implement a `MemberExtractor` class that handles safe attribute access and categorization.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Logic and Data Extraction' (Protocol in workflow.md)

## Phase 2: Core Inspector Implementation
- [ ] Task: Write Tests for categorization logic and privacy filtering.
- [ ] Task: Implement the core `InspectorEngine` that processes extracted data into a renderable structure.
- [ ] Task: Implement MRO and Type identity display.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Core Inspector Implementation' (Protocol in workflow.md)

## Phase 3: Visual Rendering with Rich
- [ ] Task: Write Tests for `rich` output structure (using snapshots or string verification).
- [ ] Task: Implement the visual layout using `rich` Tables and Panels.
- [ ] Task: Integrate docstring and signature preview logic.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Visual Rendering with Rich' (Protocol in workflow.md)

## Phase 4: Recursion and Advanced Features
- [ ] Task: Write Tests for recursive inspection with various `depth` settings.
- [ ] Task: Implement nested container inspection logic.
- [ ] Task: Implement the `all` flag for showing private/dunder members.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Recursion and Advanced Features' (Protocol in workflow.md)

## Phase 5: Integration
- [ ] Task: Replace `rich.inspect` with the new `InspectorEngine` in the `i` helper.
- [ ] Task: Conductor - User Manual Verification 'Phase 5: Integration' (Protocol in workflow.md)
