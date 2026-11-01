"""Sentence length rule."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ste.model import Finding, Severity

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ste.model import Block, Document

SENTENCE_DELIMITER = re.compile(r"(?<=[.!?])\s+")


@dataclass(frozen=True, slots=True)
class LongSentenceRule:
    """Rule that checks sentence word counts against STE limits."""

    id: str = "long-sentence"
    severity: Severity = Severity.HARD
    max_words: int = 25
    description: str = "Check for sentences exceeding length limits (max 25 words)."

    def check(self, document: Document) -> list[Finding]:
        """Report sentences in every block that exceed the word cap.

        Returns
        -------
        list[Finding]
            One finding per overlong sentence.

        """
        findings: list[Finding] = []
        for block in document.blocks:
            self._check_block(document, block, findings)
        return findings

    def _check_block(
        self,
        document: Document,
        block: Block,
        findings: list[Finding],
    ) -> None:
        """Check each sentence of `block`, ending with the trailing one."""
        spans = SENTENCE_DELIMITER.finditer(block.text)
        bounds = self._sentence_bounds(block.text, spans)
        for offset, sentence in bounds:
            self._check_sentence(document, block, offset, sentence, findings)

    @staticmethod
    def _sentence_bounds(
        text: str,
        spans: Iterator[re.Match[str]],
    ) -> list[tuple[int, str]]:
        """Return trimmed sentences with offsets, trailing one last.

        Returns
        -------
        list[tuple[int, str]]
            Sentence strings paired with their block-text offsets.

        """
        start = 0
        bounds: list[tuple[int, str]] = []
        ends = [match.end() for match in spans]
        for end in [*ends, len(text)]:
            raw_sentence = text[start:end]
            lead = len(raw_sentence) - len(raw_sentence.lstrip())
            sentence = raw_sentence.strip()
            if sentence:
                bounds.append((start + lead, sentence))
            start = end
        return bounds

    def _check_sentence(
        self,
        document: Document,
        block: Block,
        offset: int,
        sentence: str,
        findings: list[Finding],
    ) -> None:
        """Append a finding when `sentence` exceeds the word cap."""
        count = len(sentence.split())
        if count <= self.max_words:
            return
        line, col = block.locate(offset)
        if document.suppressions.silences(line, self.id):
            return
        findings.append(
            Finding(
                file=document.filename,
                line=line,
                column=col,
                rule=self.id,
                severity=self.severity,
                match=f"{count} words",
                message=f"Sentence has {count} words (cap {self.max_words}). Split it.",
            )
        )


LONG_SENTENCE_RULE = LongSentenceRule()
