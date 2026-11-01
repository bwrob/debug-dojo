---
description: >-
  Guide for Termynal animated terminal widgets in documentation.
  Covers the HTML data-ty API, Markdown .termy console wrapping, animation delays,
  interactive controls, and styling. Use when creating, debugging, or styling
  terminal animation widgets in Zensical docs.
  Triggers: termynal, termy, terminal animation, cli animation, animated terminal, docs animation.
name: tool-termynal
version: 1.0.0
---

# Termynal Animated Terminal (`tool-termynal`)

This skill documents **Termynal**, an animated terminal widget designed by Ines
Montani. Sebastián Ramírez extended Termynal for Markdown
documentation.

Termynal uses native browser `async`/`await` for typing animations without external
dependencies or layout reflows. Non-JavaScript visitors still see the complete
terminal output as clean static text.

---

## 1. Quick Reference & Core Syntax

Zensical loads Termynal styles and scripts through `docs/stylesheets/termynal.css` and
`docs/javascripts/termynal.js`.

### Markdown Integration (`.termy`)

Wrap standard Markdown `console` code blocks inside `<div class="termy">`:

````markdown
<div class="termy">

```console
$ uv run my-cli greet "World"

✨ Hello, World!

// Inspect CLI options and help
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

</div>
````

### Line Syntax Mapping

When you wrap lines in `<div class="termy">`, Termynal parses each line:

| Markdown Syntax | Parsed Type | Behavior in Animation |
| :--- | :--- | :--- |
| `$ <command>` | `input` | Types characters one by one with animated cursor and `$ ` prompt. |
| `# <command>` | `input` | Types command with custom prompt `# ` or `>`. |
| `<prompt> $ <cmd>` | `input` | Types command with custom prompt `<prompt>`. |
| `---> 100%` | `progress` | Animates a loading progress bar from 0% to 100% (`████████ 100%`). |
| `// <comment>` | `comment` | Instant line prepended with `💬 ` and styled with `--termynal-comment`. |
| `<b>text</b>` | `output` | Output line preserving bold styling without typing delay. |
| `plain text` | `output` | Plain output displayed after line delay (`data-ty-lineDelay`). |

---

## 2. HTML API (`data-ty` Attributes)

For full control or custom HTML layouts outside Markdown code blocks, use the
native HTML API:

```html
<div id="termynal" data-termynal data-ty-startDelay="600" data-ty-typeDelay="60" data-ty-lineDelay="500">
    <span data-ty="input">uv add spacy</span>
    <span data-ty="progress"></span>
    <span data-ty>Successfully installed spacy</span>
    <span data-ty="input" data-ty-prompt="guest@dev:~$">whoami</span>
    <span data-ty data-ty-delay="1000">developer</span>
</div>
```

### Container Attributes

Configure terminal-wide timing and appearance on the root `<div data-termynal>`:

| Attribute | Default | Description |
| :--- | :--- | :--- |
| `data-ty-startDelay` | `600` | Delay in milliseconds before typing starts. |
| `data-ty-typeDelay` | `80` (or `60`) | Delay in milliseconds between individual typed characters. |
| `data-ty-lineDelay` | `1200` (or `500`) | Delay in milliseconds before revealing the next line. |
| `data-ty-progressLength` | `40` | Total character width of the progress bar. |
| `data-ty-progressChar` | `█` | Character used to draw progress blocks. |
| `data-ty-progressPercent` | `100` | Percentage target where progress stops. |
| `data-ty-cursor` | `▋` | Cursor character displayed during typing. |

### Line Attributes

Override behavior on individual child `<span>` elements:

| Attribute | Example | Description |
| :--- | :--- | :--- |
| `data-ty="input"` | `data-ty="input"` | Defines an animated typed command line. |
| `data-ty="progress"` | `data-ty="progress"` | Defines an animated progress bar. |
| `data-ty` | `data-ty` | Defines instant output line. |
| `data-ty-delay` | `data-ty-delay="250"` | Override line delay for this specific element (ms). |
| `data-ty-typeDelay` | `data-ty-typeDelay="40"`| Override typing speed for this specific input line (ms). |
| `data-ty-prompt` | `data-ty-prompt="➜ "` | Custom prompt string preceding the command. |

---

## 3. JavaScript API

You can also instantiate Termynal programmatically:

```javascript
import { Termynal } from './termynal.js';

const termynal = new Termynal('#termynal', {
    startDelay: 500,
    typeDelay: 50,
    lineDelay: 400,
    lineData: [
        { type: 'input', value: 'uv run poe test' },
        { value: '15 passed in 0.42s' },
        { type: 'input', value: 'uv run poe docs-build' },
        { value: 'Build finished in 0.50s' }
    ]
});
```

### Controls

Termynal includes interactive control buttons in the top right:
- **`fast →`**: Instantly sets delays to `0`, finishing the animation immediately.
- **`restart ↻`**: Clears the container and replays the animation from the start.

---

## 4. Styling & Custom Properties (`termynal.css`)

CSS variables in `docs/stylesheets/termynal.css` control terminal appearance:

```css
:root {
  --termynal-bg: #1e222b;          /* Terminal window background */
  --termynal-text: #eaeaea;        /* Primary command & output text */
  --termynal-subtle: #7d8590;      /* Header title and inactive controls */
  --termynal-accent: #2dd4bf;      /* Prompt ($) and active button accents */
  --termynal-comment: #5eead4;     /* Comment text (// ...) */
}
```

The top window bar renders macOS-style window controls (red `#ff5f56`, yellow
`#ffbd2e`, green `#27c93f`) via CSS `:before` pseudo-elements.

---

## 5. Guidelines and Best Practices

1. **Always Use Static `console` Inside `<div class="termy">`**:
   Never use dynamic Python execution (` ```python exec="on" `) inside a `<div class="termy">`.
   Dynamic subshell calls execute at documentation build time, emitting raw ANSI escape
   codes (`\x1b[1m`), stripping rich HTML bold tags, and breaking termynal line parsing.
2. **Constrain Column Width**:
   Keep terminal outputs concise (under 60–70 columns). Wide lines force unwanted horizontal
   scrolling or awkward line breaks on smaller screens.
3. **Preserve Rich Tags**:
   Use `<b>Usage: </b>` for command banners. Termynal parses HTML tags in output lines
   and renders them with proper browser font weight.
4. **Instant Navigation Support**:
   In Zensical with `instant` navigation, Termynal hooks into `document$.subscribe()`
   to initialize newly mounted `.termy` blocks without full page reloads.
