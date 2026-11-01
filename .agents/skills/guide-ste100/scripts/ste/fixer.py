"""Deterministic automated fixer for ASD-STE100 mechanical violations."""

from __future__ import annotations

import re

# Each entry pairs a pattern with its replacement. The order matters: multi-word
# phrases are listed first so they match before their individual words.
SAFE_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Latin abbreviations
    (re.compile(r"\b\(e\.g\.,?\s*", re.IGNORECASE), "(for example, "),
    (re.compile(r"\be\.g\.,?\s*", re.IGNORECASE), "for example, "),
    (re.compile(r"\b\(i\.e\.,?\s*", re.IGNORECASE), "(that is, "),
    (re.compile(r"\bi\.e\.,?\s*", re.IGNORECASE), "that is, "),
    # Multi-word unapproved phrases
    (re.compile(r"\bIn order to\b"), "To"),
    (re.compile(r"\bin order to\b"), "to"),
    (re.compile(r"\bPrior to\b"), "Before"),
    (re.compile(r"\bprior to\b"), "before"),
    (re.compile(r"\bSubsequent to\b"), "After"),
    (re.compile(r"\bsubsequent to\b"), "after"),
    (re.compile(r"\bDue to the fact that\b"), "Because"),
    (re.compile(r"\bdue to the fact that\b"), "because"),
    (re.compile(r"\bIn the event that\b"), "If"),
    (re.compile(r"\bin the event that\b"), "if"),
    (re.compile(r"\bWith the exception of\b"), "Except for"),
    (re.compile(r"\bwith the exception of\b"), "except for"),
    (re.compile(r"\bAt this time\b"), "Now"),
    (re.compile(r"\bat this time\b"), "now"),
    (re.compile(r"\bAt the present time\b"), "Now"),
    (re.compile(r"\bat the present time\b"), "now"),
    (re.compile(r"\bIs capable of\b"), "Can"),
    (re.compile(r"\bis capable of\b"), "can"),
    (re.compile(r"\bIs able to\b"), "Can"),
    (re.compile(r"\bis able to\b"), "can"),
    (re.compile(r"\bHas the capability to\b"), "Can"),
    (re.compile(r"\bhas the capability to\b"), "can"),
    # Contractions
    (re.compile(r"\bDon't\b"), "Do not"),
    (re.compile(r"\bdon't\b"), "do not"),
    (re.compile(r"\bDoesn't\b"), "Does not"),
    (re.compile(r"\bdoesn't\b"), "does not"),
    (re.compile(r"\bDidn't\b"), "Did not"),
    (re.compile(r"\bdidn't\b"), "did not"),
    (re.compile(r"\bCan't\b"), "Cannot"),
    (re.compile(r"\bcan't\b"), "cannot"),
    (re.compile(r"\bWon't\b"), "Will not"),
    (re.compile(r"\bwon't\b"), "will not"),
    (re.compile(r"\bIt's\b"), "It is"),
    (re.compile(r"\bit's\b"), "it is"),
    (re.compile(r"\bYou're\b"), "You are"),
    (re.compile(r"\byou're\b"), "you are"),
    (re.compile(r"\bWe're\b"), "We are"),
    (re.compile(r"\bwe're\b"), "we are"),
    (re.compile(r"\bThey're\b"), "They are"),
    (re.compile(r"\bthey're\b"), "they are"),
    (re.compile(r"\bWe'll\b"), "We will"),
    (re.compile(r"\bwe'll\b"), "we will"),
    (re.compile(r"\bThey'll\b"), "They will"),
    (re.compile(r"\bthey'll\b"), "they will"),
    (re.compile(r"\bYou'll\b"), "You will"),
    (re.compile(r"\byou'll\b"), "you will"),
    (re.compile(r"\bCouldn't\b"), "Could not"),
    (re.compile(r"\bcouldn't\b"), "could not"),
    (re.compile(r"\bShouldn't\b"), "Should not"),
    (re.compile(r"\bshouldn't\b"), "should not"),
    (re.compile(r"\bWouldn't\b"), "Would not"),
    (re.compile(r"\bwouldn't\b"), "would not"),
    (re.compile(r"\bAren't\b"), "Are not"),
    (re.compile(r"\baren't\b"), "are not"),
    (re.compile(r"\bIsn't\b"), "Is not"),
    (re.compile(r"\bisn't\b"), "is not"),
    (re.compile(r"\bHaven't\b"), "Have not"),
    (re.compile(r"\bhaven't\b"), "have not"),
    (re.compile(r"\bHasn't\b"), "Has not"),
    (re.compile(r"\bhasn't\b"), "has not"),
    # Unapproved words (utilize -> use, commence -> start, etc.)
    (re.compile(r"\bUtilize\b"), "Use"),
    (re.compile(r"\butilize\b"), "use"),
    (re.compile(r"\bUtilizes\b"), "Uses"),
    (re.compile(r"\butilizes\b"), "uses"),
    (re.compile(r"\bUtilized\b"), "Used"),
    (re.compile(r"\butilized\b"), "used"),
    (re.compile(r"\bUtilizing\b"), "Using"),
    (re.compile(r"\butilizing\b"), "using"),
    (re.compile(r"\bUtilization\b"), "Use"),
    (re.compile(r"\butilization\b"), "use"),
    (re.compile(r"\bCommence\b"), "Start"),
    (re.compile(r"\bcommence\b"), "start"),
    (re.compile(r"\bCommences\b"), "Starts"),
    (re.compile(r"\bcommences\b"), "starts"),
    (re.compile(r"\bCommenced\b"), "Started"),
    (re.compile(r"\bcommenced\b"), "started"),
    (re.compile(r"\bCommencing\b"), "Starting"),
    (re.compile(r"\bcommencing\b"), "starting"),
    (re.compile(r"\bFacilitate\b"), "Help"),
    (re.compile(r"\bfacilitate\b"), "help"),
    (re.compile(r"\bFacilitates\b"), "Helps"),
    (re.compile(r"\bfacilitates\b"), "helps"),
    (re.compile(r"\bFacilitated\b"), "Helped"),
    (re.compile(r"\bfacilitated\b"), "helped"),
    (re.compile(r"\bPreclude\b"), "Prevent"),
    (re.compile(r"\bpreclude\b"), "prevent"),
    (re.compile(r"\bPrecludes\b"), "Prevents"),
    (re.compile(r"\bprecludes\b"), "prevents"),
    (re.compile(r"\bNecessitate\b"), "Need"),
    (re.compile(r"\bnecessitate\b"), "need"),
    (re.compile(r"\bNecessitates\b"), "Needs"),
    (re.compile(r"\bnecessitates\b"), "needs"),
    (re.compile(r"\bHazardous\b"), "Dangerous"),
    (re.compile(r"\bhazardous\b"), "dangerous"),
)


