# AGENTS.md

Operational guidelines, architectural conventions, and workflows for AI coding
assistants working in **Debug Dojo**.

## Project Stewardship

When working in this repository, your primary responsibility is to the long-term health
of the project, its users (both human and agent), and its maintainers—not merely
satisfying the immediate prompt with the shortest possible patch. Act as the first line
of defense against technical debt, architectural drift, and low-quality contributions by
enforcing end-to-end type safety, clean public abstractions, comprehensive test
coverage, and accurate documentation.

## Pre-Flight Checks

Before editing code or running tasks, ensure a clean, isolated environment:

1. Check repository status with `git status`. Do not make edits when uncommitted changes
   exist without explicit user consent.
2. Confirm remotes and branches before committing or pushing changes. Use git worktrees
   or dedicated feature branches for non-trivial tasks.
3. Run all commands inside the hermetic project environment using `uv run <command>` or
   `uv run poe <task>`. Never use global or system Python environments directly.
4. When creating temporary or scratch files, always place them in the `.temp/`
   directory. Never pollute the workspace root or tracked directories with temporary
   files.

## Operational Workflows

- **Environment & Packages**: Always use **`uv`**. Never use `pip`, `poetry`, or
  virtualenv directly.
  - Sync environment: `uv sync`
  - Add dependency: `uv add <package>` or `uv add --group <group> <package>`
  - Run commands in environment: `uv run <command>`
- **Temporary Files**: When creating temporary files, scratch scripts, or intermediate
  test outputs, always store them in the `.temp/` directory.
- **Task Runner**: All development tasks are managed through **Poe the Poet**.
  Do not guess command flags or invoke linters directly. Run:

  ```bash
  uv run poe --help
  ```

- **Verification Gate**: Before proposing or finalizing changes, always verify
  your work using:
  - `uv run poe test` (or `uv run poe test-fast`)
  - `uv run poe code-quality`
  - `uv run prek run --all-files`
  - `uv run poe fix` (to auto-fix formatting and spelling where applicable; always
    re-read files modified by `poe fix` or `prek` before making further edits)
  - `uv run poe clean` (to purge build artifacts and stale caches)
- **CI Monitoring on Push**: Never leave work unmonitored after `git push`. Track the
  triggered CI runs with `gh run watch` or `gh run list`. If a remote check fails,
  inspect the failure immediately (`gh run view <run-id> --log-failed`), reproduce,
  fix, and verify until all checks pass.
- **Tool Guidance**: For tool usage and common configuration changes,
  consult the corresponding skill in `.agents/skills/tool-*/SKILL.md`.
- **Reproduce-First Bug Scoping**: When fixing a bug, first reproduce the failure with a
  minimal test, trace the root cause, and search the codebase for sibling occurrences of
  the same pattern before editing production code.
- **Complexity Reset Rule**: If a fix or implementation starts requiring layered hacks,
  defensive workarounds, or fighting the type checker, stop and re-evaluate the design
  from first principles rather than piling on patches.
- **AI Contribution Policy**: All contributions must adhere to `AI_POLICY.md`
  for human review, local test verification, and tool disclosure.
- **Automatic Skill Activation by Domain**: When working in specific project domains,
  agents must activate and follow the corresponding workflow skill unconditionally, even
  without explicit prompt triggers:
  - **Documentation (`docs/`)**: Always activate and adhere to
    `workflow-docs-authoring`.
  - **Pre-PR & Code Audits**: Always activate and adhere to `workflow-code-review`.
  - **Architecture Decisions (`docs/adr/`)**: Always activate and adhere to
    `workflow-adr`.
  - **Changelog & Releases (`docs/changelog.md`)**: Always activate and adhere to
    `workflow-changelog`.
  - **Python Implementation & Refactoring**: Always adhere to `guide-python`.
  - **Skill Authoring (`.agents/skills/`)**: Always activate and adhere to
    `workflow-skill-creator` and `guide-ste100`.
  - **Git Operations (branches, commits, PRs)**: Always activate and adhere to
    `workflow-git`.
  - **Spec-Driven Features (`specs/`)**: Activate the matching `sdd-*` phase skill.
  - **Manual Only**: Never self-activate skills marked
    `disable-model-invocation: true` (`workflow-setup`, `workflow-docs-consumers`).
    Run them only on explicit user request.
