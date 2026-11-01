---
name: sdd-review
description: >-
  Audits implemented code against functional specifications and quality invariants.
  Verifies acceptance criteria, tests for regressions, and audits for scope creep.
  Mandatory after all tasks of an SDD plan are complete, before the agent reports the feature as done.
  Triggers: sdd review, verify spec, audit implementation, spec conformance, sdd convergence.
version: 1.1.0
---

# Specification Conformance Review (`sdd-review`)

This skill defines the audit protocol to verify implemented code against functional specifications in this project.
It verifies that delivered code satisfies all acceptance criteria without introducing scope creep or regressions.

---

## 1. Core Principles & Audit Invariants

1. **Strict Read-Only Contract**:
   When auditing an implementation, report findings and stop.
   Never edit code or configuration files during a review turn.
2. **Bi-Directional Requirement Traceability**:
   - Forward: Every requirement in `.specs/<feature-id>/spec.md` must link to an automated test.
   - Backward: Every new public interface must link to a stated requirement in the specification.
3. **Scope Creep Suppression**:
   Flag any code, helper function, or configuration not requested in the specification.
   Verify that items listed as Out-of-Scope remain absent from the codebase.
4. **Grounded Findings Only**:
   Ground every finding in a failing test or an explicit repository rule.
   Do not report personal stylistic preferences.

---

## 2. Subagent Profile: `sdd-reviewer`

When operating in multi-agent environments, invoke a dedicated `sdd-reviewer` subagent:

- **Role**: Quality Auditor and Specification Verifier.
- **Permissions**: Read-only codebase access and command execution.
- **Strict Constraint**: Never edit source code files or test files.
- **Goal**: Produce an objective `.specs/<feature-id>/review.md` audit report.

---

## 3. Review Procedure

Follow these steps to audit specification conformance:

### Step 1: Ingest Specification and Code Diff

Read `.specs/<feature-id>/spec.md` to review acceptance criteria.
Inspect the git diff against the base branch:

```bash
git diff main...HEAD
```

### Step 2: Instantiate Review Template

Copy the template [templates/review.md](./templates/review.md) to `.specs/<feature-id>/review.md`.

### Step 3: Construct Traceability Matrix

Run the automated traceability validator [scripts/check_traceability.py](./scripts/check_traceability.py):

```bash
uv run python .agents/skills/sdd-review/scripts/check_traceability.py .specs/<feature-id>/spec.md
```

1. Inspect the output to verify that every requirement links to a passing test.
2. Embed the generated matrix into `.specs/<feature-id>/review.md`.

### Step 4: Audit Scope Boundaries with Smart Diff Chunking

Inspect the diff volume to determine the review strategy:

```bash
git diff --shortstat main...HEAD -- . ':!.specs'
```

1. **Standard Mode (300 Lines or Fewer)**:
   Inspect the entire diff in a single pass:
   ```bash
   git diff main...HEAD -- . ':!.specs'
   ```
2. **Iterative Review Mode (More Than 300 Lines)**:
   When changes exceed 300 lines, review each modified file individually to prevent context saturation:
   - List all modified files:
     ```bash
     git diff --name-only main...HEAD -- . ':!.specs'
     ```
   - Inspect and evaluate each modified file individually:
     ```bash
     git diff main...HEAD -- <file-path>
     ```
   - Collect findings per file into working memory before you synthesize the final report.
3. **Inspect Scope Boundaries**:
   - Verify that no out-of-scope capabilities exist.
   - Verify that no dead code or uncalled helper functions exist.

### Step 5: Verify Public API Diffs with Griffe

Run the public API inspection script [scripts/check_public_api.py](./scripts/check_public_api.py):

```bash
uv run python .agents/skills/sdd-review/scripts/check_public_api.py --plan .specs/<feature-id>/plan.md
```

1. Inspect the output to verify that Griffe reports zero breaking changes.
2. Verify that all added public symbols match declared interfaces in `plan.md`.
3. If unplanned public symbols exist, verify the additions with the developer.

### Step 6: Execute Quality Verification Gates

Run the verification suite to prove correctness:

```bash
uv run poe code-quality
```

Record the output in the Quality Invariant Scorecard.

### Step 7: Render Verdict

Set the final review verdict in `.specs/<feature-id>/review.md`:
- If all acceptance criteria pass and no quality violations exist, declare **Approved**.
- If requirements are missing or quality gates fail, declare **Changes Requested** with actionable feedback.

### Step 8: Append Review Fixes Phase to Plan (When Changes Requested)

If the review verdict is **Changes Requested**:

1. Identify required code or test fixes from the findings.
2. Formulate atomic remediation tasks.
3. Append a `Review Fixes` phase to `.specs/<feature-id>/plan.md`:
   ```markdown
   ## Phase <N>: Review Fixes
   - [ ] **Fix 1: [Short Title]**
     - **Scope**: [Description of changes and files affected]
     - **Verification Gate**: `uv run poe test`
   ```
4. Hand over execution to `sdd-implement` to resolve fixes with TDD.

---

## 4. Verification & Quality Gate

Verify that the review report satisfies these criteria:

1. Every requirement from `spec.md` appears in the traceability matrix.
2. The report includes command results for `uv run poe code-quality`.
3. The verdict provides clear justification based on test evidence.
