#!/usr/bin/env python3
"""Check public API diffs using Griffe and verify against the implementation plan.

This script:
1. Runs `griffe check` to detect breaking changes against a base git reference.
2. Extracts public symbols from the package and compares them against declared
   interfaces in `.specs/<feature-id>/plan.md`.
3. Reports planned additions, unplanned public symbols (scope creep), and
   breaking changes.
4. Generates a developer confirmation checklist for the review artifact.
"""

from __future__ import annotations

import argparse
import ast
import re
import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import]
import sys
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

console = Console(highlight=False)
err_console = Console(stderr=True, highlight=False)

# Resolved at import time; falls back to the bare command name, which lets
# subprocess raise the customary FileNotFoundError that callers interpret.
_GIT_BIN = shutil.which("git") or "git"
_UV_BIN = shutil.which("uv") or "uv"

_EXIT_COMMAND_NOT_FOUND = 127


@dataclass(frozen=True, slots=True)
class ApiDiffResult:
    """Structured result of public API analysis."""

    package_name: str
    base_ref: str
    griffe_available: bool
    breaking_changes: list[str]
    current_public_symbols: list[str]
    base_public_symbols: list[str]
    added_symbols: list[str]
    removed_symbols: list[str]
    planned_symbols: list[str]
    unplanned_symbols: list[str]
    missing_planned_symbols: list[str]


def detect_package_name(cwd: Path) -> str | None:
    """Detect Python package name from src/ directory or pyproject.toml.

    Returns:
        The detected package name, or None when no package could be located.

    """
    src_dir = cwd / "src"
    if src_dir.is_dir():
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / "__init__.py").exists():
                return child.name

    pyproject = cwd / "pyproject.toml"
    if pyproject.is_file():
        content = pyproject.read_text(encoding="utf-8")
        match = re.search(r'name\s*=\s*["\']([^"\']+)["\']', content)
        if match:
            return match.group(1).replace("-", "_")

    return None


def get_default_base_ref() -> str:
    """Determine the default git reference to compare against.

    Returns:
        The first resolvable git reference, or "HEAD" when none verify.

    """
    for ref in ("origin/main", "main", "origin/master", "master", "HEAD~1"):
        res = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
            [_GIT_BIN, "rev-parse", "--verify", ref],
            capture_output=True,
            text=True,
            check=False,
        )
        if res.returncode == 0:
            return ref
    return "HEAD"


def run_griffe_check(
    package_name: str,
    base_ref: str,
    search_dir: str = "src",
) -> tuple[bool, list[str]]:
    """Execute griffe check via subprocess and collect breaking change notices.

    Returns:
        A tuple of (griffe availability, collected breaking change notices).

    """
    cmd = [
        _UV_BIN,
        "run",
        "griffe",
        "check",
        package_name,
        "--search",
        search_dir,
        "--against",
        base_ref,
    ]

    try:
        proc = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False, ["uv executable not found"]

    command_not_found = proc.returncode == _EXIT_COMMAND_NOT_FOUND
    if command_not_found or "No such file or directory" in proc.stderr:
        # Griffe is not installed or available
        return False, []

    output = (proc.stdout + "\n" + proc.stderr).strip()
    breaking: list[str] = []
    if proc.returncode != 0 and output:
        breaking.extend(
            line_stripped
            for line in output.splitlines()
            if (line_stripped := line.strip()) and not line_stripped.startswith("INFO")
        )

    return True, breaking


def _exported_all_names(tree: ast.Module) -> list[str]:
    """Collect string entries exported through ``__all__`` assignments.

    Returns:
        Entries of any ``__all__`` assignment holding a list or tuple.

    """
    symbols: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets_all = (
            isinstance(target, ast.Name) and target.id == "__all__"
            for target in node.targets
        )
        if not any(targets_all):
            continue
        if isinstance(node.value, (ast.List, ast.Tuple)):
            symbols.extend(
                element.value
                for element in node.value.elts
                if isinstance(element, ast.Constant) and isinstance(element.value, str)
            )
    return symbols


