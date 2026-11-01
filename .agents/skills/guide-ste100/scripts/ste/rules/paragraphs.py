"""Paragraph length rule enforcing one topic and maximum 6 sentences per paragraph."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ste.model import BlockKind, Finding, Severity

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ste.model import Block, Document

MAX_SENTENCES_PER_PARAGRAPH = 6
MIN_SENTENCE_WORD_COUNT = 2


@dataclass(frozen=True, slots=True)
class ParagraphLengthRule:
    """Rule that flags paragraphs with more than 6 sentences (Rule 6.6)."""

    id: str = "paragraph-length"
    severity: Severity = Severity.HARD
    description: str = "Enforce maximum 6 sentences per paragraph (Rule 6.6)."
    max_sentences: int = 6

    def check(self, document: Document) -> list[Finding]:
        """Report paragraph blocks holding more than six sentences.

        Returns
        -------
        list[Finding]
            One finding per overlong paragraph.

        """
        return [
            finding
            for block in document.blocks
            if block.kind == BlockKind.PARAGRAPH
            for finding in self._check_block(document, block)
        ]

    def _check_block(self, document: Document, block: Block) -> Iterator[Finding]:
        """Yield a finding when `block` exceeds the sentence cap.

        Yields
        ------
        Finding
            Hard finding with the sentence count.

        """
        sentence_count = self._count_sentences(block.text)
        if sentence_count <= self.max_sentences:
            return
        line, col = block.locate(0)
        if document.suppressions.silences(line, self.id):
            return
        yield Finding(
            file=document.filename,
            line=line,
            column=col,
            rule=self.id,
            severity=self.severity,
            match=f"{sentence_count} sentences",
            message=(
                f"Paragraph has {sentence_count} sentences "
                f"(cap {self.max_sentences}, Rule 6.6). "
                "Split into multiple single-topic paragraphs."
            ),
        )

    @staticmethod
    def _count_sentences(text: str) -> int:
        """Count sentences holding at least two words.

        `!` and `?` are normalized to `.` so one split pass suffices.

        Returns
        -------
        int
            Number of qualifying sentences.

        """
        normalized = text.replace("?", ".").replace("!", ".")
        return sum(
            len(words) >= MIN_SENTENCE_WORD_COUNT
            for words in (part.strip().split() for part in normalized.split("."))
        )


PARAGRAPH_LENGTH_RULE = ParagraphLengthRule()
