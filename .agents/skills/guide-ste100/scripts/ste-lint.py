#!/usr/bin/env python3
"""Deterministic structural linter for ASD-STE100 Simplified Technical English.

Modularized and adapted for repository conventions, reflowed Markdown,
GitHub alerts, Zensical admonitions, frontmatter descriptions, and inline suppressions.

Original creator: Dustin Yuchen Teng (https://github.com/danyuchn/asd-ste100-skill)
Licensed under the MIT License.
"""

from __future__ import annotations

import sys
from pathlib import Path

if __name__ == "__main__":
    # Ensure 'scripts' is on sys.path so 'import ste' works when run directly
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))

    from ste.cli import main

    sys.exit(main())
