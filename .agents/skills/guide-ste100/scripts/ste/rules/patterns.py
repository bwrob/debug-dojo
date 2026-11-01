"""Regex pattern-based structural STE rules."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from ste.model import Finding, Severity

if TYPE_CHECKING:
    from ste.model import Document


@dataclass(frozen=True, slots=True)
class PatternRule:
    """A rule that checks blocks for regex matches."""

    id: str
    severity: Severity
    pattern: re.Pattern[str]
    message: str
    description: str

    def check(self, document: Document) -> list[Finding]:
        """Report every pattern match found in the document blocks.

        Returns
        -------
        list[Finding]
            One finding per match, respecting inline suppressions.

        """
        findings: list[Finding] = []
        for block in document.blocks:
            for match in self.pattern.finditer(block.text):
                line, col = block.locate(match.start())
                if document.suppressions.silences(line, self.id):
                    continue
                findings.append(
                    Finding(
                        file=document.filename,
                        line=line,
                        column=col,
                        rule=self.id,
                        severity=self.severity,
                        match=match.group(0),
                        message=self.message,
                    )
                )
        return findings


SEMICOLON_RULE = PatternRule(
    id="semicolon",
    severity=Severity.HARD,
    pattern=re.compile(r";"),
    message="STE bans the semicolon (Rule 8.1). Split into separate sentences.",
    description="Check for prohibited semicolons.",
)

PHRASAL_VERB_RULE = PatternRule(
    id="phrasal-verb",
    severity=Severity.HARD,
    pattern=re.compile(
        r"\b(spin(?:ning|s)? up|spun up|spin(?:ning|s)? down|spun down|"
        r"reach(?:ing|es|ed)? out|div(?:e|es|ing|ed) into|dove into|"
        r"kick(?:ing|s|ed)? off|circl(?:e|es|ing|ed) back|touch(?:ing|es|ed)? base|"
        r"drill(?:ing|s|ed)? down|wrap(?:ping|s|ed)? up|ramp(?:ing|s|ed)? up|"
        r"tear(?:ing|s)? down|tore down|torn down|scale(?:s|d|ing)? up|"
        r"roll(?:ing|s|ed)? out|figur(?:e|es|ed|ing) out|point(?:ing|s|ed)? out)\b",
        re.IGNORECASE,
    ),
    message="Soft phrasal verb. Use the single plain verb "
    "(start, contact, read, begin).",
    description="Check for informal phrasal verbs.",
)

MARKETING_ADJECTIVE_RULE = PatternRule(
    id="marketing-adjective",
    severity=Severity.HARD,
    pattern=re.compile(
        r"\b(seamless(?:ly)?|robust(?:ly)?|cutting-edge|effortless(?:ly)?|"
        r"blazing(?:ly)?[- ]fast|lightning[- ]fast|rock[- ]solid|ultra[- ]fast|"
        r"world-class|state-of-the-art|game-chang(?:ing|er)|authoritative|"
        r"comprehensive|battle-tested|industry-standard|turnkey|bulletproof|"
        r"groundbreaking|transformative|testament|innovative|unprecedented|"
        r"meticulous(?:ly)?|holistic|multifaceted|vibrant)\b",
        re.IGNORECASE,
    ),
    message="Marketing adjective. Delete, or replace with the measurement "
    "that earns the claim.",
    description="Check for hyperbolic marketing adjectives.",
)

UNAPPROVED_PHRASE_RULE = PatternRule(
    id="unapproved-phrase",
    severity=Severity.HARD,
    pattern=re.compile(
        r"\b(in order to|prior to|subsequent to|with the exception of|"
        r"due to the fact that|in the event that|in the event of|"
        r"for the purpose of|at the present time|at this time|"
        r"with regard to|in regard to|with reference to|"
        r"is capable of|it is necessary to|in the vicinity of|"
        r"in conjunction with|in accordance with|a number of|"
        r"when it comes to|out of the box|under the hood|"
        r"at the end of the day|in conclusion|in summary|"
        r"enables you to|allows you to|aims to|"
        r"has the capability to|is able to|in view of the fact that|"
        r"it is recommended that)\b",
        re.IGNORECASE,
    ),
    message="Unapproved phrase. Use plain equivalents (to, before, after, "
    "except, because, if, now, about, can, must, near, with, under, some).",
    description="Check for wordy, unapproved multi-word connectives and phrases.",
)

UNAPPROVED_WORD_RULE = PatternRule(
    id="unapproved-word",
    severity=Severity.HARD,
    pattern=re.compile(
        r"\b(utiliz(?:e|es|ed|ing|ation)|"  # spellchecker:disable-line
        r"commenc(?:e|es|ed|ing|ement)|"
        r"ascertain(?:s|ed|ing)?|endeavor(?:s|ed|ing)?|"
        r"facilitat(?:e|es|ed|ing)|replenish(?:es|ed|ing)?|"
        r"procure(?:s|d|ing)?|procurement|rectif(?:y|ies|ied|ying)|"
        r"delve(?:s|d|ing)?|tapestry|plethora|myriad|streamline(?:s|d|ing)?|"
        r"bolster(?:s|ed|ing)?|elucidat(?:e|es|ed|ing)|foster(?:s|ed|ing)?|"
        r"harness(?:es|ed|ing)?|revolutioniz(?:e|es|ed|ing)|"
        r"preclude(?:s|d|ing)?|necessitat(?:e|es|ed|ing)|"
        r"hazardous|prescrib(?:e|es|ed|ing))\b",
        re.IGNORECASE,
    ),
    message="Unapproved word. Use simpler approved alternatives "
    "(use, start, find, try, help, fill, get, correct, prevent, need, "
    "dangerous, specify).",
    description="Check for complex, unapproved STE words.",
)

CONTRACTION_RULE = PatternRule(
    id="contraction",
    severity=Severity.HARD,
    pattern=re.compile(
        r"\b([a-zA-Z]+(?:n't|'ll|'re|'ve|'d)|it's|you're)\b",
        re.IGNORECASE,
    ),
    message="Contraction (Rule 4.2). Expand into full forms "
    "(do not, cannot, it is, you are).",
    description="Check for prohibited informal contractions.",
)

LATIN_ABBREV_RULE = PatternRule(
    id="latin-abbrev",
    severity=Severity.HARD,
    pattern=re.compile(
        r"\b(e\.g\.|i\.e\.|etc\.?)(?=[\s,.)]|\b)",
        re.IGNORECASE,
    ),
    message="Latin abbreviation (GR-6). Use plain alternatives "
    "(for example, that is) or list all items.",
    description="Check for Latin abbreviations (e.g., i.e., etc.).",
)

ING_CLAUSE_RULE = PatternRule(
    id="ing-clause",
    severity=Severity.HARD,
    pattern=re.compile(
        r",\s+(making|allowing|enabling|ensuring|creating|providing|"
        r"resulting|leading|causing|helping)\b",
        re.IGNORECASE,
    ),
    message="Subordinate '-ing' participle clause (Rule 3.5). Start a new "
    "sentence with an active subject and finite verb.",
    description="Check for trailing subordinate '-ing' participle clauses.",
)

NOMINALIZATION_RULE = PatternRule(
    id="nominalization",
    severity=Severity.HARD,
    pattern=re.compile(
        r"\b(perform|performs|performed|conduct|conducts|conducted|"
        r"carry out|carries out|carried out)"  # spellchecker:disable-line
        r"\s+(?:(?:a|an|the)\s+)?\w+(?:tion|sion|ment|ance|ence|ysis)\b",
        re.IGNORECASE,
    ),
    message="Action frozen into a noun. Use the verb (analyze, not "
    "perform an analysis of).",
    description="Check for nominalized verbs (e.g. 'perform an analysis').",
)

PASSIVE_VOICE_RULE = PatternRule(
    id="passive-voice",
    severity=Severity.ADVISORY,
    pattern=re.compile(
        r"\b(is|are|was|were|been|being)\s+(\w+ed|given|taken|made|done|"
        r"found|seen|known|shown|written|built|sent|set|run|read|kept|held|"
        r"left|put)\b(?!\s+(?:to|for|by)\s+\w+ing)",
        re.IGNORECASE,
    ),
    message="Possible passive voice. Name the actor and use an active "
    "verb, unless the actor is unknown or irrelevant.",
    description="Check for passive voice constructions (advisory).",
)

PRESENT_PERFECT_RULE = PatternRule(
    id="present-perfect",
    severity=Severity.ADVISORY,
    # Hedges (may have, might have, could have, should have, would have,
    # must have) are protected.
    pattern=re.compile(
        r"(?<!\bmay )(?<!\bmight )(?<!\bcould )(?<!\bshould )(?<!\bwould )(?<!\bmust )"
        r"\b(has|have|had)\s+(?:been\s+)?\w+(?:ed|en)\b",
        re.IGNORECASE,
    ),
    message="Compound tense. Use simple past/present unless current "
    "relevance is the point (then keep and flag).",
    description="Check for compound tenses / present perfect (advisory).",
)

BANNED_MODAL_RULE = PatternRule(
    id="banned-modal",
    severity=Severity.HARD,
    pattern=re.compile(r"\b(should|would|ought to)\b", re.IGNORECASE),
    message="Unapproved modal (Rule 3.2). State requirements with 'must' "
    "or imperative, or state as direct fact.",
    description="Check for unapproved modal verbs (should, would, ought to).",
)

TRAILING_CONDITION_RULE = PatternRule(
    id="trailing-condition",
    severity=Severity.ADVISORY,
    pattern=re.compile(r",\s+(?:if|when)\b", re.IGNORECASE),
    message="Trailing condition (Rule 5.4). Put the condition before the "
    "command (e.g. 'If X, do Y').",
    description="Check for trailing conditions placed after instructions.",
)

PATTERN_RULES: tuple[PatternRule, ...] = (
    SEMICOLON_RULE,
    PHRASAL_VERB_RULE,
    MARKETING_ADJECTIVE_RULE,
    UNAPPROVED_PHRASE_RULE,
    UNAPPROVED_WORD_RULE,
    CONTRACTION_RULE,
    LATIN_ABBREV_RULE,
    ING_CLAUSE_RULE,
    NOMINALIZATION_RULE,
    PASSIVE_VOICE_RULE,
    PRESENT_PERFECT_RULE,
    BANNED_MODAL_RULE,
    TRAILING_CONDITION_RULE,
)
