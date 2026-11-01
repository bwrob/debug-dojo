---
name: sdd-plan
description: >-
  Translates functional specifications into technical implementation plans.
  Defines component architectures, layer boundaries, interface contracts, and atomic task breakdowns.
  Mandatory whenever converting an approved spec into a plan or task list.
  Triggers: plan implementation, sdd plan, technical plan, task breakdown, architecture plan.
version: 1.1.0
---

# Technical Implementation Planning (`sdd-plan`)

This skill translates approved functional specifications into actionable technical plans.
It establishes component boundaries, typing contracts, and atomic tasks before code execution starts.

---

## 1. Core Principles & Architecture Invariants

1. **Direct Specification Traceability**:
   Every architectural decision and task must link directly to `.specs/<feature-id>/spec.md`.
   Do not introduce speculative abstractions or unrequested frameworks.
2. **Project Architecture Rules**:
   - Python 3.12+ syntax: Use PEP 695 generics (`def func[T]()`, `type Alias = ...`).
   - Immutable data models: Use `@dataclass(frozen=True, slots=True)`.
   - Structural subtyping: Use `typing.Protocol` instead of concrete inheritance.
   - Layer boundaries: Respect unidirectional dependencies in `tach.toml` (`cli` -> `core`).
   - Complexity cap: Maintain cognitive complexity of 10 or less per function.
3. **Atomic Task Decomposition**:
   Break implementation into small tasks under 50 to 100 lines of change each.
   Order tasks strictly by dependency:
   1. Data models and protocols
   2. Core domain transformations
   3. Public interfaces or CLI commands
   4. Documentation and docstrings
   5. Integration tests
4. **Per-Task Verification Gates**:
   Every task must specify an explicit, hermetic verification command (for example, `uv run poe test`).

---

## 2. Subagent Profile: `sdd-planner`

When operating in multi-agent environments, invoke a dedicated `sdd-planner` subagent:

- **Role**: Software Architect and Implementation Planner.
- **Permissions**: Read-only codebase access and file viewing.
- **Strict Constraint**: Never edit source code files or test files.
- **Goal**: Produce an approved `.specs/<feature-id>/plan.md` document.

---

## 3. Planning Procedure

Follow these steps to produce an implementation plan:

### Step 1: Ingest the Specification

Read `.specs/<feature-id>/spec.md`.
Identify all functional requirements and acceptance scenarios.
Inspect existing codebase modules to identify integration points.

### Step 2: Instantiate Plan Template

Copy the template [templates/plan.md](./templates/plan.md) to `.specs/<feature-id>/plan.md`.

### Step 3: Design Component Layout

Describe component interactions and data flow.
Create a Mermaid diagram illustrating component relationships.
Verify compliance with layer boundaries defined in `tach.toml`.

### Step 4: Define Public Contracts

Draft public protocols, frozen slotted dataclasses, and function signatures.
Verify import paths and type parameter syntax.

### Step 5: Construct Atomic Task Checklist

Create sequential tasks with checkbox format (`- [ ] **Task N: ...**`).
For each task:
- State exact files created or modified.
- State the specific requirement ID addressed.
- Provide the exact verification command.

### Step 6: Verify User Alignment

Present `.specs/<feature-id>/plan.md` to the user.
Secure explicit approval before starting `sdd-implement`.

---

## 4. Verification & Quality Gate

Verify that the plan satisfies these criteria:

1. Every requirement in `spec.md` maps to at least one atomic task.
2. Every task contains an explicit verification command.
3. No task requires more than 100 lines of estimated code change.
4. Layer dependencies flow unidirectionally without circular imports.
