---
description: >-
  Workflow and standards for authoring clear, human-centered technical documentation in this project.
  Enforces information architecture, anti-AI-slop writing rules, single source of truth linking, and verification gates.
  Mandatory whenever writing, structuring, editing, updating, or reviewing documentation in docs/, even without prompt triggers.
  Triggers: write docs, doc authoring, documentation guide, docs workflow, document feature, write guide.
  Additional triggers: anti slop, single source of truth, in the docs, update docs, edit docs, clarify docs, review docs.
name: workflow-docs-authoring
version: 1.2.0
---

# Documentation Authoring Workflow (`workflow-docs-authoring`)

This skill defines the standards, writing guidelines, information architecture,
and verification procedures to author high-quality documentation in this project.

This project treats documentation as a primary product feature. Well-crafted documentation
respects the developer's time: it is concise, scannable, fact-dense, and free from
hollow filler.

---

## 1. The Golden Source of Truth: Do Not Repeat, Link

Documentation decay happens when multiple pages describe the same feature, configuration,
or architectural rule. When code changes, duplicate descriptions drift and provide
conflicting guidance.

Follow this primary rule: **Every fact, option, and workflow has exactly one canonical home.**

### Rules for Canonical Linking

1. **Do Not Duplicate Concepts**:
   - Never copy explanations across multiple doc pages, `README.md`, docstrings, or skills.
   - Describe a concept once in its canonical document. Link to that document
     whenever other pages reference it.
2. **Canonical Mapping**:
   - **Public Python APIs**: Do not write manual signature tables. Use `mkdocstrings`
     (`::: package.module`) or link directly to the source module in `src/`.
   - **Architecture Decisions**: Link to the specific record in `docs/adr/NNNN-*.md`.
     Do not summarize the rationale in multiple guides.
   - **Tool Syntax & Commands**: Link to the dedicated reference page or `.agents/skills/tool-*/SKILL.md`.
     Do not document third-party CLI flags across general pages.
   - **Workflows & Procedures**: Link to the relevant guide or `.agents/skills/workflow-*/SKILL.md`.
   - **Release Notes**: Maintain changes strictly in `docs/changelog.md`.
3. **Use Continuous-Tested Snippet Transclusion**:
   - When documentation requires code examples, do not copy code manually into
     markdown fences.
   - Store complete, runnable examples in `examples/` or `tests/`. Transclude them using
     `pymdownx.snippets`:
     ````markdown
     ```python
     --8<-- "examples/quickstart.py"
     ```
     ````
   - **Continuous Test Coverage**: Every transcluded snippet file must run in the test
     suite (`uv run poe test`) in CI. If code updates break the example, CI fails
     before the documentation drifts.
   - **Complete & Standalone**: Do not use lazy ellipses (`...`) or hide imports.
     A developer must be able to copy the snippet into a clean file and run it
     without missing references.
4. **Semantic Link Anchoring**:
   - Always write descriptive link text that identifies the exact target.
   - For example, write `[Pyrefly Type Configuration](...)`.
   - Never use generic anchor text like `click here`, `link`, or raw naked URLs.

---

## 2. Documentation-Driven Design: Documentation as the Interface Test

This project adopts Documentation-Driven Design as an architectural feedback loop.
Treat documentation not as a closing chore, but as an active test for your API ergonomics.

### Documentation as the Interface Smell Test

- **Draft in Lockstep**: Draft the tutorial or guide before or during code implementation.
- **Listen to Documentation Friction**: Explaining an option must not require long
  warnings or apologies for odd syntax. Treat prose friction as an interface smell.
- **Redesign the Interface**: Do not write more prose to compensate for clumsy architecture.
  Redesign the public API or CLI interface until the code example is simple, intuitive,
  and fast to document.

### Progressive Disclosure

Structure documentation to protect user focus and prevent cognitive overload:

1. **Focus on the 80% Main Path**:
   - In tutorials and guides, show the common sequence that serves most users.
   - Introduce concepts one by one.
