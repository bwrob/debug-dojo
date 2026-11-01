"""Registry and aggregation of STE structural rules."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ste.rules.lists import DANGLING_CONJUNCTION_RULE, DanglingConjunctionRule
from ste.rules.paragraphs import PARAGRAPH_LENGTH_RULE, ParagraphLengthRule
from ste.rules.patterns import (
    BANNED_MODAL_RULE,
    CONTRACTION_RULE,
    ING_CLAUSE_RULE,
    LATIN_ABBREV_RULE,
    MARKETING_ADJECTIVE_RULE,
    NOMINALIZATION_RULE,
    PASSIVE_VOICE_RULE,
    PATTERN_RULES,
    PHRASAL_VERB_RULE,
    PRESENT_PERFECT_RULE,
    SEMICOLON_RULE,
    TRAILING_CONDITION_RULE,
    UNAPPROVED_PHRASE_RULE,
    UNAPPROVED_WORD_RULE,
    PatternRule,
)
from ste.rules.sentences import LONG_SENTENCE_RULE, LongSentenceRule
from ste.rules.synonyms import SYNONYM_ROTATION_RULE, SynonymRotationRule

if TYPE_CHECKING:
    from collections.abc import Sequence

    from ste.rules.base import Rule

ALL_RULES: tuple[Rule, ...] = (
    *PATTERN_RULES,
    LONG_SENTENCE_RULE,
    SYNONYM_ROTATION_RULE,
    DANGLING_CONJUNCTION_RULE,
    PARAGRAPH_LENGTH_RULE,
)

RULE_MAP: dict[str, Rule] = {rule.id: rule for rule in ALL_RULES}

__all__ = [
    "ALL_RULES",
    "BANNED_MODAL_RULE",
    "CONTRACTION_RULE",
    "DANGLING_CONJUNCTION_RULE",
    "ING_CLAUSE_RULE",
    "LATIN_ABBREV_RULE",
    "LONG_SENTENCE_RULE",
    "MARKETING_ADJECTIVE_RULE",
    "NOMINALIZATION_RULE",
    "PARAGRAPH_LENGTH_RULE",
    "PASSIVE_VOICE_RULE",
    "PATTERN_RULES",
    "PHRASAL_VERB_RULE",
    "PRESENT_PERFECT_RULE",
    "RULE_MAP",
    "SEMICOLON_RULE",
    "SYNONYM_ROTATION_RULE",
    "TRAILING_CONDITION_RULE",
    "UNAPPROVED_PHRASE_RULE",
    "UNAPPROVED_WORD_RULE",
    "DanglingConjunctionRule",
    "LongSentenceRule",
    "ParagraphLengthRule",
    "PatternRule",
    "SynonymRotationRule",
    "get_rules",
]


def get_rules(disabled: Sequence[str] | None = None) -> tuple[Rule, ...]:
    """Return active rules, excluding any rule IDs listed in `disabled`.

    Parameters
    ----------
    disabled : Sequence[str] | None
        Rule IDs to exclude. `None` or empty selects every rule.

    Returns
    -------
    tuple[Rule, ...]
        Active rules in registry order, minus the disabled IDs.

    """
    if not disabled:
        return ALL_RULES
    disabled_set = set(disabled)
    return tuple(rule for rule in ALL_RULES if rule.id not in disabled_set)
