"""STE (Simplified Technical English) modular linter package."""

from __future__ import annotations

from ste.engine import LintResult, lint_document, lint_text
from ste.markdown import parse
from ste.model import Block, BlockKind, Document, Finding, Severity, Span
from ste.rules.base import Rule
from ste.rules.registry import ALL_RULES, get_rules

__all__ = [
    "ALL_RULES",
    "Block",
    "BlockKind",
    "Document",
    "Finding",
    "LintResult",
    "Rule",
    "Severity",
    "Span",
    "get_rules",
    "lint_document",
    "lint_text",
    "parse",
]
