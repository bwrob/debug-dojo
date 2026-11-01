---
name: sdd
description: >-
  Coordinates the Spec-Driven Development (SDD) lifecycle from feature conception to verification.
  Orchestrates specification authoring, planning, implementation, and review using artifact boundaries and subagents.
  Triggers: sdd, spec driven dev, spec-driven development, feature spec, execute sdd, sdd runbook.
version: 1.2.0
---

# Spec-Driven Development Orchestrator (`sdd`)

This skill orchestrates the end-to-end Spec-Driven Development (SDD) lifecycle for this project.
It coordinates specification, planning, implementation, and review across dedicated subagents or sequential phases.

---

## 1. Core Principles & The Artifact Contract

1. **Artifact-Grounded Source of Truth**:
   The specification document is the primary source of truth.
   Code is a downstream artifact generated from the approved specification.
2. **Dedicated Workspace Location**:
   Store all feature artifacts in `.specs/<feature-id>/`:
   - `.specs/<feature-id>/spec.md`: Requirements and acceptance criteria.
   - `.specs/<feature-id>/plan.md`: Technical architecture and atomic tasks.
   - `.specs/<feature-id>/review.md`: Spec conformance and verification audit.
   Git ignores this directory to prevent repository clutter during active iteration.
3. **Context Isolation**:
   Do not mix specification debates with implementation code generation in one long session.
   Delegate distinct phases to specialized subagents or start fresh context windows.

---

## 2. Execution Modes: Supervised vs. Autonomous

The SDD orchestrator supports two operational modes:

| Mode | Trigger | Behavior |
| :--- | :--- | :--- |
| **Supervised Mode (Default)** | Default operation. | The agent stops after every step. It requests explicit developer approval before advancing. |
| **Autonomous Mode** | Explicit user request (for example: "run autonomously" or `/goal`). | The agent executes all steps continuously without intermediate approval stops if tests pass. |

If an automated test fails in autonomous mode, stop immediately and report the error to the user.

---

## 3. Subagent Roles & Responsibilities

In multi-agent environments, delegate each phase to an isolated subagent:

| Subagent Role | Purpose | Permissions | Output Artifact |
| :--- | :--- | :--- | :--- |
| **`sdd-specifier`** | Interactive requirements clarification and EARS syntax. | Read codebase, web search, ask user. | `.specs/<id>/spec.md` |
| **`sdd-planner`** | Architecture design and atomic task decomposition. | Read codebase, view files. | `.specs/<id>/plan.md` |
| **`sdd-implementer`** | Sequential TDD implementation of atomic tasks. | Edit files, run test commands. | Code and unit tests |
| **`sdd-reviewer`** | Grounded acceptance criteria audit and quality verification. | Read codebase, run test commands. | `.specs/<id>/review.md` |

In single-agent environments, execute each phase sequentially.
Clear mental state between phases.

---

## 4. End-to-End SDD Workflow

Follow these steps to develop a feature:

### Step 1: Initialize Feature Workspace

1. Create a dedicated git feature branch:
   ```bash
   git checkout -b feature/<feature-id>
   ```
2. Create the feature specification directory:
   ```bash
   mkdir -p .specs/<feature-id>
   ```

### Step 2: Author the Specification

Activate the `sdd-spec` skill.
If using subagents, invoke the `sdd-specifier` subagent.
Interview the user to resolve ambiguities.
Generate `.specs/<feature-id>/spec.md`.

> [!IMPORTANT]
> **Approval Stop 1 (Specification)**:
> If in Supervised Mode, present the specification to the developer and stop.
> Do not start planning until the developer explicitly approves the specification.

### Step 3: Author the Implementation Plan

Activate the `sdd-plan` skill.
If using subagents, invoke the `sdd-planner` subagent.
Read `.specs/<feature-id>/spec.md`.
Define component interactions, public contracts, and atomic tasks under 100 lines each.
Generate `.specs/<feature-id>/plan.md`.

> [!IMPORTANT]
> **Approval Stop 2 (Technical Plan)**:
> If in Supervised Mode, present the technical plan to the developer and stop.
> Do not write code until the developer explicitly approves the plan.

### Step 4: Execute Implementation via TDD

Activate the `sdd-implement` skill.
If using subagents, invoke the `sdd-implementer` subagent.
Iterate through the tasks in `.specs/<feature-id>/plan.md` sequentially.
For each task:
1. Write failing unit tests asserting acceptance criteria.
2. Implement the minimal code required to pass tests.
3. Run `uv run poe test`.
4. Run auto-fixers with `uv run poe fix`.
5. Mark the task complete in `plan.md`.

> [!IMPORTANT]
> **Approval Stop 3 (Implementation)**:
> If in Supervised Mode, present completed tasks and test results to the developer.
> Stop and wait for developer review before starting the conformance audit.

### Step 5: Review Specification Conformance & Public API

Activate the `sdd-review` skill.
If using subagents, invoke the `sdd-reviewer` subagent.
Compare the implemented diff against `.specs/<feature-id>/spec.md`.
Run public API verification:
```bash
uv run python .agents/skills/sdd-review/scripts/check_public_api.py --plan .specs/<feature-id>/plan.md
```
Generate `.specs/<feature-id>/review.md`.

> [!IMPORTANT]
> **Approval Stop 4 (Final Conformance & Public API)**:
> If in Supervised Mode, present the conformance scorecard and API diff.
> Stop immediately and verify all public API changes with the developer.

### Step 6: Finalize Quality Gate

Run full repository quality verification tasks:
```bash
uv run poe code-quality
```
After verification tasks pass, submit the pull request following `workflow-git`.

### Step 7: Archive Feature Specification

After pull request approval, archive the specification with [scripts/archive_feature.py](./scripts/archive_feature.py):

```bash
uv run python .agents/skills/sdd/scripts/archive_feature.py <feature-id>
```

This command moves artifacts from `.specs/<feature-id>/` into `docs/specs/<feature-id>/`.
It registers the feature in `docs/specs/index.md` to preserve permanent project memory.

---

## 5. Fast-Path SDD for Small Changes

For small features or bug fixes under 150 lines of change, use Fast-Path SDD:

1. **Single Artifact**: Combine requirements and task list into `.specs/<feature-id>/spec.md`.
2. **Omit Heavy Architecture**: Do not draw architecture diagrams or public contract matrices.
3. **Single Approval Stop**: Present the combined specification and task list to the developer once.
4. **Direct Implementation**: After developer approval, implement tasks with standard TDD.
5. **Fast Verification**: Run `uv run poe sdd-verify <feature-id>` before pull request submission.

---

## 6. Rollback & Task Reversion

If an implemented task introduces defects or fails review, revert it with [scripts/revert_task.py](./scripts/revert_task.py):

```bash
# Revert the most recently completed task
uv run poe sdd-revert <feature-id>

# Revert a specific commit SHA
uv run poe sdd-revert <feature-id> <commit-sha>
```

This protocol:
1. Reverts the Git commit cleanly with `git revert --no-edit`.
2. Resets the task checkbox from `[x]` back to `[ ]` in `.specs/<feature-id>/plan.md`.
3. Commits the plan update.

---

## 7. Verification & Quality Gate

Verify that the feature meets all project quality standards:

```bash
uv run poe test
uv run poe code-quality
```
