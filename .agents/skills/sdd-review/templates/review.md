# Spec Conformance Review: [Feature Name]

- **Feature Identifier**: `[feature-id]`
- **Spec Reference**: `.specs/[feature-id]/spec.md`
- **Plan Reference**: `.specs/[feature-id]/plan.md`
- **Reviewer**: [Reviewer Agent / Human]
- **Date**: YYYY-MM-DD
- **Verdict**: Approved | Changes Requested

---

## 1. Executive Summary

[Summarize findings from comparing the implementation to the specification.]

---

## 2. Requirement Traceability Matrix

| Requirement ID | Acceptance Scenario | Test Case Function | Status |
| :--- | :--- | :--- | :--- |
| `REQ-001` | Scenario 1: Happy path | `tests/test_feature.py::test_happy_path` | Passed |
| `REQ-002` | Scenario 2: Error path | `tests/test_feature.py::test_error_state` | Passed |

---

## 3. Scope Boundary Audit

- [ ] **In-Scope Verification**: Implementation satisfies and verifies all in-scope requirements.
- [ ] **No Scope Creep**: The codebase contains no unauthorized features, speculative code, or unrequested helpers.
- [ ] **Out-of-Scope Respected**: Items marked out-of-scope in `spec.md` remain absent from codebase.

---

## 4. Quality Invariant Scorecard

- [ ] **Tach Boundaries**: Passes `uv run tach check` with zero layer violations.
- [ ] **Type Precision**: Passes `uv run pyrefly check` with zero errors.
- [ ] **Cognitive Complexity**: All functions score 10 or less via `uv run complexipy`.
- [ ] **Test Coverage**: Passes `uv run poe test` with 100% branch coverage.
- [ ] **Code Hygiene**: Passes `uv run poe code-quality` (lint, format, spell check).

---

## 5. Findings & Action Items

### Required Changes (if any)
1. [Finding description with file link and exact trigger]

### Remediation Tasks for Plan ("Review Fixes")
If you request changes, append these tasks to `plan.md` under a new phase:
- [ ] **Fix 1: [Short Title]**
  - **Scope**: [Description of changes and files affected]
  - **Verification Gate**: `uv run poe test`

### Informational Notes
1. [Note on implementation trade-offs or future considerations]
