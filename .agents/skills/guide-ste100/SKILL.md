---
name: guide-ste100
description: >-
  Use when an agent must parse text without human review.
  Mandatory whenever writing or editing agent skills in .agents/skills/ or Python docstrings, even without prompt triggers.
  Serves as a clarity suggestion, not an enforced rule, in user documentation.
  Triggers: disambiguate, STE100 rewrite, apply Simplified Technical English, plain-language rewrite, controlled-language rewrite, rewrite so an agent cannot misread the text.
  Not for creative or marketing copy.
version: 0.5.0
---

# Simplified Technical English (`guide-ste100`)

<!-- ste-lint-disable -->
> [!NOTE]
> **Attribution**: Based on [`asd-ste100-skill`](https://github.com/danyuchn/asd-ste100-skill) (Dustin Yuchen Teng), [`asd-ste100-writer-skill`](https://github.com/blagoySimandov/asd-ste100-writer-skill) (Blagoy Simandov), [`SimpleEnglish`](https://github.com/AminBlg/SimpleEnglish) (Amin Boulegroun), [`ste-prompt`](https://github.com/menonpg/ste-prompt) (Prasanna Gautam Menon), [`ASD-STE100`](https://github.com/JAICHANGPARK/ASD-STE100) (Jaichang Park), and [`asd-ste100-checker`](https://github.com/sourdough-bread/asd-ste100-checker) (sourdough-bread), licensed under MIT. Extended with deterministic zero-NLP linter, automated fixer, and compliance scoring.
<!-- ste-lint-enable -->

ASD-STE100 is a controlled-language standard created for aerospace maintenance.
It eliminates ambiguity so AI agents, translation pipelines, and technicians parse instructions without human intervention.
Do not use this skill for creative or marketing text.

> [!IMPORTANT]
> **Enforcement Scope**: ASD-STE100 is strictly enforced for **agent skills** (`.agents/skills/`) and **Python docstrings**. It is not enforced as a rule in user-facing documentation (`docs/`), where it serves only as a suggestion for clear phrasing.

## Automated Verification & Fixing

Delegate mechanical checks to the deterministic standard-library linter and fixer:

```bash
# 1. Automatically fix contractions, Latin abbreviations, and unapproved phrases in-place
uv run python .agents/skills/guide-ste100/scripts/ste-lint.py --fix path/to/document.md

# 2. Check for remaining structural violations (sentence length, semicolons, modals, paragraph size)
uv run python .agents/skills/guide-ste100/scripts/ste-lint.py path/to/document.md
```

Options: `--fix` (apply safe 1:1 rewrites in-place), `--json` (structured output), `--baseline N` (tolerate N violations), `--disable <rules>` (silence rules), `--list-rules` (show all 17 rules), `--selftest`.

## Core Invariants

1. **Length Caps**: Limit instruction sentences to 20 words and descriptions to 25 words. Limit paragraphs to 6 sentences.
2. **Structure & Mood**: Active voice. Imperative mood for instructions. Put conditions first ("If the disk is full, delete temporary files").
3. **Hard Prohibitions**:
   - No semicolons (split into separate sentences).
   - No contractions (`don't` → `do not`, `it's` → `it is`).
   - No Latin abbreviations (`e.g.` → `for example`, `i.e.` → `that is`, `etc.` → list items).
   - No soft phrasal verbs (`spin up` → `start`, `kick off` → `begin`, `reach out` → `contact`).
   - No banned modals (`should`, `would`, `ought to` → state as fact or use `must` / imperative).
   - No marketing adjectives (`seamless`, `robust`, `cutting-edge`, `effortless`).
4. **Preserve Modality**: Keep hedges (`may`, `could`, `might have`). Never promote a hedge to a certainty.
5. **Untouchables**: Inline/fenced code, flags (`--fix`), config keys, URLs, and file paths are immune.

## Execution Modes

- **Strict**: Procedures, error messages, tool descriptions, prompts, inter-agent messages. Enforce all rules strictly.
- **STE-Flavored**: Explanatory docs, PRs, changelogs. Enforce structural rules, and treat lexical synonyms as advisory.

## Output Format

- **Default**: Output the rewritten text alone. Do not add explanations, preamble, or rule summaries.
- **On Request ("diff", "explain", "before/after")**: Output a Markdown table mapping original phrasing to simplified text, followed by the mode and violation count.

## Detailed References

For full rule breakdowns, word substitutions, and worked examples, see:
- [references/writing-rules.md](./references/writing-rules.md) — 9 official rule categories.
- [references/word-choices.md](./references/word-choices.md) — Unapproved words and phrases lookup table.
- [references/checklist.md](./references/checklist.md) — Pre-flight scan checklist.
- [references/use-cases.md](./references/use-cases.md) — Patterns for prompts, runbooks, changelogs, and UI copy.
- [examples/before-after.md](./examples/before-after.md) — Worked transformations.
