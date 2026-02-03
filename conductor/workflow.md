# Development Workflow

## 1. Principles
- **Test-Driven Development (TDD):** Write tests before implementing features.
- **100% Test Coverage:** All new code must be covered by tests.
- **Strict Static Typing:** Full adherence to `basedpyright` in strict mode.
- **Full Linting Adherence:** No `ruff` violations allowed (enforcing ALL rule set).
- **Atomic Commits:** Commit changes after every successful task.

## 2. Process
1.  **Branching:** Ensure you are on a dedicated feature branch for the track (e.g., `feat/track-name` or `fix/issue-id`). Create one if necessary.
2.  **Understand:** Analyze requirements and existing code.
3.  **Plan:** Break down the track into small, manageable tasks in `plan.md`.
4.  **Implement (Iterative):**
    -   Write failing tests.
    -   Implement the feature/fix.
    -   **Verify Quality:** Run `poe fix` (format/lint) and `poe type-check`.
    -   **Verify Tests:** Run `poe test` and ensure 100% coverage.
    -   Commit the task and record the summary via Git Notes.
5.  **Verify Track:** Ensure the entire track meets the specification and all quality standards.

## 3. Tooling
- **Dependency Management:** `uv`
- **Task Automation:** `poethepoet` (`poe code-quality` is the master check).
- **Testing:** `pytest`
- **Linting/Formatting:** `ruff`
- **Type Checking:** `basedpyright`

## 4. Documentation
- Keep `plan.md` updated with task statuses (`[ ]`, `[/]`, `[x]`).
- Use **Git Notes** to record detailed summaries for each completed task.

## 5. Phase Completion Verification and Checkpointing Protocol
At the end of each phase, a mandatory verification task must be performed to ensure the codebase remains in a 'green' state:
1.  **Code Quality:** Run `poe fix` to ensure perfect formatting and no auto-fixable lint issues.
2.  **Static Typing:** Run `poe type-check` and ensure zero errors in strict mode.
3.  **Linting:** Run `poe lint` to catch any remaining issues.
4.  **Tests:** Run `poe coverage` to ensure all tests pass and 100% coverage is maintained.
5.  **Checkpoint:** If and only if ALL checks pass, the phase is considered complete.
