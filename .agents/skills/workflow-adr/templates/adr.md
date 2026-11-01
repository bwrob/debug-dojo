# ADR-[NUMBER]: [TITLE]

- **Status**: [STATUS] <!-- Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-XXXX -->
- **Date**: [YYYY-MM-DD]
- **Deciders**: [DECIDERS]
- **Consulted**: [CONSULTED]
- **Informed**: [INFORMED]

---

## Context & Problem Statement

[Describe the context and problem statement. What technical challenge or architectural trade-off requires a solution? What forces, requirements, and constraints apply?]

---

## Decision Drivers

- [Driver 1, for example, strict static type checking with Pyrefly]
- [Driver 2, for example, zero runtime overhead or sub-millisecond import time]
- [Driver 3, for example, modular layer boundary enforcement via Tach]

---

## Considered Options

1. **Option 1**: [Name of option 1]
2. **Option 2**: [Name of option 2]
3. **Option 3**: [Name of option 3]

---

## Pros and Cons of the Options

### Option 1: [Name of option 1]

- :white_check_mark: **Good**: [Positive argument]
- :white_check_mark: **Good**: [Positive argument]
- :x: **Bad**: [Negative argument]

### Option 2: [Name of option 2]

- :white_check_mark: **Good**: [Positive argument]
- :x: **Bad**: [Negative argument]

---

## Decision Outcome

Chosen option: **"Option [X]: [Name of option]"**, because [justification, for example, only option that satisfies driver 1 and driver 2 without introducing circular dependencies].

### Positive Consequences

- [Positive consequence 1]
- [Positive consequence 2]

### Negative Consequences / Trade-offs

- [Negative consequence or mitigation required]

---

## Architecture & Boundary Compliance

- **Tach Layers**: [How this decision affects `tach.toml` modules or layer definitions]
- **Static Typing**: [Impact on Pyrefly type contracts, Protocols, or generic parameters]
- **Testing Strategy**: [How automated tests check this architectural invariant]
