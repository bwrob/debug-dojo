---
diataxis: explanation
purpose: Record the architectural decision to document design choices using Architecture Decision Records (ADRs).
---

# ADR-0001: Record Architecture Decisions

- **Status**: Accepted
- **Date**: 2026-01-01
- **Deciders**: bwrob
- **Consulted**: Maintainers
- **Informed**: Contributors and Developers

## Context & Problem Statement

As **Debug Dojo** evolves, contributors and AI coding assistants
make architectural and technical choices (such as modular layer boundaries, static type
checking rules, dependency management, and serialization contracts). Without a
persistent record of the context, alternatives evaluated, and trade-offs accepted,
future maintainers face technical drift and risk inadvertently reversing intentional
design decisions.

## Decision Drivers

- **Knowledge Persistence**: Retain technical rationale alongside source code in version
  control.
- **Agent Alignment**: Ensure AI coding assistants understand architectural constraints
  before generating non-compliant code.
- **Traceability**: Pair automated tool boundaries (like **Tach**) with human-readable
  justifications.

## Considered Options

1. **Option 1**: Michael Nygard Architecture Decision Records (MADR) in Markdown under
   `docs/adr/`.
2. **Option 2**: Ephemeral discussion threads in GitHub Issues or Pull Requests.
3. **Option 3**: Unstructured notes in wiki or standalone README sections.

## Pros and Cons of the Options

The options below summarize the trade-offs considered for this decision.

### Option 1: Architecture Decision Records (MADR)

- :white_check_mark: **Good**: Version-controlled alongside source code in Git.
- :white_check_mark: **Good**: Automatically integrated into Zensical documentation
  site.
- :white_check_mark: **Good**: Machine-readable and easily digested by AI coding
  assistants.
- :white_check_mark: **Good**: Follows recognized open-source and enterprise standards.
- :x: **Bad**: Requires discipline to draft and review during architectural shifts.

### Option 2: GitHub Issues / Pull Request Discussions

- :white_check_mark: **Good**: Low friction to create during active development.
- :x: **Bad**: Fragmented across closed PRs, difficult to discover or audit
  systematically.
- :x: **Bad**: Vulnerable to repository migration or issue closure loss.

### Option 3: Unstructured Notes in Wiki

- :x: **Bad**: Separated from git commit history and code review gating.
- :x: **Bad**: Frequently becomes stale and out of sync with code changes.

## Decision Outcome

Chosen option: **"Option 1: Michael Nygard Architecture Decision Records (MADR) in
Markdown under `docs/adr/`"**, because storing version-controlled Markdown records
directly in the repository ensures that architectural intent remains permanently coupled
with codebase evolution.

### Positive Consequences

- Architectural decisions are discoverable in both git and the generated Zensical
  documentation site.
- AI coding assistants can reference `docs/adr/` when evaluating proposed modifications.
- Decisions undergo peer review via standard Pull Requests.

### Negative Consequences / Trade-Offs

- Maintainers must ensure new architectural paradigms are accompanied by an ADR.

## Architecture & Boundary Compliance

- **Tach Layers**: Any modification to `tach.toml` modules, layer hierarchies, or
  external dependencies requires an accompanying ADR reference.
- **Documentation**: All accepted ADRs must be registered in `docs/adr/index.md` and
  `zensical.toml`.
