#!/usr/bin/env python3
"""Validate functional specification structural invariants in Spec-Driven Development.

Ensures that `.specs/<feature-id>/spec.md`:
1. Defines explicit In-Scope and Out-of-Scope boundaries.
2. Contains functional requirements written with EARS patterns.
3. Contains testable Given/When/Then acceptance scenarios.
4. Prevents premature implementation leakage (e.g. internal class/function definitions).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

console = Console(highlight=False)


@dataclass(frozen=True, slots=True)
class SpecValidationResult:
    """Result of specification validation."""

    spec_path: Path
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    requirement_count: int
    scenario_count: int


_PLACEHOLDER_PATTERN = re.compile(
    r"\[(?:Describe|Short Title|User Story|Happy Path|Error or Edge|Pending|Reason for"
    r"|Requirement statement|precondition|action occurs|expected observable"
    r"|expected handled).*?\]"
)

_EARS_PATTERNS = (
    re.compile(r"\bthe system must\b", re.IGNORECASE),
    re.compile(r"\bwhen\b.+\bmust\b", re.IGNORECASE),
    re.compile(r"\bwhile\b.+\bmust\b", re.IGNORECASE),
    re.compile(r"\bif\b.+\bthen\b.+\bmust\b", re.IGNORECASE),
)

_NO_REQUIRED_REQ_ERROR = (
    "No functional requirements found (expected 'REQ-001' or 'Requirement N')."
)
_NO_EARS_WARNING = (
    "No standard EARS patterns detected (e.g. 'The system must...',"
    " 'When... must...', 'If... then...')."
)
_NO_SCENARIO_ERROR = "No complete Given/When/Then acceptance scenarios found."
_CODE_LEAK_ERROR = (
    "Premature implementation details detected in spec.md: code block contains"
    " class/function definitions. Move technical architecture and code skeletons"
    " to plan.md."
)


def _required_sections_errors(content: str) -> list[str]:
    """Check In-Scope and Out-of-Scope section presence.

    Returns:
        Errors for each missing scope boundary section.

    """
    errors: list[str] = []

    # 1. Boundary Check: In-Scope and Out-of-Scope
    has_in_scope = bool(re.search(r"###?\s*In-Scope", content, re.IGNORECASE))
    has_out_of_scope = bool(re.search(r"###?\s*Out-of-Scope", content, re.IGNORECASE))

    if not has_in_scope:
        errors.append("Missing required 'In-Scope' section.")
    if not has_out_of_scope:
        errors.append("Missing required 'Out-of-Scope' section.")
    return errors


def _requirement_ids(content: str) -> set[str]:
    """Detect declared requirement identifiers, with a heading fallback.

    Returns:
        Normalized REQ-NNN ids, or an empty set when none could be found.

    """
    req_ids = {
        f"REQ-{int(match.group(1)):03d}"
        for match in re.finditer(r"\bREQ-(\d+)\b", content, re.IGNORECASE)
    }
    if req_ids:
        return req_ids

    return {
        f"REQ-{int(match.group(1)):03d}"
        for match in re.finditer(r"###?\s*Requirement\s*(\d+)", content, re.IGNORECASE)
    }


def _placeholder_warning(content: str) -> str | None:
    """Detect unfilled template placeholder markers.

    Returns:
        A warning message when placeholders remain, otherwise None.

    """
    placeholder_matches = _PLACEHOLDER_PATTERN.findall(content)
    if len(placeholder_matches) == 0:
        return None

    return (
        f"Specification contains {len(placeholder_matches)} unfilled template"
        f" placeholder marker(s) (e.g. '{placeholder_matches[0]}')."
        " Replace them before development."
    )


def _has_ears_patterns(content: str) -> bool:
    """Report whether the content uses one of the standard EARS patterns.

    Returns:
        True when any standard EARS pattern is present.

    """
    return any(pattern.search(content) for pattern in _EARS_PATTERNS)


def _code_leak_error(content: str) -> str | None:
    """Detect implementation details inside fenced code blocks.

    Returns:
        An error message when an untagged block defines classes or functions,
        otherwise None.

    """
    if "<!-- allow-code -->" in content:
        return None

    code_blocks = re.findall(r"```(?:python|py)?\n(.*?)\n```", content, re.DOTALL)
    for block in code_blocks:
        if not re.search(r"\b(?:class\s+\w+|def\s+\w+|@dataclass)\b", block):
            continue
        if "# example" in block.lower() or "# test input" in block.lower():
            continue
        return _CODE_LEAK_ERROR
    return None


def validate_spec_content(content: str, spec_path: Path) -> SpecValidationResult:
    """Validate specification content against SDD quality invariants.

    Returns:
        Validation result with errors, warnings, and detected counts.

    """
    errors = _required_sections_errors(content)
    warnings: list[str] = []

    # 2. Functional Requirements Check
    req_count = len(_requirement_ids(content))
    if req_count == 0:
        errors.append(_NO_REQUIRED_REQ_ERROR)

    placeholder_warning = _placeholder_warning(content)
    if placeholder_warning is not None:
        warnings.append(placeholder_warning)

    if not _has_ears_patterns(content):
        warnings.append(_NO_EARS_WARNING)

    # 3. Acceptance Criteria Check (Given / When / Then)
    scenario_count = _scenario_count(content)
    if scenario_count == 0:
        errors.append(_NO_SCENARIO_ERROR)

    # 4. Implementation Leakage Check
    leak_error = _code_leak_error(content)
    if leak_error is not None:
        errors.append(leak_error)

    return SpecValidationResult(
        spec_path=spec_path,
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        requirement_count=req_count,
        scenario_count=scenario_count,
    )


def _scenario_count(content: str) -> int:
    """Count complete Given/When/Then acceptance scenarios.

    Returns:
        The smallest keyword occurrence count across the triple.

    """
    given_matches = list(re.finditer(r"\bGiven\b", content))
    when_matches = list(re.finditer(r"\bWhen\b", content))
    then_matches = list(re.finditer(r"\bThen\b", content))
    return min(len(given_matches), len(when_matches), len(then_matches))


def validate_spec_file(spec_path: Path) -> SpecValidationResult:
    """Read and validate a specification file.

    Returns:
        Validation result, or an invalid result when the file is missing or
        unreadable.

    """
    if not spec_path.is_file():
        return SpecValidationResult(
            spec_path=spec_path,
            is_valid=False,
            errors=[f"Specification file not found: {spec_path}"],
            warnings=[],
            requirement_count=0,
            scenario_count=0,
        )

    try:
        content = spec_path.read_text(encoding="utf-8")
    except OSError as exc:
        return SpecValidationResult(
            spec_path=spec_path,
            is_valid=False,
            errors=[f"Failed to read specification file: {exc}"],
            warnings=[],
            requirement_count=0,
            scenario_count=0,
        )

    return validate_spec_content(content, spec_path)


_REPORT_ERRORS_HEADER = "### Errors (Must Fix Before Planning):"
_REPORT_WARNINGS_HEADER = "### Advisory Warnings:"


def format_validation_report(result: SpecValidationResult) -> str:
    """Format validation result into readable report.

    Returns:
        The markdown validation report, lines joined with newlines.

    """
    status = "Passed" if result.is_valid else "Failed"
    lines = [
        "## Specification Quality Linter Report",
        "",
        f"- **Target File**: `{result.spec_path}`",
        f"- **Status**: {status}",
        f"- **Requirements Detected**: {result.requirement_count}",
        f"- **Acceptance Scenarios**: {result.scenario_count}",
        "",
    ]

    if result.errors:
        lines.extend(
            (
                _REPORT_ERRORS_HEADER,
                *(f"- ❌ {err}" for err in result.errors),
                "",
            )
        )

    if result.warnings:
        lines.extend(
            (
                _REPORT_WARNINGS_HEADER,
                *(f"- ⚠️ {warn}" for warn in result.warnings),
                "",
            )
        )

    if result.is_valid and not result.warnings:
        lines.append(
            "✓ Specification satisfies all SDD structural invariants and is ready"
            " for planning."
        )

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for spec quality validation.

    Returns:
        0 when the specification is valid, otherwise 1.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Validate functional specification structural invariants in"
            " Spec-Driven Development."
        )
    )
    parser.add_argument(
        "spec_path",
        type=Path,
        help="Path to spec.md file or feature directory",
    )
    args = parser.parse_args(argv)

    spec_path = args.spec_path
    if spec_path.is_dir():
        spec_path /= "spec.md"

    result = validate_spec_file(spec_path)
    console.print(format_validation_report(result), markup=False, soft_wrap=True)

    return 0 if result.is_valid else 1


if __name__ == "__main__":
    sys.exit(main())
