---
description: >-
  Guide for rumdl Markdown linter and formatter in Rust.
  Use when checking, formatting, and linting Markdown documentation and embedded code blocks.
  Triggers: rumdl, markdown, lint-md, format-md, rumdl.toml.
name: tool-rumdl
version: 1.0.0
---


# rumdl Markdown Linter & Formatter (`tool-rumdl`)

`rumdl` is a fast markdown linter and formatter written in Rust. It enforces
consistent markdown style across documentation and guides. It also formats
and lints embedded Python code snippets using Ruff.

This project configures `rumdl` to enforce GitHub Flavored Markdown (GFM)
rules with an 88-character line limit for prose and code blocks.

---

## 1. Core CLI Commands

Lint and format project documentation with these commands.

```bash
uv run rumdl check                     # Lint all markdown files in repository
uv run rumdl check path/to/doc.md      # Lint a single markdown file
uv run rumdl fmt                       # Format all markdown files and code
uv run rumdl fmt path/to/doc.md        # Format a specific markdown file
```

This project wires task aliases into Poe:

```bash
uv run poe lint-md                     # Runs rumdl check
uv run poe format-md                   # Runs rumdl fmt
```

---

## 2. Configuration Location

Configure `rumdl` through **`rumdl.toml`** at the project root:

```toml
flavor = "gfm"
line-length = 88
respect-gitignore = true

# Excluded paths
exclude = [
    ".git",
    ".github",
    ".venv",
    ".ruff_cache",
    ".rumdl_cache",
    "site",
    "dist",
]

# Rule toggles
enable = ["ALL"]
disable = ["MD060", "MD063", "MD078", "MD090", "MD093"]
extend-enable = ["MD080", "MD083"]

# Code block formatting tools
[code-block-tools]
enabled = true
on-error = "warn"
on-missing-tool-binary = "warn"

[code-block-tools.language-aliases]
"bash"     = "shell"
"py"       = "python"
"python3"  = "python"

[code-block-tools.languages.python]
format = ["ruff:format"]
lint   = ["ruff:check"]

[code-block-tools.tools."ruff:format"]
command = ["ruff", "format", "-"]
```

---

## 3. Common Configuration Changes During Development

Adjust allowed HTML tags, line lengths, and rule exclusions with these
settings.

### A. Allowing Additional HTML Elements (MD033)

If you embed custom HTML tags (for example, `<details>`, `<summary>`, `<video>`):

```toml
[MD033]
allowed-elements = [
    "a", "br", "details", "div", "img", "kbd", "p",
    "span", "summary", "table", "tbody", "td", "th", "tr"
]
```

### B. Adjusting Line Length Restrictions (MD013)

This project enforces an 88-character limit for narrative text and code blocks. To
adjust or exempt specific constructs:

```toml
[MD013]
line-length = 88
code-block-line-length = 88
headings = false       # Don't fail long section titles
tables = false         # Don't wrap wide markdown tables
math-blocks = false    # Don't break long LaTeX formulas
reflow = true
```

### C. Disabling or Suppressing a Specific Rule

If a rule conflicts with documentation design:

```toml
disable = [
    "MD013", # Disable line length checking
    "MD033", # Allow inline HTML
]
```

### D. Adding Language Aliases for Code Block Checkers

When using template expressions or custom syntax tags inside fences:

```toml
[code-block-tools.language-aliases]
"{python}" = "python"
"py3"      = "python"
"zsh"      = "shell"
```

---

## 4. Important Markdown Rules

Follow these markdown conventions:

1. **Put blank lines before lists (MD032)**.
2. **Do not put trailing punctuation on headings (MD026)**.
3. **Put blank lines before and after code fences (MD031)**.
4. **Always specify fence languages (MD040)**: Use ```` ```python ````,
   ```` ```bash ````, ```` ```mermaid ````, never bare ```` ``` ````.