- **Inline Lint Suppression**: `# noqa` comments are forbidden. Where a rule
  genuinely conflicts with required code, use the Ruff ignore directive
  `# ruff: ignore[full-rule-name]` with a rationale comment (see the
  `tool-ruff` skill, including the line-1 placement rule for module-level
  diagnostics).

## Project Instructions Discovery & Compatibility

- **Multi-Agent Discovery & Settings**: Instruction files and configuration profiles are
  maintained in the repository root for seamless compatibility across supported AI
  coding tools:
  - **Google Gemini CLI & Antigravity**: `.gemini/settings.json`
    (`contextFileName: "AGENTS.md"`) and `.agents/skills/`.
  - **OpenAI Codex CLI**: `.codex/config.toml` (auto-discovering `AGENTS.md` and setting
    the `workspace-write` sandbox) and `.codex/agents/*.toml` (project subagents).
  - **Claude Code**: `CLAUDE.md` symlink (`ln -s AGENTS.md CLAUDE.md`) and
    `.claude/settings.json` (pre-authorizing hermetic `uv run poe:*` commands).
- **Scope Hierarchy**: When exploring subdirectories, check for nested `AGENTS.md` or
  `CLAUDE.md` files; localized instructions take precedence within their scope.
- **Workflow & Tool Guidance**: Consult `.agents/skills/` for lifecycle workflow skills
  (`workflow-git`, `workflow-code-review`, `workflow-changelog`, `workflow-adr`,
  `workflow-setup`, `workflow-skill-creator`, `workflow-docs-authoring`,
  `workflow-docs-consumers`), Spec-Driven Development suite (`sdd`, `sdd-spec`,
  `sdd-plan`, `sdd-implement`, `sdd-review`), engineering guides (`guide-python`,
  `guide-ste100`), and tool-specific guidance (`tool-*/SKILL.md`).

## Architecture & Code Design

Refer to `.agents/skills/guide-python/SKILL.md` for complete guidelines.

- **Python Version**: Python 3.12+.
- **Imports**: Use canonical absolute imports exclusively
  (`from debug_dojo.module import ...`). Relative imports are
  strictly banned via Ruff (`ban-relative-imports = "all"`).
- **Type Annotations**: Use modern PEP 695 type parameter syntax exclusively
  (`type Alias = ...`, `def func[T](...)`). Never use legacy `TypeVar` or
  `Optional`. Import collection abstractions from `collections.abc`.
- **Data Modeling**: Model data with immutable slotted dataclasses
  (`@dataclass(frozen=True, slots=True)`).
- **Subtyping & Contracts**: Use structural subtyping with `typing.Protocol`
  rather than inheritance. Favor composition and callable handlers over class
  hierarchies.
- **Functional Style**: Write pure, composable, idempotent functions with
  explicit inputs and outputs. Avoid in-place mutation.
- **CLI Framework**: Use **Typer** exclusively for any command-line interfaces
  or CLI tools. Never use `argparse`, `click`, or manual `sys.argv` parsing.
  Always declare CLI parameters using PEP 593 `typing.Annotated` and explicit
  `typer.Typer()` applications (consult `.agents/skills/tool-typer/SKILL.md`).
- **Layer Boundaries**: The application follows strict layer boundaries:
  `cli` -> `core` -> external dependencies. The `core` module must never import
  from `cli`.

## Testing & Documentation

- **Testing**: Write unit tests with `pytest`. Use `hypothesis` for property-based
  exploration and `syrupy` for snapshot assertions. `pytest.ini` enforces zero-tolerance
  warning gates (`filterwarnings = error`), import isolation
  (`--import-mode=importlib`), and strict marker validation (`--strict-markers`).
- **Documentation**: Site is built with Zensical. API references are generated
  automatically from docstrings with `mkdocstrings`. Docstrings are rendered as
  Markdown, not reStructuredText: use single backticks for inline code
  (`` `value` ``), never double backticks (```` ``value`` ````). Build-time link
  and reference validation is strictly enforced via `[project.validation]`.
- **Diagrams**: Use Mermaid code blocks (```mermaid) for architecture and sequence
  diagrams.

## Investigating CI Failures

When diagnosing GitHub Actions failures:

1. Enumerate recent runs: `gh run list --limit 5`
2. Inspect failing step logs directly: `gh run view <run-id> --log-failed`
3. Avoid downloading full job logs when annotations and failed step summaries are
   sufficient.
