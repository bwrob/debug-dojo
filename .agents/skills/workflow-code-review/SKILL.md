---
description: >
  Performs a pre-flight code review against project engineering,
  architecture, and AI policy standards before submitting changes or opening a PR.
  Mandatory before opening a pull request or reporting an autonomous task as complete,
  even without prompt triggers.
  Use when asked to review code, conduct pre-PR audits, check compliance with
  AI_POLICY.md, check architectural boundaries, or check typing precision.
name: workflow-code-review
version: 1.1.0
---

# Pre-Flight Code Review (`workflow-code-review`)

This skill defines the code review protocol for Python repositories.
It establishes the quality gates that all code changes must satisfy before merge.

---

## 1. Read-Only & Grounded Review Contract

1. **Strict Read-Only Contract**: When asked to review a working tree or pull request
   diff, **report findings and stop**. Never edit any file during a review turn. Do
   not mix unrequested fixes with review output. Apply fixes only after the user
   explicitly asks you to fix specific items.
2. **Bias Ordering (Diff Before Context)**:
   Inspect `git status` and `git diff` **before** reading surrounding files or PR
   descriptions. This anchors your review to the actual code change rather than the
   author's stated intent.
3. **Risk-Tiered Review Depth**:
   Allocate review scrutiny proportionally to the risk surface of the diff:
   - **Low risk** (docs, comments, isolated test additions): Check for accuracy and
     hollow assertions.
   - **Medium risk** (standard module logic, internal refactors): Complete full 6-Point Matrix
     check.
   - **High risk** (public API signatures, concurrency/async state, serialization,
     security/subprocess boundaries, dependency changes): Trace failure modes,
     edge-case inputs, and backward compatibility.
4. **Ground Every Finding & Suppress False Positives**:
   Before reporting a finding, resolve symbols through base classes and protocols.
   - For a **correctness finding**, name the concrete input or state that triggers the
     failure.
   - For an **architectural, typing, or style finding**, quote the exact rule or
     convention it violates.
   - **Causal Root-Cause Attribution**:
     Never dismiss a failing test or lint gate as unrelated without proof.
     Check that it fails identically on the base commit and name the cause.
   - **False-Positive Suppression Filter**:
     Omit speculative nitpicks and hypothetical race conditions without a concrete trigger path.
     Skip issues enforced by automated CI gates unless currently failing.
     Omit stylistic preferences not codified in `guide-python`.
     If you cannot ground a finding in a failing input or an explicit rule, leave it out.

---

## 2. The 6-Point Review Matrix

Review changes across six dimensions:

### 1. AI Governance & Accountability (`AI_POLICY.md`)

- [ ] **Human Understanding**: Does the change reflect clear intent and complete
  comprehension rather than unvetted model generation?
- [ ] **No Diff-Narrative Comments**: Are all comments relevant to the *current*
  state of the code? Remove any AI-generated comments that narrate what changed
  relative to the previous version or describe what the agent did or did not do.
- [ ] **Disclosure Ready**: Are the scope of AI assistance and tools used clearly
  identified for inclusion in the pull request description?

### 2. Architectural Boundaries & Public API Stability (`tach.toml` & `griffe`)

- [ ] **Layer Hierarchy**: Does code respect the unidirectional dependency graph:
  `cli` ➔ `core` ➔ external dependencies?
- [ ] **No Inversion**: Does `core` remain strictly isolated from `cli` and user
  interface logic?
- [ ] **Public API Compatibility**: Does the change pass `uv run poe check-api`
  (`griffe check`) without introducing unannounced breaking changes to public
  signatures?

### 3. Type Precision & Python 3.12+ Standards (`guide-python`)

- [ ] **PEP 695 Generics**: Does code use modern `def func[T]()` and `type Alias = ...`
  syntax instead of legacy `TypeVar` or `TypeAlias`?
- [ ] **Standard Collections**: Are collection protocols imported from
  `collections.abc` (`Sequence`, `Mapping`, `Iterable`), never from `typing`?
- [ ] **Immutable Data Models**: Are data entities modeled as frozen, slotted
  dataclasses (`@dataclass(frozen=True, slots=True)`)?
- [ ] **Pyrefly Strict**: Does static type checking pass without bare suppressions
  (only rule-scoped `# pyrefly: ignore[code]` when unavoidable)?
- [ ] **No-ruff-ignores Contract**: Does the diff contain zero `# noqa`
  comments across source files, scripts, and tests?
  Does every `# ruff: ignore[...]` directive use the full lowercase rule name
  with a rationale comment?

### 4. Cognitive Complexity (`complexipy.toml`)

- [ ] **Cognitive Score**: Does every function maintain a cognitive complexity score
  of 10 or less?
- [ ] **Composability**: Are complex conditional branches, nested loops, or deep
  matching clauses decomposed into small, pure helper functions?

### 5. Testing & Quality Assurance (`pytest.ini` & `tool-pytest`)

- [ ] **One Test File Per Unit**: Are new tests placed in the canonical
  `tests/test_<module>.py` file rather than a change-named grab-bag file?
- [ ] **Transformation Assertions**: Do assertions check computed outputs rather than
  echoing input arguments? Do bug fixes include provenance docstrings
  (`Bug / Root cause / Fix`)?
- [ ] **Coverage Threshold**: Does test coverage satisfy project thresholds (100%
  statement and branch coverage)?

### 6. Packaging & Hermetic Dependencies (`pyproject.toml`)

- [ ] **Declared Dependencies**: Are all third-party imports declared in
  `[project.dependencies]` or appropriate dependency groups?
- [ ] **Wheel Import Verification**: Does the package build and pass pre-flight
  wheel import verification via `uv run poe verify-wheel`?

---

## 3. Review Execution Workflow

Follow these steps to conduct a pre-flight review:

```bash
# 1. Inspect working tree status and diff
git status
git diff

# 2. Run all static quality gates (linting, types, complexity, architecture)
uv run poe code-quality

# 3. Run automated test suite with coverage
uv run poe test

# 4. Verify wheel packaging in isolated virtual environment
uv run poe verify-wheel

# 5. Verify all git hooks pass via prek
uv run prek run --all-files
```

---

## 4. Output Review Template

Format code review feedback using the standard structure defined in
[templates/review_output.md](./templates/review_output.md).

Always include:
- Executive verdict (`APPROVE` or `CHANGES REQUESTED`).
- Verification gate outcomes (`poe code-quality`, `poe test`, `poe verify-wheel`).
- Prioritized findings with concrete `file:line` locations and failing inputs or violated rules.
