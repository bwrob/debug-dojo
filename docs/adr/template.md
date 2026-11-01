---
diataxis: reference
purpose: Provide the standardized MADR template for drafting new architectural decision records.
---

# ADR-XXXX: Short Imperative Title

- **Status**:
  Proposed <!-- Proposed | Accepted | Rejected | Deprecated | Superseded by ADR-XXXX -->
- **Date**: YYYY-MM-DD
- **Deciders**: *List core maintainers*
- **Consulted**: *List consulted contributors or domain experts*
- **Informed**: *List informed community members or stakeholders*

## Context & Problem Statement

*Describe the context and problem statement. What technical challenge or architectural
trade-off requires resolution? What forces, requirements, and constraints apply?*

## Decision Drivers

- *Driver 1, e.g., zero runtime overhead or sub-millisecond import time*
- *Driver 2, e.g., strict static type checking with Pyrefly*
- *Driver 3, e.g., modular layer boundary enforcement via Tach*

## Considered Options

1. **Option 1**: *Description*
2. **Option 2**: *Description*
3. **Option 3**: *Description*

## Pros and Cons of the Options

The options below summarize the trade-offs considered for this decision.

### Option 1: Name

- :white_check_mark: **Good**: *Argument*
- :white_check_mark: **Good**: *Argument*
- :x: **Bad**: *Argument*

### Option 2: Name

- :white_check_mark: **Good**: *Argument*
- :x: **Bad**: *Argument*

## Decision Outcome

Chosen option: **"Option 1: *Name*"**, because
*concise justification explaining how it satisfies drivers*.

### Positive Consequences

- *Positive consequence 1*
- *Positive consequence 2*

### Negative Consequences / Trade-Offs

- *Negative consequence or mitigation required*

## Architecture & Boundary Compliance

- **Tach Layers**: *Impact on `tach.toml` modules or layer definitions*
- **Static Typing**:
  *Impact on Pyrefly type contracts, Protocols, or generic parameters*
- **Testing Strategy**: *How this invariant is validated in automated tests*
