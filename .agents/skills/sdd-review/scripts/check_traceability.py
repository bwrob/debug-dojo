#!/usr/bin/env python3
"""Automated Requirement-to-Test Traceability Matrix Validator.

This script:
1. Parses `.specs/<feature-id>/spec.md` to extract declared requirement IDs
   (e.g. `REQ-001`).
2. Scans `tests/` for test functions referencing those requirement IDs in their
   names, docstrings, comments, or pytest markers.
3. Generates a markdown traceability matrix.
4. Returns exit code 1 if any requirement lacks test coverage.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

console = Console(highlight=False)


@dataclass(frozen=True, slots=True)
class RequirementInfo:
    """Requirement metadata extracted from specification."""

    req_id: str
    title: str
    scenarios: list[str]


@dataclass(frozen=True, slots=True)
class TraceabilityResult:
    """Traceability analysis result."""

    spec_path: Path
    tests_dir: Path
    requirements: list[RequirementInfo]
    req_to_tests: dict[str, list[str]]
    missing_tests: list[str]
    unmapped_tests: dict[str, list[str]]


def extract_requirements_from_spec(spec_path: Path) -> list[RequirementInfo]:
    """Parse spec.md to extract requirement IDs, titles, and scenarios.

    Returns:
        Declared requirements, or the casual REQ-NNN mentions when the
        structured format could not be parsed.

    """
    if not spec_path.is_file():
        return []

    try:
        content = spec_path.read_text(encoding="utf-8")
    except OSError:
        return []

    requirements = _structured_requirements(content)
    return requirements or _fallback_requirements(content)


def _seal(
    requirements: list[RequirementInfo],
    current_req_id: str | None,
    current_title: str,
    current_scenarios: list[str],
) -> None:
    """Append the open requirement under construction, if any, to the results."""
    if current_req_id is None:
        return
    requirements.append(
        RequirementInfo(
            req_id=current_req_id,
            title=current_title or current_req_id,
            scenarios=current_scenarios,
        )
    )


def _header_requirement(line: str) -> tuple[str | None, str]:
    """Parse a `### Requirement N: Title` heading line.

    Returns:
        An optional embedded REQ id plus the cleaned heading title.

    """
    header_match = re.search(r"###?\s*Requirement\s*\d+:\s*(.+)", line, re.IGNORECASE)
    if header_match is None:
        return None, ""

    raw_title = header_match.group(1).strip()
    embedded_match = re.search(r"\b(REQ-\d+)\b", raw_title, re.IGNORECASE)
    if embedded_match:
        req_id = embedded_match.group(1).upper()
        clean_title = re.sub(
            r"\(?\bREQ-\d+\)?\s*[:-]?\s*", "", raw_title, flags=re.IGNORECASE
        ).strip()
        return req_id, clean_title or req_id
    return None, raw_title


def _line_requirement_id(line: str) -> str | None:
    """Extract an explicit REQ-NNN identifier from one spec line.

    Returns:
        The uppercased requirement id, or None when the line declares none.

    """
    req_match = re.search(r"-\s*\*\*ID\*\*:\s*`?(REQ-\d+)`?", line, re.IGNORECASE)
    if req_match is None:
        req_match = re.search(
            r"###?\s*Requirement\s*\d+:\s*`?(REQ-\d+)`?", line, re.IGNORECASE
        )
    return req_match.group(1).upper() if req_match else None


def _structured_requirements(content: str) -> list[RequirementInfo]:
    """Walk the spec document line by line to collect declared requirements.

    Returns:
        Structured requirement entries with titles and scenarios.

    """
    requirements: list[RequirementInfo] = []
    current_req_id: str | None = None
    current_title = ""
    current_scenarios: list[str] = []

    for line in content.splitlines():
        if line.strip().startswith("## "):
            _seal(requirements, current_req_id, current_title, current_scenarios)

            current_req_id = None
            current_title = ""
            current_scenarios = []
            continue

        header_req_id, header_title = _header_requirement(line)
        if header_title:
            _seal(requirements, current_req_id, current_title, current_scenarios)

            current_req_id = header_req_id
            current_title = header_title
            current_scenarios = []

        req_id = _line_requirement_id(line)
        if req_id:
            if current_req_id and current_req_id != req_id:
                _seal(requirements, current_req_id, current_title, current_scenarios)
                current_scenarios = []
            current_req_id = req_id

        scenario_match = re.search(
            r"###?\s*Scenario\s*\d+:\s*(.+)", line, re.IGNORECASE
        )
        if scenario_match and current_req_id:
            current_scenarios.append(scenario_match.group(1).strip())

    _seal(requirements, current_req_id, current_title, current_scenarios)
    return requirements


def _fallback_requirements(content: str) -> list[RequirementInfo]:
    """Collect casual REQ-NNN mentions when no structured format is present.

    Returns:
        Requirements built from every distinct id mentioned in the text.

    """
    found_ids = sorted(set(re.findall(r"\bREQ-\d+\b", content, re.IGNORECASE)))
    return [
        RequirementInfo(req_id=rid.upper(), title=rid.upper(), scenarios=[])
        for rid in found_ids
    ]


def scan_tests_for_requirements(tests_dir: Path) -> dict[str, list[str]]:
    """Scan test directory for references to REQ-NNN in test files.

    Returns:
        Mapping from normalized REQ-NNN ids to discovered test references.

    """
    req_to_tests: dict[str, list[str]] = {}

    if not tests_dir.is_dir():
        return req_to_tests

    for test_file in sorted(tests_dir.rglob("test_*.py")):
        try:
            content = test_file.read_text(encoding="utf-8")
        except OSError:
            continue

        try:
            tree = ast.parse(content)
        except SyntaxError:
            continue

        for node in ast.walk(tree):
            if not _is_test_function(node):
                continue
            test_ref = f"{test_file.name}::{node.name}"
            for req_id in _collected_req_refs(node):
                req_to_tests.setdefault(req_id, []).append(test_ref)

    return req_to_tests


def _is_test_function(node: ast.AST) -> bool:
    """Report whether the node defines a test-named function.

    Returns:
        True for function definitions whose name starts with ``test_``.

    """
    return isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and (
        node.name.startswith("test_")
    )


def _normalized_req(raw_number: str) -> str:
    """Format captured requirement digits into a REQ-NNN id.

    Returns:
        The zero-padded REQ-NNN identifier.

    """
    return f"REQ-{int(raw_number):03d}"


def _collected_req_refs(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    """Collect REQ-NNN identifiers referenced by one test function.

    Returns:
        Ids referenced in the function name, docstring, or pytest markers.

    """
    refs: set[str] = set()

    # 1. Match from function name (e.g. test_req_001_...) with underscore boundaries
    refs.update(
        _normalized_req(match.group(1))
        for match in re.finditer(r"(?:^|_)req_?(\d+)(?:_|$)", node.name, re.IGNORECASE)
    )

    # 2. Match from docstring
    docstring = ast.get_docstring(node) or ""
    refs.update(
        _normalized_req(match.group(1))
        for match in re.finditer(r"\bREQ-(\d+)\b", docstring, re.IGNORECASE)
    )

    # 3. Match from pytest mark decorators (@pytest.mark.req("REQ-001"), etc.)
    for decorator in node.decorator_list:
        refs.update(_decorator_req_refs(decorator))

    return refs


def _decorator_req_refs(decorator: ast.expr) -> set[str]:
    """Collect REQ-NNN ids from string arguments of a decorator call.

    Returns:
        Ids referenced inside the decorator string arguments.

    """
    if not isinstance(decorator, ast.Call):
        return set()

    refs: set[str] = set()
    for arg in decorator.args:
        if not (isinstance(arg, ast.Constant) and isinstance(arg.value, str)):
            continue
        refs.update(
            _normalized_req(match.group(1))
            for match in re.finditer(r"\bREQ-(\d+)\b", arg.value, re.IGNORECASE)
        )
        refs.update(
            _normalized_req(match.group(1))
            for match in re.finditer(r"^\s*(\d+)\s*$", arg.value)
        )
    return refs


def analyze_traceability(spec_path: Path, tests_dir: Path) -> TraceabilityResult:
    """Analyze traceability between specification requirements and test files.

    Returns:
        Structured result mapping requirements to tests and coverage gaps.

    """
    requirements = extract_requirements_from_spec(spec_path)
    req_to_tests = scan_tests_for_requirements(tests_dir)

    known_ids = {r.req_id for r in requirements}
    missing = [r.req_id for r in requirements if not req_to_tests.get(r.req_id)]
    unmapped = {k: v for k, v in req_to_tests.items() if k not in known_ids}

    return TraceabilityResult(
        spec_path=spec_path,
        tests_dir=tests_dir,
        requirements=requirements,
        req_to_tests=req_to_tests,
        missing_tests=missing,
        unmapped_tests=unmapped,
    )


_TABLE_HEADER = (
    "| Requirement ID | Requirement Title | Associated Test Case | Status |",
    "| :--- | :--- | :--- | :--- |",
)
_VERIFIED_STATUS = "✓ Verified"
_MISSING_STATUS = "❌ Missing Test"
_NO_TESTS_PLACEHOLDER = "*None found*"


def format_traceability_table(result: TraceabilityResult) -> str:
    """Format traceability matrix as markdown table.

    Returns:
        The markdown table, one row per declared requirement.

    """
    lines = list(_TABLE_HEADER)
    for req in result.requirements:
        tests = result.req_to_tests.get(req.req_id, [])
        lines.append(_table_row_line(req, tests))
    return "\n".join(lines)


def _table_row_line(req: RequirementInfo, tests: list[str]) -> str:
    """Build one markdown table row for a requirement.

    Returns:
        The formatted row with status and associated tests.

    """
    if tests:
        test_list = "<br/>".join(f"`{t}`" for t in tests)
        status = _VERIFIED_STATUS
    else:
        test_list = _NO_TESTS_PLACEHOLDER
        status = _MISSING_STATUS
    return f"| `{req.req_id}` | {req.title} | {test_list} | {status} |"


_REPORT_TITLE = "## Requirement Traceability Audit Report"
_ALL_VERIFIED_NOTE = (
    "✓ All specification requirements have passing automated test coverage."
)


def format_traceability_report(result: TraceabilityResult) -> str:
    """Format full traceability audit report.

    Returns:
        The markdown audit report, lines joined with newlines.

    """
    requirements = len(result.requirements)
    missing = len(result.missing_tests)
    lines = [
        _REPORT_TITLE,
        "",
        f"- **Spec File**: `{result.spec_path}`",
        f"- **Tests Directory**: `{result.tests_dir}`",
        f"- **Requirements Declared**: {requirements}",
        f"- **Requirements Verified**: {requirements - missing}",
        f"- **Missing Verification**: {missing}",
        "",
        "### Traceability Matrix",
        "",
        format_traceability_table(result),
        "",
    ]

    if result.missing_tests:
        lines.append("### Missing Test Coverage")
        lines.extend(
            f"- ❌ `{req_id}` lacks an automated test case in `tests/`."
            for req_id in result.missing_tests
        )
        lines.append("")

    if result.unmapped_tests:
        lines.append("### Unmapped Requirement Tags in Tests")
        lines.extend(
            f"- ⚠️ `{req_id}` is referenced in tests {tests} but is not declared in"
            " `spec.md`."
            for req_id, tests in sorted(result.unmapped_tests.items())
        )
        lines.append("")

    if not result.missing_tests:
        lines.append(_ALL_VERIFIED_NOTE)

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for traceability verification.

    Returns:
        0 when every declared requirement is covered, otherwise 1.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Verify requirement-to-test traceability matrix in Spec-Driven Development."
        )
    )
    parser.add_argument("spec_path", type=Path, help="Path to spec.md")
    parser.add_argument(
        "--tests-dir",
        type=Path,
        default=Path("tests"),
        help="Path to tests/ directory",
    )
    parser.add_argument(
        "--table-only", action="store_true", help="Output only the markdown table"
    )
    args = parser.parse_args(argv)

    spec_path = args.spec_path
    if spec_path.is_dir():
        spec_path /= "spec.md"

    result = analyze_traceability(spec_path, args.tests_dir)

    if args.table_only:
        console.print(format_traceability_table(result), markup=False, soft_wrap=True)
    else:
        console.print(format_traceability_report(result), markup=False, soft_wrap=True)

    return 1 if result.missing_tests else 0


if __name__ == "__main__":
    sys.exit(main())
