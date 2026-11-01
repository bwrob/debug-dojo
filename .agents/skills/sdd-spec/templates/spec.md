# Feature Specification: [Feature Name]

- **Feature Identifier**: `[feature-id]`
- **Status**: Draft | Under Review | Approved
- **Author**: [Author / Agent]
- **Created**: YYYY-MM-DD
- **Target Release**: [Version or Milestone]

---

## 1. Problem Statement & User Value

### Problem
[Describe the problem or limitation this feature solves.]

### User Value
[Explain how users or developers benefit from this solution.]

---

## 2. User Personas & Scenarios

- **Persona**: [For example: Library consumer, CLI operator, API integrator]
- **Scenario**: [Describe primary user journey and expected outcome.]

---

## 3. Scope Boundaries

### In-Scope
- [Explicit capability or behavior 1]
- [Explicit capability or behavior 2]

### Out-of-Scope
- [Explicitly excluded behavior or future extension 1]
- [Explicitly excluded behavior or future extension 2]

---

## 4. Functional Requirements

Write functional requirements using EARS patterns:
- *Ubiquitous*: The system must [behavior].
- *Event-driven*: When [event], the system must [action].
- *State-driven*: While [state], the system must [action].
- *Unwanted event*: If [error occurs], then the system must [recovery action].

### Requirement 1: [Short Title]
- **ID**: `REQ-001`
- **Statement**: [Requirement statement using EARS syntax.]
- **Rationale**: [Reason for this rule.]

### Requirement 2: [Short Title]
- **ID**: `REQ-002`
- **Statement**: [Requirement statement using EARS syntax.]
- **Rationale**: [Reason for this rule.]

---

## 5. Non-Functional Requirements

- **Type Safety**: Full type annotations conforming to Python 3.12+ and Pyrefly strict mode.
- **Complexity**: Maximum cognitive complexity of 10 per function.
- **Performance**: [Execution time, memory budgets, or I/O constraints if applicable.]
- **Dependencies**: No unauthorized external dependencies.

---

## 6. Acceptance Criteria

Define concrete scenarios using Given / When / Then format.

### Scenario 1: [Happy Path Scenario]
- **Given** [precondition or initial state]
- **When** [action occurs]
- **Then** [expected observable outcome]

### Scenario 2: [Error or Edge Case Scenario]
- **Given** [invalid input or exceptional state]
- **When** [action occurs]
- **Then** [expected handled error or exception raised]

---

## 7. Open Questions & Clarifications

- [ ] Question 1: [Pending clarification from maintainer or user]
