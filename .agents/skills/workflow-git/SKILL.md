---
description: >
  Manages git branches, conventional commits, and pull requests in this
  project. Enforces AI disclosure checklists, testing plans, and clean commit
  hygiene. Mandatory whenever creating branches, preparing commits, staging files,
  authoring commit messages, or creating pull requests, even without prompt triggers.
  Triggers: commit, branch, pull request, PR, push, conventional commit.
name: workflow-git
version: 1.0.0
---

# Git Workflow & Pull Request Standards (`workflow-git`)

This skill defines branch management, conventional commit
formatting, and pull request standards for this repository.

---

## 1. Branch Conventions

Maintain dedicated feature branches for non-trivial tasks:

- **Main Branch**: `main` remains protected and always deployable.
- **Feature Branches**: Prefix with purpose:
  - `feat/<short-description>`: New features or capabilities.
  - `fix/<short-description>`: Bug fixes or issue resolutions.
  - `refactor/<short-description>`: Internal code refactoring.
  - `docs/<short-description>`: Documentation additions or updates.
  - `chore/<short-description>`: Dependency updates, CI, or tool configuration.

---

## 2. Conventional Commit Standards

Each commit message must follow the Conventional Commits specification:

```text
<type>(<scope>): <short imperative summary>

[optional body explaining problem and solution rationale]

[optional footer, e.g. Closes #123]
```

### Commit Types

- **`feat`**: A new user-facing feature or library capability.
- **`fix`**: A bug fix.
- **`docs`**: Documentation changes only.
- **`refactor`**: Code changes that neither fix bugs nor add features.
- **`test`**: Adding or updating test cases.
- **`chore`**: Maintenance, build system, or dependency updates.

### Rules for Commit Messages

1. **Imperative Mood**: Use imperative present tense in the subject ("add feature",
   not "added feature" or "adds feature").
2. **Lowercase Subject**: Start the summary with a lowercase letter and no trailing period.
3. **State the Reason**: The subject line must state the reason for
   the change, not only the mechanical edit:

   | Write (Why the change exists) | Not (Which lines moved) |
   | :--- | :--- |
   | `fix(sessions): prevent duplicate events on resume` | `fix(sessions): check interrupt_id before appending` |
   | `feat(cli): support JSON output for machine parsing` | `feat(cli): add --json flag to main` |

   *Self-check*: Read the subject back and ask whether it explains *why* someone made
   the change. If it only names the edited symbol, rewrite it.

### AI Co-Authorship & Attribution Trailers

When AI coding assistants help generate code or commit diffs, credit them in the commit
footer using standard Git `Co-authored-by` trailers:

```git
feat(auth): add token refresh endpoint

Implement automatic token rotation on expiry with sliding window validation.

Co-authored-by: Claude <noreply@anthropic.com>
```

---

## 3. Explicit File Staging (No Blanket Staging)

Always stage files explicitly by path (`git add <file1> <file2>`).
**Never** use blanket staging commands (`git add -A`, `git add .`, or `git commit -am`).
The working tree can contain scratch notes, in-progress edits, or environment files.
Blanket staging adds these untracked files into commits without human review.

---

## 4. Pre-Commit Verification Gate

Never commit unverified changes. Run the verification pipeline locally:

```bash
# Verify static analysis, types, and architecture
uv run poe code-quality

# Verify unit tests and coverage
uv run poe test

# Verify all git hooks pass via prek
uv run prek run --all-files
```

> [!IMPORTANT]
> **Always Re-Read Files Modified by Hooks**:
> If formatters or prek hooks change files on disk, re-read those files before you make further edits.
> This step prevents edit collisions from shifted line numbers.

---

## 5. Pull Request Preparation & AI Disclosure

When you open a pull request, follow `PULL_REQUEST_TEMPLATE.md` and `AI_POLICY.md`:

> [!IMPORTANT]
> **Maintainers do not accept unsupervised agent contributions**.
> A human contributor must review, understand, and test every contribution.
> The human contributor must substantively explain and defend all changes.
> See `AI_POLICY.md` for full requirements.

### Pull Request Structure

1. **Problem & Solution**:
   - Provide a concise description of the underlying problem.
   - Summarize the chosen solution and architectural rationale.
2. **Testing Plan**:
   - Report passed `pytest` results and coverage status.
   - Document any manual tests.
3. **AI Assistance Disclosure (Mandatory)**:
   - Identify AI coding assistants used (for example, Antigravity, Claude Code, Cursor).
   - Summarize the scope of assistance (for example, initial draft, refactoring, test
     generation).
   - Check that a human reviewed and approved all submitted changes.
   - Check that commit messages credit AI assistants with `Co-authored-by`
     trailers.

### Shell-Safe Outbound CLI Calls (`gh` & `git`)

Do not pass double-quoted inline strings (`--body "... `code` ..."`) when markdown text contains backticks, `$variables`, or double quotes.
The shell evaluates backticks as command substitutions and damages the text.
Always use `--body-file` (or `-F`) with a file in `.temp/` or a single-quoted heredoc (`<<'EOF'`):

```bash
gh pr create --title "feat(core): add parser" --body-file - <<'EOF'
### Summary
Updated `parse_token` to handle `$HOME` literals safely.
EOF
```

---

## 6. Continuous Integration (CI) Monitoring After Every Push

Never consider a task complete immediately after running `git push`.
Remote CI environments run on multiple platforms and Python versions.
They often catch environment-specific issues that local machines do not show.

### Post-Push Monitoring Protocol

Immediately after pushing commits to a branch or pull request:

1. **Find the triggered workflow run**:

   ```bash
   gh run list --branch <branch-name> --limit 3
   ```

2. **Watch the workflow until completion**:

   ```bash
   gh run watch <run-id>
   ```

3. **Inspect failures immediately**:
   If any job fails, inspect the failed step logs directly:

   ```bash
   gh run view <run-id> --log-failed
   ```

4. **Remediate and repeat**:
   Reproduce the failure locally.
   Apply the fix, run local verification gates, commit, and push again.
   Monitor CI again until all jobs report green.
