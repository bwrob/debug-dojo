"""Core linting engine orchestrating parsing and rule execution."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from ste.markdown import parse
from ste.model import Finding, Severity
from ste.rules.registry import ALL_RULES

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ste.model import Document
    from ste.rules.base import Rule


@dataclass(frozen=True, slots=True)
class LintResult:
    """Aggregated lint results for a document or batch of documents."""

    filename: str
    findings: list[Finding]
    words_total: int

    @property
    def hard_count(self) -> int:
        """Count of non-advisory violations that affect the exit code.

        Returns
        -------
        int
            Number of findings of severity `hard`.

        """
        return sum(1 for finding in self.findings if finding.severity == Severity.HARD)

    @property
    def advisory_count(self) -> int:
        """Count of advisory violations.

        Returns
        -------
        int
            Number of findings of severity `advisory`.

        """
        return sum(
            1 for finding in self.findings if finding.severity == Severity.ADVISORY
        )

    @property
    def violation_rate(self) -> float:
        """Violations found per 100 words.

        Returns
        -------
        float
            0.0 for empty documents; rounded totals otherwise.

        """
        if not self.words_total:
            return 0.0
        return round(len(self.findings) * 100 / self.words_total, 1)


def lint_document(
    document: Document,
    rules: Sequence[Rule] | None = None,
) -> LintResult:
    """Lint an already parsed Document against the specified rules.

    Parameters
    ----------
    document : Document
        Parsed Markdown prose to inspect.
    rules : Sequence[Rule] | None
        Active rules; `None` selects every registered rule.

    Returns
    -------
    LintResult
        Findings sorted by position, plus the document word count.

    """
    active_rules = rules if rules is not None else ALL_RULES
    findings: list[Finding] = []

    for rule in active_rules:
        findings.extend(rule.check(document))

    findings.sort(key=lambda finding: (finding.line, finding.column, finding.rule))
    words_total = sum(len(block.text.split()) for block in document.blocks)

    return LintResult(
        filename=document.filename,
        findings=findings,
        words_total=words_total,
    )


def lint_text(
    text: str,
    filename: str = "<stdin>",
    rules: Sequence[Rule] | None = None,
) -> LintResult:
    """Parse and lint Markdown text.

    Parameters
    ----------
    text : str
        Markdown source to inspect.
    filename : str
        Name shown in the findings.
    rules : Sequence[Rule] | None
        Active rules; `None` selects every registered rule.

    Returns
    -------
    LintResult
        Aggregated findings for the parsed text.

    """
    document = parse(text, filename=filename)
    return lint_document(document, rules=rules)
