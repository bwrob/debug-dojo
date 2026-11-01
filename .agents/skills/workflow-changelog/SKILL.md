---
description: >
  Workflow to maintain, draft, and update Keep-a-Changelog
  compliant changelogs and release notes in this project. Enforces source-checked
  Git commit ranges, Semantic Versioning, PR inspection via gh CLI, and contributor
  attribution. Mandatory whenever editing docs/changelog.md, preparing releases,
  drafting release notes, or logging user-facing changes, even without prompt triggers.
  Triggers: changelog, release notes, release, version bump, semver.
name: workflow-changelog
version: 1.0.0
---

# Changelog & Release Notes Workflow (`workflow-changelog`)

This skill defines standards and procedures to maintain
project changelogs and author source-checked release notes.

This project tracks user-facing changes in `docs/changelog.md` following
[Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/) and
[Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

---

## 1. Core Principles

1. **Keep a Changelog Categories**: Assign each notable change to one category:
   - **`Added`**: New user-facing features or capabilities.
   - **`Changed`**: Changes in existing functionality.
   - **`Deprecated`**: Features scheduled for removal.
   - **`Removed`**: Removed features.
   - **`Fixed`**: Bug fixes.
   - **`Security`**: Vulnerability fixes or security improvements.
2. **Audience-Centric**: Write for users and consumers, not maintainers.
   Explain impact, benefits, and migration steps. Do not describe internal refactors.
3. **Source-Checked**: Never summarize git history from commit titles alone.
   Always check pull request descriptions, code diffs, and deprecation warnings.
4. **Human Review**: Draft changelog entries for human review. Do not
   publish releases or push tags without explicit instructions.

---

## 2. Standard Structure (`docs/changelog.md`)

Structure changelogs according to [templates/changelog.md](./templates/changelog.md).
Key structural elements:
- Top-level `## [Unreleased]` section with categorized subsections (`Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`).
- Dated release sections (`## [X.Y.Z] - YYYY-MM-DD`).
- Migration guides beneath version headings when breaking changes occur.
- Comparison links mapping tags to Git commit ranges at the bottom.

---

## 3. Workflow: Updating `[Unreleased]` During Development

Follow these steps when you add features, fix bugs, or address security issues on a branch:

1. Open `docs/changelog.md`.
2. Find the `## [Unreleased]` section at the top.
3. Under the matching category header (`### Added`, `### Fixed`), append a
   bullet point describing the change.
4. Create the category header under `## [Unreleased]` if it does not exist.
5. Include a link to the relevant issue or PR and author credit:
   ```markdown
   - Support streaming JSON-lines response format ([#128](https://github.com/user/project/pull/128)) by @contributor.
   ```

---

## 4. Workflow: Drafting a New Release

Follow these steps to prepare a new release (`vX.Y.Z`):

### Step 1: Establish the Exact Git Range

Identify the previous release tag (for example, `v0.1.0`) and target branch (`main`):

```bash
# Fetch latest tags and commits
git fetch --quiet origin --tags

# List commits in the release range
git log --format='%H %s' v0.1.0..HEAD

# Inspect summary of changed files
git diff --stat v0.1.0..HEAD
```

### Step 2: Query Pull Requests and Author Handles

Map each commit in the range to its GitHub Pull Request:

```bash
# Query PR metadata using gh CLI
gh pr view <PR_NUMBER> --json number,title,body,author,url
```

For direct commits without a PR number:
```bash
git log --format='%H %an <%ae> %s' v0.1.0..HEAD
```

### Step 3: Check Actual Behavior in Source Code

Do not trust pull request titles alone. Check the code changes directly:
- **Breaking Changes**: Check for changed function signatures, renamed CLI options,
  removed module exports, or raised exception types.
- **Deprecations**: Check for `warnings.warn(..., DeprecationWarning)` or docstring
  deprecation notices.
- **Dependencies**: Check `pyproject.toml` for raised minimum dependency bounds.

### Step 4: Promote `[Unreleased]` to Version Header

In `docs/changelog.md`:
1. Change `## [Unreleased]` to include the new version and current date:
   ```markdown
   ## [Unreleased]

   ## [0.2.0] - 2026-10-17
   ```
2. Sort category headers in standard order: `Added`, `Changed`, `Deprecated`, `Removed`,
   `Fixed`, `Security`.
3. If breaking changes exist, document migration instructions below the version heading:
   ```markdown
   #### Migration Guide
   The `Client.connect()` method now requires an explicit `timeout` keyword argument.
   Replace `Client.connect("localhost")` with `Client.connect("localhost", timeout=10.0)`.
   ```
4. Update comparison links at the bottom:
   ```markdown
   [Unreleased]: https://github.com/org/repo/compare/v0.2.0...HEAD
   [0.2.0]: https://github.com/org/repo/compare/v0.1.0...v0.2.0
   [0.1.0]: https://github.com/org/repo/releases/tag/v0.1.0
   ```

---

## 5. Verification Gate

Before committing changelog updates:
1. Check Markdown formatting with `uv run rumdl check docs/changelog.md`.
2. Build documentation site with `uv run poe docs-build` to check navigation and links.
3. Check the drafted entries for active voice and accurate contributor handles.
