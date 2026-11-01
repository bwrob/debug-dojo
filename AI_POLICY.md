# AI Usage & Contribution Policy

The **Debug Dojo** project welcomes the responsible use of AI
coding assistants (such as Claude Code, Antigravity, Cursor, GitHub Copilot, and LLMs)
to augment human development. To preserve codebase quality, architectural clarity, and
maintainer time, all contributors must adhere to the following principles:

## 1. Human-in-the-Loop & Full Accountability

- **Human Ownership**: All AI-assisted code, documentation, and issues must be
  thoroughly understood, reviewed, and edited by a human contributor before submission.
- **You Are Responsible**: By submitting a pull request, you accept full personal
  accountability for the submitted changes, including bug fixes, type safety, test
  coverage, and long-term maintainability.

## 2. Verification Gate Before Submitting

- **Mandatory Local Testing**: Never submit AI-generated code without running the full
  test and verification suite locally:

  ```bash
  uv run poe test
  uv run poe code-quality
  uv run prek run --all-files
  ```

- **No Speculative Solutions**: Do not submit code for environments, platforms, or
  hardware you cannot test locally. Relying on remote CI pipelines to discover if
  AI-generated code works is prohibited.

## 3. No Unattended Bots or PR Floods

- **Automated Agents Restricted**: Autonomous, unattended agent scripts are strictly
  forbidden from directly opening pull requests, submitting issues, or posting bot
  comments on this repository.
- **Targeted Contributions**: Pull requests created with AI assistance should address
  existing, accepted issues or open discussions. Drive-by PRs addressing non-issues may
  be closed without review.
- **Search Before Opening (No Duplicates)**: Before opening a pull request, search open
  and closed pull requests, issues, and discussions. Do not open a pull request when the
  same change has already been proposed or is currently in progress. Submitting
  duplicate pull requests wastes maintainer bandwidth.
- **Contribute at Human Speed, Not AI Speed**: AI tools make it trivial to generate
  large volumes of code and prose quickly, but open source review bandwidth moves at
  human speed. Do not post rapid-fire pull requests, mass-claim open issues, or flood
  issue trackers with automated solutions.
- **Do Not Communicate via LLM-Generated Text**: Do not rely on AI assistants to speak
  for you in issues, pull request discussions, or reviews. Maintainers expect direct,
  thoughtful communication written by the contributor, not raw LLM summaries.

## 4. Transparent Disclosure

- **PR Disclosure**: Contributors using AI coding tools must state the tools used (e.g.
  Claude Code, Antigravity, Cursor) and the general scope of assistance in the pull
  request description (see `.github/PULL_REQUEST_TEMPLATE.md`).
- **Commit Attribution**: When AI coding assistants contribute directly to code
  generation or commits, credit them in Git commit messages using standard
  `Co-authored-by` trailers (e.g. `Co-authored-by: Claude <noreply@anthropic.com>`).
- **Protecting Newcomer Issues**: Issues tagged with `good first issue` are reserved for
  human contributors learning the codebase. Using AI to generate automated solutions for
  these issues defeats their educational purpose and is discouraged.

## 5. Concise Code, Clear Comments, No Slop

- **Default to Zero Inline Comments Unless Explaining 'Why'**: Comments should default
  to none. Only add inline comments when explaining a non-obvious rationale, hidden
  constraint, workaround, or subtle architectural invariant.
- **Remove Obsolete, Verbose, & Diff-Narrative Commentary**: Any comments added must be
  concise and relevant for the *current* state of the code. Remove any AI-generated
  comments that describe changes relative to the previous state of the code, narrate
  what the agent did or did not do, or restate obvious language semantics before opening
  a PR.
- **Maintain Architectural Invariants**: Ensure AI-generated code respects project
  conventions (PEP 695 generics, slotted dataclasses, pure functions, absolute imports,
  and layer boundaries defined in `AGENTS.md`).
