# Diátaxis Documentation Architecture Reference

This reference describes the Diátaxis framework used in Project documentation.
Diátaxis separates technical documentation into four distinct quadrants based on
user need.

---

## 1. The Diátaxis 2x2 Matrix

Technical documentation serves two distinct needs:
1. **Practical Action** (assisting work) versus **Theoretical Knowledge** (assisting study).
2. **Acquisition** (learning) versus **Application** (serving a working user).

| | Practical (Action-Oriented) | Theoretical (Knowledge-Oriented) |
| :--- | :--- | :--- |
| **Learning (Acquisition)** | **Tutorials**<br/>Learning-oriented loop | **Explanation**<br/>Understanding-oriented concepts |
| **Working (Application)** | **How-To Guides**<br/>Task-oriented procedures | **Reference**<br/>Information-oriented facts |

---

## 2. The Four Quadrants

### Quadrant 1: Tutorials (Learning-Oriented)

- **Primary Question**: "Can you teach me how to do this?"
- **User Mindset**: Beginner. The user wants to learn through direct experience.
- **Typical Location**: `docs/getting-started.md`.
- **Tone & Style**:
  - Linear and step-by-step.
  - Inspires confidence through immediate working results.
  - Shows concrete commands with exact expected outputs.
- **What to Include**:
  - One proven sequence from start to finish.
  - Safe, deterministic commands.
  - Immediate feedback loops.
- **What to Exclude**:
  - Explanations of theoretical alternatives.
  - Exhaustive reference tables of flags.
  - Edge cases and advanced configurations.

### Quadrant 2: How-To Guides (Task-Oriented)

- **Primary Question**: "How do I solve this specific problem?"
- **User Mindset**: Competent user with a concrete real-world goal.
- **Typical Location**: `docs/guides/`, `docs/adr/`.
- **Tone & Style**:
  - Practical and focused on an outcome.
  - Assumes basic tool knowledge.
  - Direct execution steps without introductory hand-holding.
- **What to Include**:
  - Clear prerequisites.
  - Numbered, actionable steps.
  - Verification commands to confirm success.
- **What to Exclude**:
  - Basic tool introductions.
  - Deep historical or architectural rationale.
  - Exhaustive API dictionaries.

### Quadrant 3: Reference (Information-Oriented)

- **Primary Question**: "What is the exact machinery, parameter, or syntax?"
- **User Mindset**: Working engineer who needs accurate facts fast.
- **Typical Location**: `docs/reference.md`.
- **Tone & Style**:
  - Austere, fact-dense, and objective.
  - Structured tables and code signatures.
  - No narrative filler.
- **What to Include**:
  - Configuration keys, data types, and default values.
  - CLI commands, options, and flags.
  - API signatures, type parameters, and return types.
- **What to Exclude**:
  - Step-by-step walkthroughs.
  - Opinionated design debates.
  - Beginner introductions.

### Quadrant 4: Explanation (Understanding-Oriented)

- **Primary Question**: "Why was it designed this way? What are the trade-offs?"
- **User Mindset**: Architect or engineer seeking mental models and context.
- **Typical Location**: `docs/index.md`, `docs/adr/`.
- **Tone & Style**:
  - Discursive, analytical, and context-rich.
  - Discusses design decisions, historical context, and architectural trade-offs.
  - Uses diagrams to illustrate relationships.
- **What to Include**:
  - Conceptual rationale and mental models.
  - Trade-off analysis and why the team rejected alternatives.
  - System architecture diagrams.
- **What to Exclude**:
  - Command-by-command tutorials.
  - Raw reference tables or syntax sheets.
  - Task checklists.

---

## 3. Detecting Boundary Drift & When to Split

Documentation decay occurs when content drifts across quadrant boundaries.
Use this guide to detect drift:

| Document Quadrant | Symptom of Drift | Action Required |
| :--- | :--- | :--- |
| **Tutorial** | Adding tables of all CLI flags or deep design debates. | Extract flags to `docs/reference.md`. |
| **How-To Guide** | Re-explaining basic Python setup or tool installation. | Link to `docs/getting-started.md` or `docs/reference.md`. |
| **Reference** | Adding long narrative tutorials or opinionated stories. | Move step-by-step instructions to a How-To Guide. |
| **Explanation** | Pasting code blocks for concrete task implementation. | Move implementation steps to a How-To Guide. |

### Splitting Recipe

When a page collects content outside its declared purpose:
1. Create a new document in the correct quadrant.
2. Add the non-renderable frontmatter preamble stating its single purpose.
3. Move the out-of-scope content into the new page.
4. Replace the removed content in the original page with a Markdown link.
5. Register the new page in `project.nav` in `zensical.toml`.
