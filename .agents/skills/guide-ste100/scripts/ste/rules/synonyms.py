"""Synonym rotation rule enforcing consistent terminology."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ste.model import Finding, Severity

if TYPE_CHECKING:
    from ste.model import Document

SYNONYM_GROUPS: tuple[tuple[str, ...], ...] = (
    ("check", "verify", "confirm", "validate"),
    ("delete", "remove", "erase"),
    ("start", "launch", "begin", "initiate"),
    ("stop", "halt", "terminate"),
    ("show", "display"),
    ("use", "utilize", "employ"),
    ("fix", "repair", "correct"),
    ("send", "transmit"),
    ("get", "retrieve", "fetch", "obtain"),
    ("change", "modify", "alter"),
    ("help", "assist", "aid"),
    ("choose", "select", "pick"),
    ("allow", "permit"),
)


def _word_pattern(base: str) -> re.Pattern[str]:
    return re.compile(rf"\b{base}(?:s|es|ed|d|ing)?\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class SynonymRotationRule:
    """Rule that flags rotating synonyms for the same action in a document."""

    id: str = "synonym-rotation"
    severity: Severity = Severity.HARD
    description: str = "Enforce one word per meaning across synonym groups."
    groups: tuple[tuple[str, ...], ...] = SYNONYM_GROUPS

    def check(self, document: Document) -> list[Finding]:
        """Report synonyms rotated away from each group's first word.

        Returns
        -------
        list[Finding]
            One finding per redundant synonym, in document order.

        """
        # Map group_idx and base_word to (line, col, match_text)
        seen: dict[tuple[int, str], tuple[int, int, str]] = {}
        patterns: dict[str, re.Pattern[str]] = {
            base: _word_pattern(base) for group in self.groups for base in group
        }

        for block in document.blocks:
            for gi, group in enumerate(self.groups):
                for base in group:
                    if (gi, base) in seen:
                        continue
                    pattern = patterns[base]
                    match = pattern.search(block.text)
                    if match:
                        line, col = block.locate(match.start())
                        seen[gi, base] = (line, col, match.group(0))

        return self._collect_findings(document, seen)

    def _collect_findings(
        self,
        document: Document,
        seen: dict[tuple[int, str], tuple[int, int, str]],
    ) -> list[Finding]:
        """Flag later synonyms over the first word of each present group.

        Returns
        -------
        list[Finding]
            Findings in document order, one per redundant synonym.

        """
        findings: list[Finding] = []
        for gi, group in enumerate(self.groups):
            present = [(seen[gi, base], base) for base in group if (gi, base) in seen]
            if len(present) > 1:
                # Sort in document order
                present.sort(key=lambda item: (item[0][0], item[0][1]))
                first_base = present[0][1]
                for (line, col, match_text), base in present[1:]:
                    if document.suppressions.silences(line, self.id):
                        continue
                    findings.append(
                        Finding(
                            file=document.filename,
                            line=line,
                            column=col,
                            rule=self.id,
                            severity=self.severity,
                            match=match_text,
                            message=(
                                f"'{base}' and '{first_base}' name the same action. "
                                "Pick one and use it every time."
                            ),
                        )
                    )

        return findings


SYNONYM_ROTATION_RULE = SynonymRotationRule()