def _top_level_names(tree: ast.Module) -> list[str]:
    """Collect public top-level names when no ``__all__`` is present.

    Returns:
        Sorted names of public classes, functions, and PEP 695 type aliases.

    """
    symbols = [
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        and not node.name.startswith("_")
    ]
    if not hasattr(ast, "TypeAlias"):
        return sorted(set(symbols))

    symbols.extend(
        node.name.id
        for node in tree.body
        if isinstance(node, ast.TypeAlias)
        and isinstance(node.name, ast.Name)
        and not node.name.id.startswith("_")
    )
    return sorted(set(symbols))


def extract_public_symbols_from_ast(code: str) -> list[str]:
    """Extract public classes, functions, and __all__ exports using standard AST.

    Returns:
        Sorted public symbol names, or an empty list when parsing fails.

    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    explicit_exports = _exported_all_names(tree)
    if explicit_exports:
        return sorted(set(explicit_exports))

    return _top_level_names(tree)


def get_package_public_symbols(package_dir: Path) -> list[str]:
    """Scan package directory for public symbols across __init__.py and modules.

    Returns:
        Sorted public symbol names found in the package sources.

    """
    symbols: list[str] = []
    init_file = package_dir / "__init__.py"
    if init_file.is_file():
        init_text = init_file.read_text(encoding="utf-8")
        init_symbols = extract_public_symbols_from_ast(init_text)
        if init_symbols:
            return sorted(set(init_symbols))

    # Scan python files in package recursively, skipping private modules and __pycache__
    for py_file in sorted(package_dir.rglob("*.py")):
        if _is_private_path(py_file.parts):
            continue
        try:
            content = py_file.read_text(encoding="utf-8")
            symbols.extend(extract_public_symbols_from_ast(content))
        except OSError:
            continue

    return sorted(set(symbols))


def _is_private_path(parts: tuple[str, ...]) -> bool:
    """Report whether any path component is private (underscore-prefixed).

    Returns:
        True when any path component starts with an underscore.

    """
    return parts[-1].startswith("_") or any(part.startswith("_") for part in parts)


def get_git_file_content(ref: str, rel_path: str) -> str | None:
    """Fetch content of a file at a specific git ref.

    Returns:
        File content at the given ref, or None when git cannot show it.

    """
    proc = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        [_GIT_BIN, "show", f"{ref}:{rel_path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode == 0:
        return proc.stdout
    return None


def get_base_public_symbols(
    base_ref: str,
    package_name: str,
    search_dir: str = "src",
) -> list[str]:
    """Extract public symbols from the base git reference.

    Returns:
        Sorted public symbol names at the base reference.

    """
    init_path = f"{search_dir}/{package_name}/__init__.py"
    content = get_git_file_content(base_ref, init_path)
    if content:
        symbols = extract_public_symbols_from_ast(content)
        if symbols:
            return symbols

    # List files in git tree for package
    proc = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        [
            _GIT_BIN,
            "ls-tree",
            "-r",
            "--name-only",
            base_ref,
            f"{search_dir}/{package_name}",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        return []

    symbols: list[str] = []
    for filepath in proc.stdout.splitlines():
        if filepath.endswith(".py") and not Path(filepath).name.startswith("_"):
            mod_content = get_git_file_content(base_ref, filepath)
            if mod_content:
                symbols.extend(extract_public_symbols_from_ast(mod_content))

    return sorted(set(symbols))


def extract_planned_symbols(plan_path: Path) -> list[str]:
    """Parse .specs/<feature-id>/plan.md to extract declared classes and functions.

    Returns:
        Sorted declared symbol names from the plan document.

    """
    if not plan_path.is_file():
        return []

    try:
        content = plan_path.read_text(encoding="utf-8")
    except OSError:
        return []

    planned: set[str] = set()

    # Prefer parsing inside python code blocks to avoid false positives in prose
    code_blocks = re.findall(r"```(?:python|py)?\n(.*?)\n```", content, re.DOTALL)
    search_texts = code_blocks or [content]

    for text in search_texts:
        planned.update(_extracted_symbols(text))

    return sorted(planned)


def _extracted_symbols(text: str) -> set[str]:
    """Extract declared public symbol names from one search text.

    Returns:
        Public class, top-level function, and type alias names in the text.

    """
    class_pattern = re.compile(r"\bclass\s+([A-Za-z0-9_]+)")
    # Match only unindented top-level defs so class and protocol methods are skipped
    func_pattern = re.compile(r"^def\s+([A-Za-z0-9_]+)", re.MULTILINE)
    type_pattern = re.compile(r"^type\s+([A-Za-z0-9_]+)\s*=", re.MULTILINE)

    symbols: set[str] = set()
    for pattern in (class_pattern, func_pattern, type_pattern):
        for match in pattern.finditer(text):
            name = match.group(1)
            if not name.startswith("_"):
                symbols.add(name)
    return symbols


def analyze_public_api(
    cwd: Path,
    package_name: str,
    base_ref: str,
    plan_path: Path | None = None,
    search_dir: str = "src",
) -> ApiDiffResult:
    """Analyze public API changes against git base ref and implementation plan.

    Returns:
        Structured analysis result covering symbols and breaking changes.

    """
    package_dir = cwd / search_dir / package_name
    current_symbols = (
        get_package_public_symbols(package_dir) if package_dir.is_dir() else []
    )
    base_symbols = get_base_public_symbols(base_ref, package_name, search_dir)

    added = [s for s in current_symbols if s not in base_symbols]
    removed = [s for s in base_symbols if s not in current_symbols]

    griffe_ok, breaking = run_griffe_check(package_name, base_ref, search_dir)

    planned: list[str] = []
    unplanned: list[str] = []
    missing_planned: list[str] = []

    if plan_path and plan_path.is_file():
        planned = extract_planned_symbols(plan_path)
        unplanned = [s for s in added if s not in planned]
        missing_planned = [s for s in planned if s not in current_symbols]

    return ApiDiffResult(
        package_name=package_name,
        base_ref=base_ref,
        griffe_available=griffe_ok,
        breaking_changes=breaking,
        current_public_symbols=current_symbols,
        base_public_symbols=base_symbols,
        added_symbols=added,
        removed_symbols=removed,
        planned_symbols=planned,
        unplanned_symbols=unplanned,
        missing_planned_symbols=missing_planned,
    )


_BREAKING_HEADER = "⚠️ **Breaking changes detected by Griffe:**"
_NO_BREAKING_LINE = "✓ No breaking changes detected in public API signatures."
_NO_ADDED_LINE = "No new public symbols added."
_NO_PLAN_SECTION_LINE = "✓ All added public symbols were declared in the plan."
_UNPLANNED_HEADER = "⚠️ **Unplanned Public Symbols (Scope Creep Warning):**"
_PLANNED_HINT_LINE = (
    "These symbols appear in the public API but were not declared in the plan:"
)
_MISSING_HEADER = "⚠️ **Missing Planned Symbols:**"
_MISSING_HINT_LINE = (
    "These symbols were specified in the plan but not found in the public API:"
)


def _report_header_lines(result: ApiDiffResult) -> list[str]:
    """Build the report header block.

    Returns:
        Markdown lines describing the package and comparison basis.

    """
    griffe_status = "Yes" if result.griffe_available else "No (fallback to AST)"
    return [
        "## Public API & Griffe Conformance Report",
        "",
        f"- **Package**: `{result.package_name}`",
        f"- **Compared Against**: `{result.base_ref}`",
        f"- **Griffe Check Available**: {griffe_status}",
        "",
    ]


def _breaking_section_lines(result: ApiDiffResult) -> list[str]:
    """Build the breaking-change detection section.

    Returns:
        Markdown lines listing Griffe breaking changes or the all-clear note.

    """
    lines = ["### 1. Breaking Change Detection"]
    if result.breaking_changes:
        lines.extend(
            (
                _BREAKING_HEADER,
                *(f"- {change}" for change in result.breaking_changes),
            )
        )
    else:
        lines.append(_NO_BREAKING_LINE)
    return lines


def _symbol_sections_lines(result: ApiDiffResult) -> list[str]:
    """Build the public-symbol modification sections.

    Returns:
        Markdown lines listing added and removed public symbols.

    """
    lines = ["### 2. Public API Symbol Modifications"]
    if result.added_symbols:
        lines.extend(
            (
                f"**Added Public Symbols ({len(result.added_symbols)}):**",
                *(f"- `{sym}`" for sym in result.added_symbols),
            )
        )
    else:
        lines.append(_NO_ADDED_LINE)

    if result.removed_symbols:
        lines.extend(
            (
                "",
                f"**Removed Public Symbols ({len(result.removed_symbols)}):**",
                *(f"- `{sym}`" for sym in result.removed_symbols),
            )
        )
    return lines


def _plan_sections_lines(result: ApiDiffResult) -> list[str]:
    """Build the implementation-plan conformance section.

    Returns:
        Markdown lines covering unplanned and missing planned symbols.

    """
    if not result.planned_symbols:
        return []

    lines = ["### 3. Implementation Plan Conformance"]
    if result.unplanned_symbols:
        lines.extend(
            (
                _UNPLANNED_HEADER,
                _PLANNED_HINT_LINE,
                *(f"- `{sym}`" for sym in result.unplanned_symbols),
            )
        )
    else:
        lines.append(_NO_PLAN_SECTION_LINE)

    if result.missing_planned_symbols:
        lines.extend(
            (
                "",
                _MISSING_HEADER,
                _MISSING_HINT_LINE,
                *(f"- `{sym}`" for sym in result.missing_planned_symbols),
            )
        )
    lines.append("")
    return lines


_CHECKLIST_PREFIX = "### 4. Developer Confirmation Checklist"
_CHECKLIST_ROWS = (
    _CHECKLIST_PREFIX,
    "- [ ] Maintainer confirms the public API diff matches intended feature scope.",
    "- [ ] Any unplanned public symbols are either intentional or made private.",
    "- [ ] Breaking changes (if any) are documented and justified.",
)


def format_report(result: ApiDiffResult) -> str:
    """Format analysis result into a human- and agent-readable markdown report.

    Returns:
        The markdown report body, lines joined with newlines.

    """
    lines = _report_header_lines(result)
    lines.extend(_breaking_section_lines(result))
    lines.append("")
    lines.extend(_symbol_sections_lines(result))
    lines.append("")
    lines.extend(_plan_sections_lines(result))
    lines.extend(_CHECKLIST_ROWS)
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for API diff and plan verification.

    Returns:
        0 when no breaking or unplanned changes are found, otherwise 1.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Verify public API changes with Griffe against git base ref and"
            " implementation plan."
        )
    )
    parser.add_argument(
        "--package", type=str, help="Package name (default: auto-detected)"
    )
    parser.add_argument(
        "--against",
        type=str,
        help="Base git reference (default: auto-detected main/origin/main)",
    )
    parser.add_argument("--plan", type=Path, help="Path to .specs/<feature-id>/plan.md")
    parser.add_argument(
        "--search", type=str, default="src", help="Search directory (default: src)"
    )
    parser.add_argument("--output", type=Path, help="Write markdown report to file")
    args = parser.parse_args(argv)

    cwd = Path.cwd()
    package_name = args.package or detect_package_name(cwd)
    if not package_name:
        err_console.print(
            "❌ Could not detect package name. Pass --package <name>",
            markup=False,
            soft_wrap=True,
        )
        return 1

    base_ref = args.against or get_default_base_ref()

    result = analyze_public_api(
        cwd=cwd,
        package_name=package_name,
        base_ref=base_ref,
        plan_path=args.plan,
        search_dir=args.search,
    )

    report = format_report(result)
    console.print(report, markup=False, soft_wrap=True)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report + "\n", encoding="utf-8")
        console.print(f"\nSaved report to {args.output}", markup=False, soft_wrap=True)

    if result.breaking_changes or result.unplanned_symbols:
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
