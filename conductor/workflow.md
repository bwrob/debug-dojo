# Development Workflow (Gemini Conductor)

## 1. Core Principles

- **Context First:** Before writing code, READ the `tech-stack.md` and related files in `src/`. Do not guess APIs.
- **Strict TDD:** Tests are the specification. Write the test -> Watch it fail -> Write code -> Watch it pass.
- **Type-Safety First:** Define data structures (Pydantic/DataClasses) and Type hints before writing logic.
- **Zero Tolerance:** No linting warnings (`ruff`), no type errors (`basedpyright`), no skipped tests.
- **Conventional Commits:** Use Angular convention (e.g., `feat:`, `fix:`, `test:`, `refactor:`).

## 2. The Development Loop (Per Task)

For every item in `plan.md`, execute this exact cycle:

### Phase A: Design & Specification

1. **Check Out:** Ensure you are on the correct feature branch.
2. **Define Interface:** Write/Update the Type definitions and function signatures first.
3. **Write Test:** Create a specific `pytest` case in `tests/` that reproduces the requirement.
4. **Verify Failure:** Run `uv run pytest path/to/test.py` and confirm it fails (Red state).

### Phase B: Implementation

1. **Implement:** Write the minimum code necessary to pass the test.
2. **Verify Pass:** Run the test again. If it fails, analyze the stack trace and iterate. Do not modify the test to make it pass unless the requirement changed.

### Phase C: Polish & Verify (The "Green" Gate)

1. **Format & Lint:** Run `uv run poe fix`.
2. **Type Check:** Run `uv run poe type-check`.
3. **Coverage:** Run `uv run poe coverage`.
4. **Refactor:** If the code is messy but passes tests, refactor now, then re-run checks.

### Phase D: Commit

1. **Update Plan:** Mark the task in `plan.md` as `[x]`.
2. **Git Commit:** Commit with a conventional message describing the *why*, not just the *what*.
   - *Example:* `feat(auth): implement JWT validation logic`

## 3. Tooling Reference

- **Command Runner:** Always use `uv run poe <command>` to ensure virtualenv context.
- **Testing:** `uv run pytest` (or `poe test`).
- **Linting:** `ruff check --fix` (via `poe fix`).
- **Type Checking:** `basedpyright` (via `poe type-check`).

## 4. Error Handling Protocol

If a verification step fails:

1. **Read the Error:** Analyze the `stdout`/`stderr` carefully.
2. **Attempt Fix:** Try to fix the code (up to 3 attempts).
3. **Stop & Ask:** If you are stuck after 3 attempts, stop and present the error to the user with a suggested path forward.
4. **Never Force:** Do not use `# type: ignore` or `# noqa` unless explicitly authorized by the user.

## 5. Final Phase Verification

When all tasks in `plan.md` are `[x]`:

1. **AI Review:** Run `/conductor:review`. This compares the final implementation against the original `spec.md` to ensure no requirements were missed.
2. **Action:** If the review flags missing features or logic gaps, create a new task in `plan.md` to address them before proceeding.
3. **Quality Gate:** Run the full suite: `uv run poe code-quality`.
4. **Completion:** If successful, announce: "Track complete. All checks passed. Ready for human review."
