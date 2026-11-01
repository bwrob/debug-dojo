# Anti-AI-Slop & Quality Review Checklist

Use this checklist before you merge documentation changes or create pull requests.

## 1. Anti-AI-Slop & Writing Mechanics

- [ ] **No Throat-Clearing Openings**:
  - Does the first paragraph state the purpose immediately?
  - Delete openers like "In this guide, we will explore..." or "In today's fast-paced world...".
- [ ] **No Banned Buzzwords**:
  - The document must not contain: `seamless`, `seamlessly`, `robust`, `delve`,
    `game-changer`, `testament to`, `empower`, `unlock`, `pivotal`, `crucial role`.
- [ ] **Condition-Before-Instruction**:
  - Are prerequisites and conditions placed before the action?
  - Example: "When errors occur, run `uv run poe fix`", not "Run `uv run poe fix` when errors occur".
- [ ] **Semantic Link Text**:
  - Does link text describe the exact target?
  - Eliminate generic text like "click here", "link", "read more", or naked URLs.
- [ ] **No Hollow Filler or State-the-Obvious**:
  - Delete sentences that define words in a circular fashion.
  - Delete generic advice that lacks concrete commands or files.
- [ ] **Concrete Negative Space**:
  - Are limitations, trade-offs, and failure modes documented honestly?
  - Does the page state when *not* to use a feature or approach?
- [ ] **Human Voice & Active Tone**:
  - Are instructions written in the active voice with the imperative mood?
  - Is the second person ("you") used naturally without excessive hedging?

## 2. Golden Source of Truth & Architecture Audit

- [ ] **Documentation-Driven Design**:
  - Is the interface simple to explain?
  - Does the text avoid long apologies or defensive warnings for odd API behavior?
- [ ] **Single Source Principle**:
  - Is any explanation duplicated from another page, `README.md`, or code docstrings?
  - If a concept exists elsewhere, replace the repeated prose with a Markdown link.
- [ ] **No Hardcoded API Duplication**:
  - Are public Python APIs referenced via `mkdocstrings` (`::: path.to.module`) or links?
  - Are architectural decisions linked to `docs/adr/` records?
- [ ] **Complete & Standalone Snippets**:
  - Are code examples complete without lazy ellipses (`...`) or hidden imports?
  - Can a developer copy the snippet into a clean file and run it directly?
- [ ] **Tested Snippet Transclusion**:
  - Are non-trivial code examples included via `pymdownx.snippets` (`--8<--`)
    rather than copied manually?
  - Does every transcluded example file run inside the test suite in CI?
- [ ] **Editor Ergonomics & Typing**:
  - Do code snippets include explicit Python type annotations?
  - Do snippets pass static type inspection and trigger clean editor autocompletion?
- [ ] **Progressive Disclosure**:
  - Does the guide focus on the primary 80% path without cognitive dumps?
  - Does the page place advanced configurations in dedicated reference sections?
- [ ] **Tutorial Speed (< 5 Minutes)**:
  - If the page is a tutorial, does the user achieve a working result in the first viewport?
  - Is background theory deferred to explanation documents?
- [ ] **Troubleshooting Triad**:
  - Do error sections follow the three-part schema: *Symptom*, *Root Cause*, *Resolution*?

## 3. Structural & Technical Verification

> [!NOTE]
> **ASD-STE100 Scope**: ASD-STE100 is strictly enforced on **agent skills** (`.agents/skills/`) and **Python docstrings**, not on user documentation in `docs/`. In documentation, STE-100 guidelines serve as suggestions for clarity, not rigid enforcement gates.

- [ ] **Scannability**:
  - Are options presented in aligned Markdown tables rather than paragraphs?
  - Are workflows illustrated with Mermaid diagrams where relationships exist?
- [ ] **Format & Linting**:
  - Run `uv run poe format-md` to format tables and text.
  - Run `uv run poe lint-md` to check rumdl compliance.
- [ ] **Strict Link Check**:
  - Run `uv run poe docs-build` to check for zero broken links, invalid anchors, or missing references.
