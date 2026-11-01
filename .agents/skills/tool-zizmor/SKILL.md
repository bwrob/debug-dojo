---
description: >-
  Guide for zizmor GitHub Actions security static analyzer.
  Use when auditing CI/CD workflows for security vulnerabilities, secrets leakage, or script injection.
  Triggers: zizmor, security, github actions, workflows, ci security.
name: tool-zizmor
version: 1.0.0
---


# zizmor GitHub Actions Security Static Analyzer (`tool-zizmor`)

`zizmor` is a fast static security analysis tool for GitHub Actions
workflows, written in Rust. It audits CI/CD pipelines for security
vulnerabilities, including script injection, untrusted code execution, cache
poisoning, credential exposure, and dangerous trigger configurations.

This project uses `zizmor` to check that workflow pipelines follow
least-privilege principles and supply-chain security standards.

---

## 1. Core CLI Commands

Use these commands to audit workflow configurations locally or in CI:

```bash
# Audit all workflows in .github/workflows
uv run zizmor --config .zizmor.yml .github/workflows

# Run via poethepoet task
uv run poe zizmor

# Full code quality pipeline (includes zizmor)
uv run poe code-quality
```

---

## 2. Configuration Location

Configure Zizmor through **`.zizmor.yml`** at the project root:

```yaml
rules:
  unpinned-uses:
    disable: true
```

### Important Rules Checked:
- **`dangerous-triggers`**: Flags insecure triggers such as `pull_request_target`.
- **`cache-poisoning`**: Detects enabled caches in release/publish pipelines that could be manipulated.
- **`artipacked`**: Detects missing `persist-credentials: false` in `actions/checkout`.
- **`unpinned-uses`**: Audits whether action references lock to specific versions or immutable commit SHAs.

---

## 3. Suppression Patterns

When a workflow requires a specific trigger or configuration (such as metadata inspection on `pull_request_target`), use inline comment annotations:

```yaml
on:
  pull_request_target: # zizmor: ignore[dangerous-triggers] -- This workflow only reads context.payload metadata, never checks out PR code
```
