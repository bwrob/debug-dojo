---
description: >-
  Workflow and standards for creating modular agent skills in this repository.
  Enforces progressive disclosure, structured directories, external template separation,
  standard prefix taxonomy, and ASD-STE100 writing standards.
  Mandatory whenever creating, editing, refactoring, or modularizing agent skills in .agents/skills/, even without prompt triggers.
  Triggers: create skill, new skill, add skill, author skill, modular skill, skill template.
name: workflow-skill-creator
version: 1.0.0
---

# Agent Skill Creator (`workflow-skill-creator`)

This skill defines the standards, directory conventions, prefix taxonomy, and workflows
to create agent skills in this project.

Agent skills extend coding assistants with specialized runbooks, workflows,
and tool knowledge. They operate under **progressive disclosure**.
The runner loads only the skill `name` and `description` into initial context.
It reads the full content only when activated.

---

## 1. Skill Prefix Taxonomy & Grouping

Every skill in the project must belong to one of five standardized prefix groups:

| Prefix | Domain & Scope | Examples |
|---|---|---|
| **`sdd-*`** | **Spec-Driven Development Suite**<br/>End-to-end specification authoring, technical planning, TDD implementation, and quality review. | `sdd`, `sdd-spec`, `sdd-plan`, `sdd-implement`, `sdd-review`. |
| **`tool-*`** | **Tool Mechanics & Syntax**<br/>Runbooks and syntax guides for specific external tools, compilers, linters, or libraries. | `tool-uv`, `tool-ruff`, `tool-pytest`, `tool-tach`, `tool-docker`, `tool-fastapi`. |
| **`workflow-*`** | **Lifecycle & Multi-Step Procedures**<br/>Operational processes, version control, release ceremonies, audits, and checklists. | `workflow-git`, `workflow-code-review`, `workflow-changelog`, `workflow-adr`, `workflow-setup`. |
| **`guide-*`** | **Engineering Conventions & Style**<br/>Invariants, coding paradigms, architecture patterns, and technical writing rules. | `guide-python`, `guide-ste100`, `guide-api-design`. |
| **`domain-*`** | **Reserved: Project Business Logic**<br/>**Reserved exclusively for the author of the instantiated project.** Documents business rules, domain models, and application workflows. | `domain-billing`, `domain-auth`, `domain-data-pipeline`. |

> [!IMPORTANT]
> The `domain-*` prefix is strictly reserved for project authors. No `domain-*` skills ship by default so the application namespace remains clean.

---

## 2. Skill Complexity Tiering

Select the structure based on skill complexity:

### Tier A: Simple Skill (Single File)
- **When to Use**: Straightforward procedures, tool guides, or concise workflows
  under 100–150 lines without boilerplate.
- **Structure**: A single `SKILL.md` file at `.agents/skills/<prefix>-<name>/SKILL.md`.
- **Constraint**: Do not create subdirectories for single-page instructions.

### Tier B: Complex Skill (Structured Directory)
- **When to Use**: Workflows with templates, reference manuals, multi-file examples,
  or helper scripts.
- **Structure**: An organized directory following the canonical pattern:
  ```text
  .agents/skills/<prefix>-<name>/
  ├── SKILL.md          # Required: Lean core workflow, decision logic, and frontmatter
  ├── templates/        # Required if templates exist: External templates in separate files
  ├── examples/         # Optional: Multi-file recipes or concrete implementations
  ├── references/       # Optional: Technical manuals, specifications, and cheat-sheets
  └── scripts/          # Optional: Executable automation or validation scripts
  ```

---

## 3. Hard Architectural Rules

### Rule 1: Place Templates in Dedicated Files
- **Never embed large templates inline**: Do not include document skeletons, boilerplate
  code, config files, or report formats directly in `SKILL.md`.
- **Store in `templates/`**: Place each template in a file under `templates/`
  (for example, `templates/changelog.md` or `templates/review_output.md`).
- **Use relative links**: Link to the template file from `SKILL.md` using relative
  Markdown links: `[templates/SKILL_TEMPLATE.md](./templates/SKILL_TEMPLATE.md)`.