def _substitute_all(text: str) -> tuple[str, int]:
    """Apply every safe replacement to `text` and count the substitutions.

    Returns
    -------
    tuple[str, int]
        Rewritten text and the number of replacements made.

    """
    fixed = text
    total_subs = 0
    for pattern, replacement in SAFE_REPLACEMENTS:
        fixed, count = pattern.subn(replacement, fixed)
        total_subs += count
    return fixed, total_subs


def fix_line(line: str) -> tuple[str, int]:
    """Apply safe replacements to prose parts of a single line.

    Preserves text inside inline code backticks (`...`).

    Returns
    -------
    tuple[str, int]
        Fixed line and the number of replacements made outside code.

    """
    if "`" not in line:
        return _substitute_all(line)

    parts = line.split("`")
    total_subs = 0
    # Even indices hold prose; odd indices hold code spans.
    for idx in range(0, len(parts), 2):
        parts[idx], count = _substitute_all(parts[idx])
        total_subs += count

    return "`".join(parts), total_subs


def fix_text(text: str) -> tuple[str, int]:
    """Apply deterministic 1:1 STE fixes to text.

    Skips fenced code blocks and inline suppression regions.

    Returns
    -------
    tuple[str, int]
        Fixed text and the total count of replacements made.

    """
    lines = text.splitlines(keepends=True)
    in_fence = False
    in_suppression = False
    fence_char = ""
    fixed_lines: list[str] = []
    total_replacements = 0

    for line in lines:
        stripped = line.strip()

        # Handle code block fences
        if not in_fence:
            if stripped.startswith(("```", "~~~")):
                in_fence = True
                fence_char = stripped[:3]
                fixed_lines.append(line)
                continue
        else:
            if stripped.startswith(fence_char):
                in_fence = False
            fixed_lines.append(line)
            continue

        # Handle inline directive comments
        if "<!-- ste-lint-disable" in line:
            in_suppression = True
            fixed_lines.append(line)
            continue
        if "<!-- ste-lint-enable" in line:
            in_suppression = False
            fixed_lines.append(line)
            continue

        if in_suppression:
            fixed_lines.append(line)
            continue

        fixed, count = fix_line(line)
        fixed_lines.append(fixed)
        total_replacements += count

    return "".join(fixed_lines), total_replacements
