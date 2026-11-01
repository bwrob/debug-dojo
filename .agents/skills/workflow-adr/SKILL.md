---
description: >-
  Workflow for proposing, drafting, reviewing, and updating Architecture Decision Records (ADRs) in this project.
  Enforces the MADR decision format, numbering sequences, status lifecycles, and architectural invariants.
  Mandatory whenever editing docs/adr/ or introducing a significant design change, even without prompt triggers.
  Use when proposing architectural choices, documenting design decisions, or superseding prior decisions.
  Triggers: adr, architecture decision record, architectural decision, record decision, create adr, document architecture, new adr.
name: workflow-adr
version: 1.0.0
---

# Architecture Decision Records (`workflow-adr`)

This skill provides the process to author, number, evaluate, and update
Architecture Decision Records (ADRs) in this project.

This project couples Tach architectural boundaries with ADRs in `docs/adr/`.
This preserves the rationale, context, and trade-offs of architectural invariants.

---

## 1. Lifecycle & Status Model

Each ADR follows a defined lifecycle:

| Status | Meaning |
| :--- | :--- |
| **`Proposed`** | Under design review. The team did not reach consensus yet. |
| **`Accepted`** | Approved by maintainers. Actively governs the codebase and architecture. |
| **`Rejected`** | Evaluated and declined. Kept in the archive to document why the team avoided an approach. |
| **`Superseded`** | Replaced by a later decision (for example, `Superseded by ADR-0004`). |
| **`Deprecated`** | No longer relevant because the architecture, platform, or scope changed. |

---

## 2. Directory & Naming Conventions

Store all ADRs in `docs/adr/`:

```text
docs/adr/
├── index.md                              # Chronological registry of all decisions
├── template.md                           # Master ADR authoring template
├── 0001-record-architecture-decisions.md # Baseline foundation
└── 0002-<short-imperative-title>.md      # Sequential decisions
```

- **Numbering**: Sequential 4-digit integers starting from `0001`.
- **Filename**: `000X-<kebab-case-title>.md` (for example, `0002-enforce-slotted-dataclasses.md`).
- **Title**: Imperative statement of the decision (for example, *Use Tach for Layer Boundaries*).

---

## 3. ADR Authoring Workflow

Follow these steps to draft or change an ADR:


### Step 1: Scan Existing Decisions & Determine Numbering

Scan `docs/adr/` to find the highest decision number. Check for related or conflicting decisions:

```bash
ls -1 docs/adr/
```

Determine the next sequential identifier (for example, `0002`).

### Step 2: Instantiate Template

Copy the template [templates/adr.md](./templates/adr.md) to
`docs/adr/000X-<kebab-case-title>.md`.

### Step 3: Populate Decision Sections

1. **Title & Metadata**:
   - Number and concise title.
   - Initial status: `Proposed` (or `Accepted` if agreed upon in issue/PR).
   - Date and deciders.
2. **Context & Problem Statement**:
   - What technical, organizational, or architectural problem requires a solution?
   - What constraints, performance budgets, or external dependencies apply?
3. **Decision Drivers**:
   - Key criteria (for example, type safety, memory footprint, cold-start latency).
4. **Considered Options**:
   - List 2 to 3 alternatives evaluated with pros and cons.
5. **Decision Outcome**:
   - Chosen option with technical justification.
6. **Consequences & Architectural Boundaries**:
   - Positive consequences (benefits gained).
   - Negative consequences (compromises or burdens accepted).
   - Impact on Tach layer boundaries (`tach.toml`) or Pyrefly typing contracts.

### Step 4: Register Decision in Documentation

1. Append the new ADR to the table in `docs/adr/index.md`.
2. Add the document path to `nav` and `project.plugins.llmstxt` in `zensical.toml`.
3. Preview the documentation locally:
   ```bash
   uv run poe docs-serve
   ```

### Step 5: Handling Superseded Decisions

When a new ADR replaces an earlier decision:

1. In the **new ADR**: add a reference in Context (`Supersedes [ADR-0002](0002-...).md`).
2. In the **old ADR**: update status to `Superseded by [ADR-000X](000X-...).md`.
3. Update the status badges in `docs/adr/index.md`.
