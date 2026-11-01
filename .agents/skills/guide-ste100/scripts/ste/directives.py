"""Inline suppression directives written as HTML comments.

The syntax mirrors rumdl's `<!-- rumdl-disable -->` comments:

- `<!-- ste-lint-disable -->` silences rules until a matching enable.
- `<!-- ste-lint-enable -->` ends a disable.
- `<!-- ste-lint-disable-next-line -->` silences rules on the next line.
- `<!-- ste-lint-disable-file -->` silences rules in the whole file.

Each directive takes an optional comma- or space-separated rule list. Without a
list, it applies to every rule.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from ste.model import Suppressions

if TYPE_CHECKING:
    from collections.abc import Iterable


class Action(StrEnum):
    """What a directive does."""

    DISABLE = "disable"
    ENABLE = "enable"
    DISABLE_NEXT_LINE = "disable-next-line"
    DISABLE_FILE = "disable-file"


DIRECTIVE = re.compile(
    r"^\s*ste-lint-(?P<action>disable-next-line|disable-file|disable|enable)"
    r"(?P<rules>(?:\s+[\w,\s-]*)?)\s*$"
)


@dataclass(frozen=True, slots=True)
class Directive:
    """One parsed directive and the line of its comment."""

    line: int
    action: Action
    rules: frozenset[str]


def parse_directive(comment_body: str, line: int) -> Directive | None:
    """Parse the text between `<!--` and `-->`. Return `None` for other comments.

    >>> directive = parse_directive(" ste-lint-disable semicolon, long-sentence ", 3)
    >>> directive.action, sorted(directive.rules)
    (<Action.DISABLE: 'disable'>, ['long-sentence', 'semicolon'])
    >>> parse_directive(" a normal comment ", 3) is None
    True

    Returns
    -------
    Directive | None
        Parsed directive, or `None` for a non-directive comment.

    """
    match = DIRECTIVE.match(comment_body)
    if match is None:
        return None
    rules = frozenset(re.split(r"[\s,]+", match.group("rules").strip())) - {""}
    return Directive(line=line, action=Action(match.group("action")), rules=rules)


def build_suppressions(directives: Iterable[Directive], last_line: int) -> Suppressions:
    """Fold directives in document order into suppressed line ranges.

    Returns
    -------
    Suppressions
        Ranges with silencing start/end lines and the rule sets.

    """
    ranges: list[tuple[int, int, frozenset[str]]] = []
    open_disables: dict[frozenset[str], int] = {}
    for directive in directives:
        match directive.action:
            case Action.DISABLE_FILE:
                ranges.append((1, last_line, directive.rules))
            case Action.DISABLE_NEXT_LINE:
                ranges.append((directive.line + 1, directive.line + 1, directive.rules))
            case Action.DISABLE:
                open_disables.setdefault(directive.rules, directive.line)
            case Action.ENABLE:
                ranges.extend(_close(open_disables, directive))
    ranges.extend((start, last_line, rules) for rules, start in open_disables.items())
    return Suppressions(tuple(ranges))


def _close(
    open_disables: dict[frozenset[str], int], directive: Directive
) -> list[tuple[int, int, frozenset[str]]]:
    """Close the disables an enable matches. A bare enable closes all.

    Returns
    -------
    list[tuple[int, int, frozenset[str]]]
        Closed ranges in document order.

    """
    keys = [k for k in open_disables if not directive.rules or k == directive.rules]
    return [(open_disables.pop(key), directive.line, key) for key in keys]
