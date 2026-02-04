# Development Workflow (Gemini Conductor)

## 1. Core Principles

- **Context First:** Before writing code, READ the `tech-stack.md` and related files in `src/`. Do not guess APIs.
- **Strict TDD:** Tests are the specification. Write the test -> Watch it fail -> Write code -> Watch it pass.
- **Type-Safety First:** Define data structures (Pydantic/DataClasses) and Type hints before writing logic.
- **Zero Tolerance:** No linting warnings (`ruff`), no type errors (`basedpyright`), no skipped tests.
- **Conventional Commits:** Use Angular convention (e.g., `feat:`, `fix:`, `test:`, `refactor:`).
- **Atomic Operations:** Keep changes small and focused on a single task.

## 2. The Development Loop (Per Task)

For every item in `plan.md`, execute this exact cycle:

### Phase A: Design & Specification

1. **Check Out:** Ensure you are on the correct feature branch.
2. **Dependency Audit:** Check `pyproject.toml` and existing modules. Leverage existing utilities before adding new ones.
3. **Define Interface:** Write/Update Type definitions and function signatures.
4. **Write Test:** Create a specific `pytest` case in `tests/` that reproduces the requirement.
5. **Verify Failure:** Run `uv run pytest path/to/test.py` and confirm it fails (Red state).

### Phase B: Implementation

1. **Implement:** Write the minimum code necessary to pass the test.
2. **Verify Pass:** Run the test again. If it fails, analyze the stack trace and iterate.
3. **Internal Consistency:** Ensure new code matches the project's architectural patterns (e.g., configuration handling, error patterns).

### Phase C: Polish & Verify (The "Green" Gate)

1. **Format & Lint:** Run `uv run poe fix`.
2. **Type Check:** Run `uv run poe type-check`.
3. **Coverage:** Run `uv run poe coverage`.
4. **Refactor:** If the code is messy, refactor now. **Mandatory:** Re-run tests after any refactor.
5. **Documentation:** Update docstrings or `docs/` if public APIs changed. Ensure no comments are outdated.

### Phase D: Commit

1. **Update Plan:** Mark the task in `plan.md` as `[x]`.
2. **Git Commit:** Commit with a conventional message describing the *why*, not just the *what*.
   - *Example:* `feat(auth): implement JWT validation logic`

## 3. Tooling Reference

- **Command Runner:** Always use `uv run poe <command>` to ensure virtualenv context.
- **Testing:** `uv run pytest` (or `poe test`).
- **Linting:** `ruff check --fix` (via `poe fix`).
- **Type Checking:** `basedpyright` (via `poe type-check`).
- **Full Suite:** `uv run poe code-quality` (runs all checks).

## 4. Error Handling Protocol

If a verification step fails:

1. **Read the Error:** Analyze the `stdout`/`stderr` carefully.
2. **Attempt Fix:** Try to fix the code (up to 3 attempts).
3. **Stop & Ask:** If you are stuck after 3 attempts, stop and present the error to the user with a suggested path forward.
4. **Never Force:** Do not use `# type: ignore` or `# noqa` unless explicitly authorized.

## 5. Final Track Verification

When all tasks in `plan.md` are `[x]`:

1. **Full Suite:** Run `uv run poe code-quality`.
2. **AI Review:** Run `/conductor:review`. This compares implementation against `spec.md`.
3. **Cleanup:** Ensure no temporary files or debug prints remain.
4. **Completion:** Announce: "Track complete. All checks passed. Ready for human review."
