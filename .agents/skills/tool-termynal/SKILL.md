---
description: >-
  Guide for Termynal animated terminal widgets in documentation.
  Covers the Markdown <!-- termynal --> extension, prompt triggers,
  timing delays, interactive controls, and styling.
  Use when creating or debugging terminal animations in Zensical.
  Triggers: termynal, termy, terminal animation, cli animation, animated terminal, docs animation.
name: tool-termynal
version: 1.0.0
---

# Termynal Animated Terminal (`tool-termynal`)

This skill documents **Termynal**, an animated terminal widget designed by Ines
Montani and extended for Markdown by Sebastián Ramírez.

Termynal uses native browser `async`/`await` for typing animations without external
libraries. Non-JavaScript visitors see the complete output as static text.

---

## 1. Quick Reference & Core Syntax

Zensical loads Termynal through the `termynal` Python extension.
Configure the extension in `zensical.toml` under `[project.markdown_extensions]`:

```toml
termynal.include_assets = true
termynal.prompt_literal_start = ["$", ">>>", "ipdb>"]
```

When `include_assets = true`, the extension automatically inlines the required CSS and JavaScript.

### Markdown Integration (`<!-- termynal -->`)

Add the HTML comment `<!-- termynal -->` directly above any fenced `console` or `bash` code block.
Do not wrap code blocks in `<div class="termy">` tags.

````markdown
<!-- termynal -->
```console
$ uv run my-cli greet "World"

✨ Hello, World!

# Inspect CLI options and help
$ uv run my-cli --help

<b>Usage: </b><b>my-cli [OPTIONS] COMMAND [ARGS]...</b>

╭─ Options ─────────────────────────────────────────╮
│ --version  -v        Show version and exit.       │
│ --help               Show this message and exit.  │
╰───────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────╮
│ greet                Display a personalized       │
│                      greeting.                    │
╰───────────────────────────────────────────────────╯
```
````

### Line Syntax Mapping

When a code block has `<!-- termynal -->`, Termynal parses each line:

| Markdown Syntax | Parsed Type | Behavior in Animation |
| :--- | :--- | :--- |
| `$ <command>` | `input` | Types characters one by one with animated cursor and `$ ` prompt. |
| `>>> <command>` | `input` | Types Python REPL commands with `>>> ` prompt. |
| `ipdb> <command>` | `input` | Types debugger commands with `ipdb> ` prompt. |
| `# <comment>` | `comment` | Instant comment line styled with `.termynal-comment`. |
| `---> 100%` | `progress` | Animates a loading progress bar from 0% to 100%. |
| `<b>text</b>` | `output` | Output line that preserves bold styling without typing delay. |
| `plain text` | `output` | Plain output line displayed after the line delay. |

> [!NOTE]
> Termynal matches prompts configured in `zensical.toml` via `termynal.prompt_literal_start`.
> If a line starts with one of these configured prompts followed by a space, Termynal treats it as an animated command input.
> If a line ends with `\`, Termynal treats the next line as a continuation of that command.

---

## 2. HTML API (`data-ty` Attributes)

Termynal converts Markdown blocks into HTML elements with `data-ty` attributes:

```html
<div class="termy" data-termynal data-ty-macos data-ty-title="bash">
    <span data-ty="input" data-ty-prompt="$">uv run app.py</span>
    <span data-ty="progress"></span>
    <span data-ty>Process finished successfully</span>
    <span class="termynal-comment" data-ty># Debugger prompt</span>
    <span data-ty="input" data-ty-prompt="ipdb>">n</span>
    <span data-ty>--Return--</span>
</div>
```

### Container Attributes

Configure container options on the root element or via `<!-- termynal:config -->`:

| Attribute | Default | Description |
| :--- | :--- | :--- |
| `data-ty-startDelay` | `600` | Delay in milliseconds before typing starts. |
| `data-ty-typeDelay` | `80` (or `60`) | Delay in milliseconds between typed characters. |
| `data-ty-lineDelay` | `1200` (or `500`) | Delay in milliseconds before revealing the next line. |
| `data-ty-progressLength` | `40` | Total character width of the progress bar. |
| `data-ty-progressChar` | `█` | Character used to draw progress blocks. |
| `data-ty-progressPercent` | `100` | Percentage target where progress stops. |
| `data-ty-cursor` | `▋` | Cursor character displayed during typing. |

### Line Attributes

Each line element accepts individual attributes:

| Attribute | Example | Description |
| :--- | :--- | :--- |
| `data-ty="input"` | `data-ty="input"` | Defines an animated typed command line. |
| `data-ty="progress"` | `data-ty="progress"` | Defines an animated progress bar. |
| `data-ty` | `data-ty` | Defines an instant output line. |
| `data-ty-delay` | `data-ty-delay="250"` | Sets line delay for this specific element in milliseconds. |
| `data-ty-typeDelay` | `data-ty-typeDelay="40"`| Sets typing speed for this input line in milliseconds. |
| `data-ty-prompt` | `data-ty-prompt="ipdb>"` | Custom prompt string preceding the command. |

---

## 3. Interactive Controls

Termynal provides interactive control buttons in the top right:
- **`fast →`**: Instantly sets delays to `0`, finishing the animation immediately.
- **`restart ↻`**: Clears the container and replays the animation from the start.

---

## 4. Styling & Custom Properties

Termynal includes embedded styling for dark terminal themes:

```css
:root {
  --color-bg: #252a33;
  --color-text: #eee;
  --color-text-subtle: #a2a2a2;
}
```

- Window controls render macOS-style buttons (red, yellow, green) via `:before` pseudo-elements.
- Comment lines render with class `.termynal-comment` using italic styling and teal accent color.
- Custom styles in `docs/stylesheets/custom.css` can override these root properties.

---

## 5. Guidelines and Best Practices

1. **Always Use Static Code Blocks**:
   Never use dynamic execution plugins inside a termynal block.
   Dynamic subshell calls run at documentation build time and emit raw ANSI escape codes.
2. **Constrain Column Width**:
   Keep terminal outputs concise (under 60–70 columns).
   Wide lines force horizontal scrolling or awkward line breaks on smaller screens.
3. **Use `# ` for Comments**:
   Format terminal comments with `# <comment>`.
   Do not use `// <comment>` because Termynal ignores non-hash prefixes for comments.
4. **Configure Custom Prompts**:
   Add interactive prompts to `termynal.prompt_literal_start` in `zensical.toml`.
   Include prompts like `ipdb>` or `>>>` so Termynal animates debugger or REPL input.
5. **Omit Manual Wrapper Divs**:
   Precede the fenced block directly with `<!-- termynal -->`.
   Do not wrap the block in `<div class="termy">` tags.
