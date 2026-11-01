---
description: >-
  Guide for Typst layout engine for SVG logos and docs.
  Use when authoring vector assets, logotypes, diagram layouts, and rendered SVG assets.
  Triggers: typst, vector, svg, logo, typesetting.
name: tool-typst
version: 1.0.0
---


# Typst Layout Engine (`tool-typst`)

`typst` is a fast typesetting and document layout engine
written in Rust. It combines the expressive power of LaTeX with the ergonomics
and instant re-compilation of modern design systems.

This project uses `typst` as a vector graphics engine to compile
SVG logotypes and branding assets directly from code.

---

## 1. Core CLI Commands

Compile Typst files into vector SVGs, raster images, or documents.

```bash
uv run typst compile input.typ output.svg # Compile Typst to vector SVG
uv run typst compile input.typ output.png # Compile Typst to raster PNG
uv run typst compile input.typ output.pdf # Compile Typst to PDF
uv run typst watch input.typ output.svg   # Live recompile on file change
uv run typst fonts                        # List all available fonts
```

This project automates the asset build task via Poe:

```bash
uv run poe docs-logo                      # Compiles python-logo.typ -> .svg
```

---

## 2. Syntax Fundamentals

Typst uses three distinct syntactic modes:

1. **Markup Mode** (default): Plain text, headings (`= Title`), bold
   (`*text*`), and italics (`_text_`).
2. **Code Mode** (prefixed with `#`): Function calls, variable assignments,
   and layout blocks.
3. **Content Blocks** (enclosed in `[...]`): Pass formatted markup into
   functions.

### Creating Tight-Bounding Vector SVGs

For standalone logos and icons, remove default page margins and enable
automatic sizing:

```typst
#set page(
  width: auto,
  height: auto,
  margin: 0pt,
  fill: none,
)

#box(baseline: 0pt)[
  #text(
    font: ("Inter", "SF Pro Display", "Roboto", "DejaVu Sans"),
    size: 40pt,
    weight: "bold",
    fill: rgb("#387eb8"),
  )[My]#text(
    font: ("Inter", "SF Pro Display", "Roboto", "DejaVu Sans"),
    size: 40pt,
    weight: "bold",
    fill: rgb("#ffc331"),
  )[Project]
]
```

---

## 3. Common Configuration Changes During Development

Customize fonts, tracking, layouts, and shapes with these common patterns.

### A. Adjusting Fonts and Fallbacks

Always provide generic cross-platform font fallbacks so assets compile
consistently on macOS, Linux, and Windows:

```typst
#set text(
  font: ("Inter", "SF Pro Text", "Segoe UI", "Roboto", "sans-serif"),
  size: 28pt,
)
```

### B. Adjusting Letter Spacing (Tracking)

For logotypes, tighter or wider letter spacing enhances brand polish:

```typst
#text(
  tracking: 1.5pt,   // Positive tracking: expanded spacing
  weight: 800,
)[ENTERPRISE]
```

### C. Creating Multi-Element Grids or Badges

To compose shapes, icons, and text together:

```typst
#grid(
  columns: (auto, auto),
  gutter: 12pt,
  align: horizon,
  circle(radius: 14pt, fill: rgb("#387eb8")),
  text(size: 20pt, weight: "medium")[Example App],
)
```

---

## 4. Guidelines and Troubleshooting

Follow these guidelines when you create assets with Typst:

- **Transparent Backgrounds**: Always set `fill: none` on `#set page` so
  exported SVGs display cleanly in both light and dark mode docs.
- **Font Availability**: If a font is absent in CI environments, Typst
  falls back to the next font in your fallback list. Use standard system
  fonts (`DejaVu Sans`) as final fallbacks.
- **Typos Exclusion**: Exclude generated `.svg` files in
  `typos.toml` because SVG glyph hashes can trigger false-positive spelling
  errors.
