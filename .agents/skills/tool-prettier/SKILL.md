---
description: >-
  Guide for Prettier code formatter for YAML manifests and CSS stylesheets.
  Use when formatting, linting, checking, or configuring YAML and CSS files.
  Triggers: prettier, yaml, css, format-yaml, format-css, .prettierrc.yaml.
name: tool-prettier
version: 1.0.0
---

# Prettier Code Formatter (`tool-prettier`)

`prettier` is a code formatter. In this repository, Prettier
enforces 4-space indentation and 88-character line lengths.
It applies uniform bracket spacing and quote styling to YAML manifests
(`.github/workflows/*.yaml`) and CSS stylesheets
(`docs/stylesheets/*.css`).

---

## 1. Core CLI Commands

Format and check YAML and CSS files with prek or Poe tasks:

```bash
uv run prek run prettier --all-files      # Format all YAML manifests
uv run prek run prettier-css --all-files  # Format all CSS stylesheets
```

This project wires task aliases into Poe:

```bash
uv run poe format-yaml       # Runs prek run prettier --all-files
uv run poe format-css        # Runs prek run prettier-css --all-files
uv run poe fix               # Auto-fixes Python, TOML, Markdown, YAML, CSS, and typos
uv run poe code-quality      # Full quality pipeline including YAML and CSS checks
```

---

## 2. Configuration (`.prettierrc.yaml`)

Configure Prettier in `.prettierrc.yaml` at the project root:

```yaml
printWidth: 88
tabWidth: 4
useTabs: false
semi: true
singleQuote: false
bracketSpacing: true
proseWrap: "preserve"
```

---

## 3. Best Practices & Troubleshooting

- **Run Through Poe**: Use `uv run poe fix` or `uv run poe code-quality` to format YAML and CSS. These tasks do not require global Node.js or npm.
- **Prek Integration**: Prettier runs during `git commit` through the `mirrors-prettier` hook in `prek.toml`.
