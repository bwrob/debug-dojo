"""Rule protocol and common definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from ste.model import Document, Finding, Severity


class Rule(Protocol):
    """Protocol implemented by every STE structural rule."""

    @property
    def id(self) -> str:
        """Unique identifier of the rule (e.g. 'semicolon')."""
        ...

    @property
    def severity(self) -> Severity:
        """Whether findings for this rule are hard or advisory."""
        ...

    @property
    def description(self) -> str:
        """Brief human-readable summary of what the rule checks."""
        ...

    def check(self, document: Document) -> list[Finding]:
        """Inspect a document and return all rule violations."""
        ...
