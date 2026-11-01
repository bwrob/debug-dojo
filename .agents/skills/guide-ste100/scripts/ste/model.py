"""Core data model shared by the Markdown extractor, the rules, and the reporters.

A `Document` is a sequence of prose `Block`s extracted from Markdown. Each block
holds its text as one logical string: hard-wrapped lines are joined with a single
space, so sentence-level rules see whole sentences. `Span`s map every offset in
that joined string back to a source line and column.
"""

from __future__ import annotations

from bisect import bisect_right
from dataclasses import dataclass, field
from enum import StrEnum


class Severity(StrEnum):
    """How a finding affects the exit status."""

    HARD = "hard"
    """Counts against `--baseline` and can fail the run."""

    ADVISORY = "advisory"
    """Reported, but never fails the run."""


class BlockKind(StrEnum):
    """The Markdown construct that produced a prose block."""

    PARAGRAPH = "paragraph"
    HEADING = "heading"
    LIST_ITEM = "list-item"
    TABLE_CELL = "table-cell"
    FRONTMATTER = "frontmatter"


@dataclass(frozen=True, slots=True)
class Span:
    """One source fragment inside a block's joined text."""

    offset: int
    """Start offset of the fragment inside `Block.text`."""

    line: int
    """1-based source line of the fragment."""

    column: int
    """1-based source column of the fragment's first character."""


@dataclass(frozen=True, slots=True)
class Block:
    """A unit of prose: one paragraph, heading, list item, or table cell."""

    kind: BlockKind
    text: str
    spans: tuple[Span, ...]

    def locate(self, offset: int) -> tuple[int, int]:
        """Map an offset in `text` to a 1-based `(line, column)` source position.

        >>> block = Block(BlockKind.PARAGRAPH, "ab cd", (Span(0, 1, 1), Span(3, 2, 3)))
        >>> block.locate(4)
        (2, 4)

        Returns
        -------
        tuple[int, int]
            1-based source position for `offset`.

        """
        index = max(bisect_right([span.offset for span in self.spans], offset) - 1, 0)
        span = self.spans[index]
        return span.line, span.column + offset - span.offset


@dataclass(frozen=True, slots=True)
class Suppressions:
    """Line ranges where inline `ste-lint` directives silence rules."""

    ranges: tuple[tuple[int, int, frozenset[str]], ...] = ()
    """`(first_line, last_line, rules)`. An empty rule set silences every rule."""

    def silences(self, line: int, rule: str) -> bool:
        """Report whether a directive silences `rule` on `line`.

        Returns
        -------
        bool
            True when any range covers `line` and `rule`.

        """
        return any(
            first <= line <= last and (not rules or rule in rules)
            for first, last, rules in self.ranges
        )


@dataclass(frozen=True, slots=True)
class Document:
    """Prose extracted from one Markdown source."""

    filename: str
    blocks: tuple[Block, ...]
    suppressions: Suppressions = field(default_factory=Suppressions)


@dataclass(frozen=True, slots=True, kw_only=True)
class Finding:
    """One rule violation at a source position."""

    file: str
    line: int
    column: int
    rule: str
    severity: Severity
    match: str
    message: str

    @property
    def sort_key(self) -> tuple[str, int, int, str]:
        """Order findings by file, then position, then rule.

        Returns
        -------
        tuple[str, int, int, str]
            Comparable sort key.

        """
        return self.file, self.line, self.column, self.rule

    def to_dict(self) -> dict[str, str | int]:
        """Return a JSON-serializable mapping.

        Returns
        -------
        dict[str, str | int]
            Mapping of all Finding fields.

        """
        return {
            "file": self.file,
            "line": self.line,
            "column": self.column,
            "rule": self.rule,
            "severity": self.severity.value,
            "match": self.match,
            "message": self.message,
        }
