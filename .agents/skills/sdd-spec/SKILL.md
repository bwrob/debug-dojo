---
name: sdd-spec
description: >-
  Authors and clarifies functional specifications in Spec-Driven Development.
  Captures user stories, scope boundaries, and acceptance criteria in EARS format without implementation details.
  Mandatory whenever authoring or changing a spec file in an SDD feature directory.
  Triggers: write spec, author spec, sdd spec, feature specification, clarify requirements.
version: 1.1.0
---

# Feature Specification Authoring (`sdd-spec`)

This skill defines the process to author and clarify functional specifications in this project.
It captures observable behavior, boundary limits, and testable acceptance criteria before code design begins.

---

## 1. Principles of Specification

1. **Separate Intent from Implementation**:
   Specify *what* system behavior changes and *why*.
   Do not include premature implementation details.
   Do not specify internal class names, private functions, or database schemas.
2. **Explicit Scope Boundaries**:
   Every specification requires both In-Scope and Out-of-Scope sections.
   State excluded items explicitly to prevent scope creep.
3. **Testable Acceptance Criteria**:
   Formulate requirements using EARS patterns (Ubiquitous, Event-driven, State-driven, Unwanted event).
   Write concrete scenarios in Given/When/Then format.
4. **Proactive Clarification**:
   Identify ambiguous points and edge cases before authoring the plan.
   Ask targeted questions to verify user expectations.

---

## 2. Subagent Profile: `sdd-specifier`

When operating in multi-agent environments, invoke a dedicated `sdd-specifier` subagent:

- **Role**: Requirements Analyst and Specification Author.
- **Permissions**: Read-only codebase access, web search, and user messaging.
- **Strict Constraint**: Never edit source code files or test files.
- **Goal**: Produce an approved `.specs/<feature-id>/spec.md` document.

---

## 3. Specification Procedure

Follow these steps to produce a feature specification:

### Step 1: Initialize Specification Directory

Create the feature directory under `.specs/`:

```bash
mkdir -p .specs/<feature-id>
```

### Step 2: Interview the User

Examine the feature request and existing documentation.
Consult [references/clarification-matrix.md](./references/clarification-matrix.md) to identify edge cases.
Formulate 2 to 4 targeted clarification questions for the user:
- Ask about edge cases and error handling behavior.
- Ask about boundary conditions and performance expectations.
- Ask about explicitly excluded features.

### Step 3: Instantiate Specification Template

Copy the template [templates/spec.md](./templates/spec.md) to `.specs/<feature-id>/spec.md`.

### Step 4: Populate Functional Requirements

Write functional requirements using Easy Approach to Requirements Syntax (EARS):
- **Ubiquitous**: The system must [behavior].
- **Event-driven**: When [event happens], the system must [action].
- **State-driven**: While [system state], the system must [action].
- **Unwanted event**: If [error condition], then the system must [recovery action].

### Step 5: Define Acceptance Scenarios

Add concrete Given/When/Then scenarios for every functional requirement:
- Include at least one happy path scenario per requirement.
- Include at least one error or edge case scenario per requirement.

### Step 6: Verify User Approval

Present the completed `.specs/<feature-id>/spec.md` to the user.
Secure explicit user approval before proceeding to `sdd-plan`.

---

## 4. Verification & Quality Gate

Run the automated specification quality linter [scripts/check_spec.py](./scripts/check_spec.py):

```bash
uv run python .agents/skills/sdd-spec/scripts/check_spec.py .specs/<feature-id>/spec.md
```

Verify that the specification satisfies these criteria:

1. The document contains both In-Scope and Out-of-Scope sections.
2. Every acceptance scenario defines the initial context, trigger event, and observable outcome.
3. The specification contains zero private implementation details.
