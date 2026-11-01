---
diataxis: reference
purpose: Catalog all Architectural Decision Records (ADRs) recorded in the project and track their status.
---

# Architecture Decision Records (ADRs)

Architecture Decision Records capture significant technical, structural, and
architectural choices made throughout the lifecycle of
**Debug Dojo**.

Zenith pairs automated architectural boundary enforcement using **Tach** with ADRs to
preserve the rationale, trade-offs, and invariants behind our codebase design.

## Decision Lifecycle

Every record follows a defined status model:

| Status         | Badge                    | Description                                                                  |
| :------------- | :----------------------- | :--------------------------------------------------------------------------- |
| **Proposed**   | :hourglass_flowing_sand: | Under maintainer and community review; not yet accepted.                     |
| **Accepted**   | :white_check_mark:       | Formally approved; actively governs codebase architecture.                   |
| **Rejected**   | :x:                      | Evaluated and declined; retained to document why an alternative was avoided. |
| **Superseded** | :arrow_right:            | Replaced by a subsequent architectural decision.                             |
| **Deprecated** | :warning:                | No longer relevant due to structural changes.                                |

## Architectural Decision Log

| Number                                                | Title                         | Status                      | Date                            |
| :---------------------------------------------------- | :---------------------------- | :-------------------------- | :------------------------------ |
| **[ADR-0001](0001-record-architecture-decisions.md)** | Record Architecture Decisions | :white_check_mark: Accepted | 2026-01-01 |

## Proposing a New ADR

To propose a new decision:

1. Review the [ADR skill][adr-skill] for workflow instructions.
2. Copy [template.md](template.md) to `docs/adr/000X-<kebab-case-title>.md`.
3. Submit a pull request detailing Context, Decision Drivers, Evaluated Options, and
   Consequences.

[adr-skill]: <https://github.com/bwrob/debug-dojo/blob/main/.agents/skills/workflow-adr/SKILL.md>
