"""List item rules, such as dangling coordinating conjunctions."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ste.model import BlockKind, Finding, Severity

if TYPE_CHECKING:
    from collections.abc import Iterator

    from ste.model import Block, Document

CONJUNCTION_END = re.compile(r"\b(?P<word>and|or)\s*$", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class DanglingConjunctionRule:
    """Rule that flags list items ending with 'and' or 'or'."""

    id: str = "dangling-conjunction"
    severity: Severity = Severity.HARD
    description: str = "Flag list items ending with 'and' or 'or'."

    def check(self, document: Document) -> list[Finding]:
        """Report list items that end with a dangling conjunction.

        Returns
        -------
        list[Finding]
            One finding per dangling list item.

        """
        return [
            finding
            for block in document.blocks
            if block.kind == BlockKind.LIST_ITEM
            for finding in self._check_block(document, block)
        ]

    def _check_block(self, document: Document, block: Block) -> Iterator[Finding]:
        """Yield a finding when `block` ends with 'and' or 'or'.

        Yields
        ------
        Finding
            Hard finding naming the dangling conjunction.

        """
        match = CONJUNCTION_END.search(block.text)
        if match is None:
            return
        line, col = block.locate(match.start("word"))
        if document.suppressions.silences(line, self.id):
            return
        yield Finding(
            file=document.filename,
            line=line,
            column=col,
            rule=self.id,
            severity=self.severity,
            match=match.group("word"),
            message=(
                "List item ends with a coordinating conjunction. "
                "Complete the item or join it with the next item."
            ),
        )


DANGLING_CONJUNCTION_RULE = DanglingConjunctionRule()