2. **Quarantine Advanced Complexity**:
   - Do not distract beginners with internal plumbing, edge cases, or deep customization hooks.
   - Move advanced settings and complex integrations to dedicated reference pages or
     advanced guide sections. Link to them from the main flow.

### Editor Ergonomics & Explicit Typing

Developer experience depends on editor feedback:

- Include complete Python type annotations in all documented code examples.
- Check that snippets trigger accurate autocompletion and pass static type inspection
  (such as Pyrefly) in standard developer editors (VS Code, PyCharm, Neovim).

---

## 3. Human-First Writing: Anti-AI-Slop Standards

AI coding assistants frequently produce "AI slop": wordy, passive, generic prose that
says very little with many syllables. Project documentation must read as if authored by
an experienced human engineer who values clarity and precision.

### Banned AI Writing Patterns

1. **Throat-Clearing Openings**:
   - **Forbidden**: "In today's fast-paced software development landscape...",
     "It is important to remember that...", "In this guide, we will dive deep...".
   - **Approved**: State what the page does in the first sentence.
2. **Hollow Marketing Buzzwords**:
   - **Forbidden**: `seamless`, `seamlessly`, `robust`, `delve`, `game-changer`,
     `empower`, `unlock the power`, `testament to`, `pivotal role`, `crucial`.
   - **Approved**: Use factual, technical descriptions. State exact performance metrics,
     error boundaries, or capabilities.
3. **Circular Definitions & Stating the Obvious**:
   - **Forbidden**: "Configuration settings allow you to configure your settings."
   - **Approved**: Provide concrete configuration keys, types, and defaults immediately.
4. **Unbalanced Optimism**:
   - AI slop presents every tool as perfect. Real software has trade-offs.
   - Always document limitations, edge cases, failure modes, and when *not* to use a pattern.

### Positive Human Writing Invariants

- **Lead with Action**: Answer "What problem does this solve?" or "What command do I run?"
  in the first paragraph.
- **Condition-Before-Instruction**: Place prerequisites and conditions before the action.
  Write "When errors occur, run `uv run poe fix`", not
  "Run `uv run poe fix` when errors occur".
- **The Troubleshooting Triad**: When writing error recovery sections, structure each
  item into three parts:
  1. **Symptom**: The exact error message or exit code.
  2. **Root Cause**: The technical reason why the failure occurred.
  3. **Resolution**: The actionable command or edit that resolves the issue.
  Use [templates/troubleshooting_section.md](./templates/troubleshooting_section.md)
  as the skeleton.
- **Active Voice & Imperative Mood**: Write "Run `uv run poe test`", not
  "The test suite can be executed by running...".
- **Visual Scannability**: Use tables for options, Mermaid for sequence flows, and
  GitHub alert callouts (`> [!NOTE]`, `> [!TIP]`, `> [!WARNING]`) for critical context.
- **High Signal-to-Noise**: If you can delete a sentence without losing technical meaning,
  delete it.

---

## 4. Information Architecture (Diátaxis Model)

This project organizes documentation into four distinct quadrants based on user intent:

| Quadrant | Purpose | Typical Location | Focus & Style |
| :--- | :--- | :--- | :--- |
| **Tutorial** | Learning-oriented loop for newcomers | `docs/getting-started.md` | Step-by-step guidance. Builds confidence with an immediate working result. |
| **How-To Guide** | Task-oriented problem solving | `docs/guides/`<br/>`docs/adr/` | Problem-focused recipes. Assumes basic knowledge and shows exact execution steps. |
| **Reference** | Information-oriented technical facts | `docs/reference.md` | Concise, fact-dense tables, configuration keys, CLI syntax, and API symbols. |
| **Explanation** | Understanding-oriented rationale | `docs/index.md`<br/>`docs/adr/` | Context, architecture invariants, design rationale, and mental models. |

