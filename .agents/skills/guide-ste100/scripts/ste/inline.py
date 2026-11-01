"""Inline Markdown masking that preserves character offsets.

Every function here returns a string of the same length as its input. Markup is
replaced with spaces, and opaque operands (code spans, URLs) collapse to a
one-letter placeholder word. Rules then see plain prose, and a match offset in
the masked string is still a valid column in the source line.
"""

from __future__ import annotations

import re
from collections.abc import Callable

type Replacer = Callable[[re.Match[str]], str]

CODE_PLACEHOLDER = "C"
"""Stands in for a code span. Counts as one word and matches no rule."""

URL_PLACEHOLDER = "U"
"""Stands in for a URL. Counts as one word and matches no rule."""

CODE_SPAN = re.compile(r"(?<!`)(`+)(?!`)(.+?)(?<!`)\1(?!`)")
HTML_COMMENT = re.compile(r"<!--.*?-->")
IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
INLINE_LINK = re.compile(r"\[(?P<text>[^\]]*)\](?P<target>\([^)]*\)|\[[^\]]*\])")
FOOTNOTE_REF = re.compile(r"\[\^[^\]]+\]")
AUTOLINK = re.compile(r"<(?:https?|mailto|ftp):[^>\s]+>")
BARE_URL = re.compile(r"\bhttps?://[^\s)>\]]+")
HTML_TAG = re.compile(r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>]*)?/?>")
ENTITY = re.compile(r"&(?:#\d+|#x[0-9A-Fa-f]+|[A-Za-z][A-Za-z0-9]*);")
EMPHASIS = re.compile(r"\*{1,3}|(?<!\w)_{1,3}|_{1,3}(?!\w)|~~")
ESCAPE = re.compile(r"\\(?=[\\`*_{}\[\]()#+\-.!|<>~])")


def _blank(match: re.Match[str]) -> str:
    return " " * len(match.group(0))


def _placeholder(token: str) -> Replacer:
    def replace(match: re.Match[str]) -> str:
        return token + " " * (len(match.group(0)) - len(token))

    return replace


def _keep_link_text(match: re.Match[str]) -> str:
    return " " + match.group("text") + " " * len(match.group("target")) + " "


MASKS: tuple[tuple[re.Pattern[str], Replacer], ...] = (
    (CODE_SPAN, _placeholder(CODE_PLACEHOLDER)),
    (HTML_COMMENT, _blank),
    (IMAGE, _blank),
    (INLINE_LINK, _keep_link_text),
    (FOOTNOTE_REF, _blank),
    (AUTOLINK, _placeholder(URL_PLACEHOLDER)),
    (BARE_URL, _placeholder(URL_PLACEHOLDER)),
    (HTML_TAG, _blank),
    (ENTITY, _placeholder("&")),
    (ESCAPE, _blank),
    (EMPHASIS, _blank),
)
"""Applied in order. Code spans go first so their contents are never parsed."""


def mask_inline(text: str) -> str:
    """Replace inline Markdown markup with offset-preserving prose.

    >>> mask_inline("Run `uv sync` and see [the docs](https://x.dev).")
    'Run C         and see  the docs                .'
    >>> mask_inline("A **bold** claim.")
    'A   bold   claim.'

    Returns
    -------
    str
        Same-length masked text.

    """
    for pattern, replace in MASKS:
        text = pattern.sub(replace, text)
    return text
