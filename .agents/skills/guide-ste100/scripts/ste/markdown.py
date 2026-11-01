"""Extract prose blocks from Markdown.

The scanner is line-based and stdlib-only. It is not a full CommonMark parser.
It understands the constructs that Project documentation and agent skills use:

- YAML frontmatter. Only the `description` value is prose. Skill descriptions
  are agent-facing text, so they get linted.
- Fenced code (backtick or tilde, closed by a fence of the same character and at
  least the same length) and `$$` math blocks. Both are skipped.
- HTML comments (skipped, but scanned for `ste-lint` directives) and HTML block
  lines such as Termynal `<div data-ty>` widgets (skipped).
- ATX headings, thematic breaks, and GFM tables (each cell is its own block).
- Blockquotes, GitHub alerts (`> [!NOTE]`), and Zensical admonitions
  (`!!! note`). The container syntax is stripped and the content is linted.
- Hard-wrapped paragraphs and list items. Wrapped lines are joined into one
  block, so a sentence that rumdl reflowed across three lines is one sentence.

Indented code blocks are not recognized: This project requires fenced code (MD046).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ste.directives import Directive, build_suppressions, parse_directive
from ste.inline import mask_inline
from ste.model import Block, BlockKind, Document, Span

QUOTE_PREFIX = re.compile(r"^ {0,3}> ?")
FENCE_OPEN = re.compile(r"^(?P<fence>`{3,}|~{3,})(?P<info>[^`]*)$")
FENCE_CLOSE = re.compile(r"^(?P<fence>`{3,}|~{3,})[ \t]*$")
ALERT = re.compile(
    r"^\[!(?:NOTE|TIP|IMPORTANT|WARNING|CAUTION)\][ \t]*$", re.IGNORECASE
)
ADMONITION = re.compile(r"^(?:!!!|\?\?\?\+?)[ \t]+\S")
HTML_BLOCK = re.compile(r"^</?[A-Za-z][A-Za-z0-9-]*(?:[\s/>]|$)")
HEADING = re.compile(r"^#{1,6}(?:[ \t]+(?P<body>.*?))?(?:[ \t]+#+)?[ \t]*$")
THEMATIC_BREAK = re.compile(r"^(?:(?:-[ \t]*){3,}|(?:\*[ \t]*){3,}|(?:_[ \t]*){3,})$")
LIST_ITEM = re.compile(
    r"^(?P<indent> *)(?P<marker>[-*+]|(?P<number>\d{1,9})[.)])(?P<gap> +)"
    r"(?:\[[ xX]\] +)?(?P<body>\S.*)$"
)
TABLE_SEPARATOR_CELL = re.compile(r"^:?-+:?$")
LINK_DEFINITION = re.compile(r"^\[(?!\^)[^\]]+\]:[ \t]+\S")
FRONTMATTER_FENCE = re.compile(r"^---[ \t]*$")
FRONTMATTER_END = re.compile(r"^(?:---|\.\.\.)[ \t]*$")
DESCRIPTION_KEY = re.compile(r"^description:[ \t]*(?P<value>.*?)[ \t]*$")
BLOCK_SCALAR = re.compile(r"^[>|][+-]?\d*$")
ADMONITION_INDENT = 4
MIN_TABLE_CELLS = 2
MAX_OPENING_INDENT = 3


@dataclass(frozen=True, slots=True)
class Line:
    """A source line with container syntax (quotes, admonitions) removed."""

    number: int
    text: str
    column: int
    """1-based source column of `text[0]`."""
    quote_depth: int

    @property
    def indent(self) -> int:
        """Count leading spaces."""
        return len(self.text) - len(self.text.lstrip(" "))

    @property
    def stripped(self) -> str:
        """The text without surrounding whitespace."""
        return self.text.strip()

    def fragment(self, start: int = 0) -> tuple[int, int, str]:
        """Extract the fragment starting at `start` without outer spaces.

        Returns
        -------
        tuple[int, int, str]
            Source line, 1-based column, and stripped fragment text.

        """
        rest = self.text[start:]
        lead = len(rest) - len(rest.lstrip())
        return self.number, self.column + start + lead, rest.strip()


@dataclass(slots=True)
class _OpenBlock:
    kind: BlockKind
    fragments: list[tuple[int, int, str]]
    content_indent: int
    quote_depth: int


def _build_block(kind: BlockKind, fragments: list[tuple[int, int, str]]) -> Block:
    """Join raw fragments with single spaces, then mask the joined text.

    Masking after the join lets inline constructs that wrap across lines (a
    link text, a code span) mask correctly.

    Returns
    -------
    Block
        Joined and inline-masked prose block with offset spans.

    """
    spans: list[Span] = []
    offset = 0
    for line, column, text in fragments:
        spans.append(Span(offset, line, column))
        offset += len(text) + 1
    raw = " ".join(text for _, _, text in fragments)
    return Block(kind, mask_inline(raw), tuple(spans))


def split_table_row(text: str) -> list[tuple[str, int]] | None:
    r"""Split a table row into `(cell, start)` pairs. Escaped pipes stay in cells.

    >>> split_table_row("| a | b \\| c |")
    [('a', 2), ('b \\| c', 6)]
    >>> split_table_row("no pipes") is None
    True

    Returns
    -------
    list[tuple[str, int]] | None
        Cell texts with start columns, or `None` when `text` is not a row.

    """
    left = len(text) - len(text.lstrip())
    content = text.strip()
    if "|" not in content:
        return None
    if content.startswith("|"):
        content, left = content[1:], left + 1
    if content.endswith("|") and not content.endswith("\\|"):
        content = content[:-1]
    raw_cells = re.split(r"(?<!\\)\|", content)
    if len(raw_cells) < MIN_TABLE_CELLS:
        return None
    cells: list[tuple[str, int]] = []
    column = left
    for raw_cell in raw_cells:
        lead = len(raw_cell) - len(raw_cell.lstrip())
        cells.append((raw_cell.strip(), column + lead))
        column += len(raw_cell) + 1
    return cells


def _is_separator(cells: list[tuple[str, int]] | None, width: int) -> bool:
    return (
        cells is not None
        and len(cells) == width
        and all(TABLE_SEPARATOR_CELL.match(cell) for cell, _ in cells)
    )


def _frontmatter(lines: list[str]) -> tuple[int, list[Block]]:
    """Return the first body line index and the `description` block, if any.

    Returns
    -------
    tuple[int, list[Block]]
        Body start index and the parsed description block, possibly empty.

    """
    if not lines or not FRONTMATTER_FENCE.match(lines[0]):
        return 0, []
    end = next(
        (i for i in range(1, len(lines)) if FRONTMATTER_END.match(lines[i])), None
    )
    if end is None:
        return 0, []
    for index in range(1, end):
        match = DESCRIPTION_KEY.match(lines[index])
        if match:
            fragments = _description_fragments(lines, index, end, match)
            blocks = (
                [_build_block(BlockKind.FRONTMATTER, fragments)] if fragments else []
            )
            return end + 1, blocks
    return end + 1, []


def _description_fragments(
    lines: list[str], index: int, end: int, match: re.Match[str]
) -> list[tuple[int, int, str]]:
    fragments: list[tuple[int, int, str]] = []
    value = match.group("value")
    if value and not BLOCK_SCALAR.match(value):
        start = match.start("value")
        if value[0] in "\"'" and value[-1] == value[0] and len(value) > 1:
            value, start = value[1:-1], start + 1
        fragments.append((index + 1, start + 1, value))
    for offset, raw in enumerate(lines[index + 1 : end], start=index + 1):
        if raw.strip() and not raw[0].isspace():
            break
        if raw.strip():
            lead = len(raw) - len(raw.lstrip())
            fragments.append((offset + 1, lead + 1, raw.strip()))
    return fragments


@dataclass(slots=True)
class _Scanner:
    """Single-pass state machine over Markdown lines."""

    lines: list[str]
    blocks: list[Block] = field(default_factory=list)
    directives: list[Directive] = field(default_factory=list)
    open: _OpenBlock | None = None
    fence: tuple[str, int] | None = None
    math: bool = False
    comment: list[str] | None = None
    admonitions: list[int] = field(default_factory=list)
    previous_blank: bool = True

    def run(self) -> None:
        index, frontmatter = _frontmatter(self.lines)
        self.blocks.extend(frontmatter)
        while index < len(self.lines):
            index = self._step(index)
        self._flush()

    # -- line normalization -------------------------------------------------

    def _normalize(self, index: int) -> Line:
        """Strip blockquote markers and admonition indentation from a line.

        Returns
        -------
        Line
            Normalized line carrying quote depth and source column.

        """
        text, column, depth = self.lines[index], 1, 0
        while match := QUOTE_PREFIX.match(text):
            text, column, depth = text[match.end() :], column + match.end(), depth + 1
        indent = len(text) - len(text.lstrip(" "))
        if text.strip():
            while self.admonitions and indent < self.admonitions[-1]:
                self.admonitions.pop()
        dedent = min(self.admonitions[-1] if self.admonitions else 0, indent)
        return Line(index + 1, text[dedent:], column + dedent, depth)

    # -- dispatch -------------------------------------------------------------

    def _step(self, index: int) -> int:
        """Consume one line and return the next index.

        Returns
        -------
        int
            Index of the next line to process.

        """
        if self.comment is not None:
            self._continue_comment(self.lines[index], index + 1)
            return index + 1
        line = self._normalize(index)
        if self._in_skipped_region(line):
            return index + 1
        if self.open and line.quote_depth != self.open.quote_depth:
            self._flush()
        if not line.stripped:
            self._flush()
            self.previous_blank = True
            return index + 1
        next_index = self._structural(line, index)
        if next_index is None:
            self._prose(line)
            next_index = index + 1
        self.previous_blank = False
        return next_index

    def _in_skipped_region(self, line: Line) -> bool:
        """Consume the line when inside fenced code and math blocks.

        Returns
        -------
        bool
            True when the line belongs to a skipped region.

        """
        if self.fence:
            close = FENCE_CLOSE.match(line.stripped)
            char, length = self.fence
            if (
                close
                and close.group("fence")[0] == char
                and len(close.group("fence")) >= length
            ):
                self.fence = None
            return True
        if self.math:
            self.math = line.stripped != "$$"
            return True
        return False

    def _structural(self, line: Line, index: int) -> int | None:
        """Handle a non-paragraph line through its matching handler.

        Returns
        -------
        int | None
            Next index when a handler consumed the line, else `None`.

        """
        for handler in (
            self._fence_open,
            self._math_open,
            self._comment_open,
            self._skip_line,
            self._admonition,
            self._heading,
            self._list_item,
        ):
            if handler(line):
                return index + 1
        return self._table(line, index)

    # -- handlers -------------------------------------------------------------

    def _fence_open(self, line: Line) -> bool:
        match = FENCE_OPEN.match(line.stripped)
        if match is None:
            return False
        self._flush()
        self.fence = (match.group("fence")[0], len(match.group("fence")))
        return True

    def _math_open(self, line: Line) -> bool:
        if line.stripped != "$$":
            return False
        self._flush()
        self.math = True
        return True

    def _comment_open(self, line: Line) -> bool:
        if not line.stripped.startswith("<!--"):
            return False
        self._flush()
        self.comment = []
        self._continue_comment(line.stripped[4:], line.number)
        return True

    def _continue_comment(self, text: str, number: int) -> None:
        if self.comment is None:
            return
        body, closed, _ = text.partition("-->")
        self.comment.append(body)
        if closed:
            directive = parse_directive(" ".join(self.comment), number)
            if directive is not None:
                self.directives.append(directive)
            self.comment = None

    def _skip_line(self, line: Line) -> bool:
        """Report whether `line` carries no prose and should be skipped.

        HTML blocks, thematic breaks, link definitions, and alert markers
        carry no lintable prose.

        Returns
        -------
        bool
            True for a skipped line.

        """
        text = line.stripped
        skip = bool(
            (line.indent <= MAX_OPENING_INDENT and THEMATIC_BREAK.match(text))
            or (line.indent <= MAX_OPENING_INDENT and LINK_DEFINITION.match(text))
            or HTML_BLOCK.match(text)
            or (line.quote_depth and ALERT.match(text))
        )
        if skip:
            self._flush()
        return skip

    def _admonition(self, line: Line) -> bool:
        if not ADMONITION.match(line.stripped):
            return False
        self._flush()
        base = self.admonitions[-1] if self.admonitions else 0
        self.admonitions.append(base + line.indent + ADMONITION_INDENT)
        return True

    def _heading(self, line: Line) -> bool:
        match = (
            HEADING.match(line.stripped) if line.indent <= MAX_OPENING_INDENT else None
        )
        if match is None:
            return False
        self._flush()
        if match.group("body"):
            fragment = line.fragment(line.indent + match.start("body"))
            self.blocks.append(_build_block(BlockKind.HEADING, [fragment]))
        return True

    def _list_item(self, line: Line) -> bool:
        match = LIST_ITEM.match(line.text)
        if match is None or self._is_wrapped_number(line, match):
            return False
        self._flush()
        self.open = _OpenBlock(
            kind=BlockKind.LIST_ITEM,
            fragments=[line.fragment(match.start("body"))],
            content_indent=match.start("body"),
            quote_depth=line.quote_depth,
        )
        return True

    def _is_wrapped_number(self, line: Line, match: re.Match[str]) -> bool:
        """Report whether `match` opens a wrapped prose line, not a list item.

        Like CommonMark, only an ordered item numbered 1 interrupts a paragraph.
        Inside a list item, a numbered line at the content indent continues it.

        Returns
        -------
        bool
            True for a reflowed prose line starting with a number.

        """
        number = match.group("number")
        if number in {None, "1"} or self.open is None or self.previous_blank:
            return False
        if self.open.kind is BlockKind.PARAGRAPH:
            return True
        return line.indent >= self.open.content_indent

    def _table(self, line: Line, index: int) -> int | None:
        header = split_table_row(line.text)
        if header is None or index + 1 >= len(self.lines):
            return None
        separator_line = self._normalize(index + 1)
        if not _is_separator(split_table_row(separator_line.text), len(header)):
            return None
        self._flush()
        self._emit_cells(line, header)
        index += 2
        while index < len(self.lines):
            row_line = self._normalize(index)
            row = split_table_row(row_line.text)
            if row is None or len(row) != len(header):
                break
            self._emit_cells(row_line, row)
            index += 1
        return index

    def _emit_cells(self, line: Line, cells: list[tuple[str, int]]) -> None:
        for text, start in cells:
            if text:
                fragment = (line.number, line.column + start, text)
                self.blocks.append(_build_block(BlockKind.TABLE_CELL, [fragment]))

    # -- paragraphs -----------------------------------------------------------

    def _prose(self, line: Line) -> None:
        if self.open and not self.previous_blank:
            self.open.fragments.append(line.fragment())
            return
        self._flush()
        self.open = _OpenBlock(
            kind=BlockKind.PARAGRAPH,
            fragments=[line.fragment()],
            content_indent=line.indent,
            quote_depth=line.quote_depth,
        )

    def _flush(self) -> None:
        if self.open is not None:
            self.blocks.append(_build_block(self.open.kind, self.open.fragments))
            self.open = None


def parse(text: str, filename: str = "<stdin>") -> Document:
    """Extract the prose blocks and suppression directives of a Markdown text.

    Parameters
    ----------
    text : str
        Markdown source to scan.
    filename : str
        Name attached to the returned document.

    Returns
    -------
    Document
        Prose blocks with their spans, plus folded suppressions.

    """
    lines = text.splitlines()
    scanner = _Scanner(lines)
    scanner.run()
    suppressions = build_suppressions(scanner.directives, max(len(lines), 1))
    return Document(filename, tuple(scanner.blocks), suppressions)