### Mandatory Non-Renderable Preamble & Splitting Rule

Every documentation page must start with a non-renderable YAML
preamble that defines its Diátaxis classification and exact purpose:

```yaml
---
diataxis: tutorial | how-to | reference | explanation
purpose: State the single focused purpose of this page.
---
```

- **Orientation**: Identifies page scope immediately for AI agents and human
  developers to prevent conceptual drift.
- **Single Focus & Splitting Rule**: A page must address only its declared
  purpose. If a page collects content outside its declared purpose, do not expand
  the file. Split the extra material into a separate page in the correct quadrant
  and link between them.
- **Non-Renderable**: Zensical treats this frontmatter as metadata, keeping rendered
  HTML output clean.
- **Tutorial Fast Loop (< 5 Minutes)**: In any tutorial, ensure the user achieves
  a working result in the first viewport within 5 minutes. Do not front-load
  theoretical setup. Defer conceptual discussions to `explanation` pages via cross-links.

For deep-dive quadrant rules, writing guidance, and drift detection recipes, consult
[references/diataxis.md](./references/diataxis.md).

---

## 5. End-to-End Authoring Workflow

Follow this procedure when creating or editing documentation:

### Step 1: Scope & Placement
1. Identify the document quadrant in the Diátaxis model.
2. Choose the file path in `docs/` (for example, `docs/guides/topic.md` or `docs/reference.md`).
3. Register the page in `project.nav` in `zensical.toml`.

### Step 2: Documentation-Driven Design & Interface Check
1. Draft the usage guide or tutorial before or in lockstep with the code implementation.
2. Check for interface friction. If explaining the interface requires defensive prose
   or complex caveats, redesign the API instead of writing more documentation.

### Step 3: Establish the Golden Source
1. Check existing documentation, source code, and skills to see if the concept is already explained.
2. If it is already documented, insert a Markdown link to that location rather than writing new text.
3. If new, draft the canonical explanation here so other pages can link to it.

### Step 4: Author the Content
1. Use [templates/page_template.md](./templates/page_template.md) as the starting skeleton.
2. Apply progressive disclosure: focus on the primary 80% use path and quarantine advanced settings.
3. Ensure code examples are complete, standalone runnable, and typed for clean editor autocompletion.
4. Transclude tested examples from `examples/` or `tests/` using `pymdownx.snippets`.
5. Structure options and flags into Markdown tables.
6. Add Mermaid diagrams or terminal snippets for visual clarity.

### Step 5: Audit & Self-Review
1. Review the draft against [references/anti-slop-checklist.md](./references/anti-slop-checklist.md).
2. Ensure the tone is direct, active, and human-centered without hollow marketing buzzwords.
3. Keep prose natural and readable.
   > [!NOTE]
   > **STE-100 Scope**: The ASD-STE100 standard is strictly enforced for **agent skills** (`.agents/skills/`) and **Python docstrings**, NOT user documentation (`docs/`). When authoring documentation, STE-100 principles (such as conciseness, active voice, and condition-before-instruction) serve as helpful suggestions for clarity, never as rigid rules or blocking gates. Do not force documentation prose into artificial STE-100 compliance.

### Step 6: Format & Lint
Format tables and markdown structure:
```bash
uv run poe format-md
uv run poe lint-md
```

### Step 7: Check Tests, Build & Links
Check that snippet unit tests pass, and all doc links and anchors resolve:
```bash
uv run poe test
uv run poe docs-build
```

---

## 6. Templates and References

- [templates/page_template.md](./templates/page_template.md) — Standard markdown skeleton for new documentation pages.
- [templates/troubleshooting_section.md](./templates/troubleshooting_section.md) — Standardized Troubleshooting Triad schema.
- [references/diataxis.md](./references/diataxis.md) — Diátaxis quadrant reference, writing rules, and drift detection guide.
- [references/anti-slop-checklist.md](./references/anti-slop-checklist.md) — Pre-flight review checklist.