### Rule 2: Move Lengthy References and Examples to Subdirectories
- **References (`references/`)**: Split technical manuals, plugin lists, or API
  specifications into separate documents (such as `references/hypothesis.md`).
- **Examples (`examples/`)**: Store complete recipes, sample scripts, or multi-file
  demonstrations in `examples/` instead of inline code blocks.

### Rule 3: Maintain Progressive Disclosure and Lean `SKILL.md`
- Focus `SKILL.md` on triggers, decision paths, and core step-by-step instructions.
- Ensure the model can read `SKILL.md` in one pass. Read sub-files on demand.

### Rule 4: Write in Simplified Technical English (ASD-STE100)
- Follow the [guide-ste100](../guide-ste100/SKILL.md) skill when authoring prose.
- Write short, unambiguous, active-voice sentences.
- Keep procedural sentences under 20 words. Keep descriptive sentences under 25 words.
- Do not use semicolons, phrasal verbs, nominalizations, or marketing adjectives.
- Run the STE linter to verify compliance:
  ```bash
  uv run python .agents/skills/guide-ste100/scripts/ste-lint.py .agents/skills/<name>/SKILL.md
  ```

### Rule 5: Select One Activation Mode
Free-running agents select skills from the `description` text only.
Write the description so that the agent cannot miss a required skill.
Select one of these three modes:
- **Mandatory**: The skill enforces a repository convention for a file domain.
  Start the activation sentence with `Mandatory whenever`.
  Name the domain paths and end with `even without prompt triggers`.
  Add the domain-to-skill mapping to `AGENTS.md`.
- **On demand**: The skill is a reference or a tool guide.
  Start the activation sentence with `Use when`.
  List the tool names, commands, and error types in `Triggers:`.
- **Manual only**: The skill has external side effects or a high cost.
  Examples: it pushes to a remote, clones external repositories,
  rebuilds the environment, or dispatches several subagents.
  Set `disable-model-invocation: true` in the frontmatter.
  Add the sentence `Runs only when explicitly requested` to the description.
  Keep manual-only skills to a minimum.

---

## 4. Skill Creation Workflow

Follow these steps to create a new skill:

### Step 1: Select Prefix Group and Tier
1. Select one of the valid prefixes: `sdd-`, `tool-`, `workflow-`, `guide-`, or `domain-`.
2. Select Tier A (single `SKILL.md`) or Tier B (structured directory).
3. If Tier B, initialize the directory layout:
   ```bash
   mkdir -p .agents/skills/<prefix>-<name>/{templates,examples,references,scripts}
   ```

### Step 2: Author Frontmatter and Core Instructions
1. Copy [templates/SKILL_TEMPLATE.md](./templates/SKILL_TEMPLATE.md) to
   `.agents/skills/<prefix>-<name>/SKILL.md`.
2. Craft the YAML frontmatter block:
   - **`name`**: Lowercase, hyphenated with prefix (for example, `workflow-changelog` or `domain-billing`).
   - **`description`**: Summary stating *what* the skill does and *when* to use it,
     including explicit triggers.
3. Write clear, step-by-step instructions following ASD-STE100 standards.

### Step 3: Extract Templates and References
1. Extract file templates into `templates/<filename>`.
2. Extract reference tables or manuals into `references/<filename>`.
3. Extract complete code examples into `examples/<filename>`.
4. Link all extracted assets from `SKILL.md` with relative links.

### Step 4: Register the Skill
1. Place the skill directory in `.agents/skills/<prefix>-<name>/`.
2. Add the skill to the skills list in `AGENTS.md`.
3. If the skill uses `Mandatory` or `Manual only` activation, update the domain activation list in `AGENTS.md`.

### Step 5: Verify Formatting and Tests
Run the verification suite:
```bash
uv run python .agents/skills/guide-ste100/scripts/ste-lint.py .agents/skills/<name>/SKILL.md
uv run poe check-skills
uv run poe code-quality
```
