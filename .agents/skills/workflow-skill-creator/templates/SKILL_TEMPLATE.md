---
name: <skill-name>
description: >-
  <Summary explaining WHAT this skill does and WHEN to use it.
  Include clear intent triggers (e.g. "Use when asked to...")>.
version: 1.0.0
---

# <Skill Title> (`<skill-name>`)

<Brief 1-2 sentence overview of the domain and purpose of this skill.>

---

## 1. Core Principles & Invariants

1. **<Principle 1>**: <Actionable guideline, architectural boundary, or invariant.>
2. **<Principle 2>**: <Actionable guideline, architectural boundary, or invariant.>

---

## 2. Standard Workflow & Procedures

### Step 1: <Initial Phase>
<Actionable instructions, CLI commands, or decision trees written in ASD-STE100.>

```bash
uv run <command>
```

### Step 2: <Execution Phase>
<Actionable instructions. If templates are required, link to external templates
in `./templates/` instead of embedding large inline blocks.>

- See template: [templates/<name>.<ext>](./templates/<name>.<ext>)

---

## 3. Verification & Quality Gate

<Mandatory verification commands to confirm the workflow succeeded without regressions.>

```bash
uv run python .agents/skills/asd-ste100/scripts/ste-lint.py .agents/skills/<skill-name>/SKILL.md
uv run <verification-command>
```
