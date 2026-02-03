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
    -   Refactor and verify (tests, linting, typing).
    -   Commit the task and record the summary.
5.  **Verify:** Ensure the entire track meets the specification and quality standards.

## 3. Tooling
- **Dependency Management:** `uv`
- **Task Automation:** `poethepoet` (`poe precommit`, `poe fix`, etc.)
- **Testing:** `pytest`
- **Linting/Formatting:** `ruff`
- **Type Checking:** `basedpyright`

## 4. Documentation
- Keep `plan.md` updated with task statuses (`[ ]`, `[/]`, `[x]`).
- Use **Git Notes** to record detailed summaries for each completed task.

## 5. Phase Completion Verification and Checkpointing Protocol
At the end of each phase, a mandatory verification task must be performed:
1.  **Run All Tests:** Ensure 100% coverage and all tests pass (`poe test` / `poe coverage`).
2.  **Lint & Format:** Ensure zero `ruff` violations (`poe lint`, `poe format`).
3.  **Type Check:** Ensure zero `basedpyright` errors in strict mode (`poe type-check`).
4.  **Checkpoint:** If all checks pass, the phase is considered complete and ready for the next.
