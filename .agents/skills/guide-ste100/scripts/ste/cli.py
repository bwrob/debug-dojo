"""Command-line interface for the modular STE linter."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

from ste.engine import lint_text
from ste.fixer import fix_text
from ste.model import Finding, Severity
from ste.reporter import format_json, format_text
from ste.rules.registry import ALL_RULES, get_rules

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence
    from typing import TextIO

    from ste.rules.base import Rule

console = Console(highlight=False, markup=False)
error_console = Console(stderr=True, highlight=False, markup=False)

SKIPPED_DIRS = frozenset[str](
    {
        ".git",
        ".venv",
        ".temp",
        ".ruff_cache",
        ".pytest_cache",
        ".rumdl_cache",
        "node_modules",
        "site",
        "dist",
        "__pycache__",
    }
)
DANGLING_EXPECTED_COUNT = 4
EXPECTED_SEMICOLON_LINE = 4
SELFTEST_EXPECTED_RULES = (
    "semicolon",
    "phrasal-verb",
    "nominalization",
    "marketing-adjective",
    "passive-voice",
    "present-perfect",
)


def build_parser() -> argparse.ArgumentParser:
    """Construct the command-line argument parser.

    Returns
    -------
    argparse.ArgumentParser
        Parser configured for the `ste-lint` command.

    """
    parser = argparse.ArgumentParser(
        prog="ste-lint",
        description=(
            "Deterministic structural linter for ASD-STE100 "
            "Simplified Technical English.\n"
            "Checks structural rules in Markdown documents and agent output."
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Markdown file(s) to lint. If omitted, reads from standard input.",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help=(
            "Automatically fix common mechanical violations (contractions, Latin "
            "abbreviations, unapproved phrases) in-place."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output findings in structured JSON format.",
    )
    parser.add_argument(
        "--baseline",
        type=int,
        default=0,
        help=(
            "Tolerate up to N hard violations before exiting with non-zero status "
            "(default: 0)."
        ),
    )
    parser.add_argument(
        "--disable",
        type=str,
        default="",
        help=(
            "Comma-separated list of rule IDs to disable "
            "(e.g. 'passive-voice,present-perfect')."
        ),
    )
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="List all available rules and exit.",
    )
    parser.add_argument(
        "--selftest",
        action="store_true",
        help="Execute internal verification test suite and exit.",
    )
    return parser


def run_selftest() -> int:
    """Run the internal verification suite validating rules against test cases.

    Returns
    -------
    int
        Exit code, always 0: any failure raises `AssertionError` instead.

    """
    _selftest_structural_rules()
    _selftest_hedges_protected()
    _selftest_code_blocks_skipped()
    _selftest_dangling_conjunctions()
    _selftest_list_continuations()
    _selftest_long_sentences()
    _selftest_table_cells()
    _selftest_synonym_rotation()
    _selftest_containers()
    _selftest_inline_suppressions()
    console.print("selftest OK: all 13 test suites passed successfully.")
    return 0


def _selftest_structural_rules() -> None:
    """Fail unless every expected hard rule fires on the structural sample.

    Raises
    ------
    AssertionError
        When an expected rule is missing from the findings.

    """
    bad = (
        "The panel is removed; spin up the job. "
        "Perform an analysis of the seamless log. "
        "We have received the report."
    )
    rule_ids = {finding.rule for finding in lint_text(bad).findings}
    for expected in SELFTEST_EXPECTED_RULES:
        if expected not in rule_ids:
            msg = f"Expected rule {expected} in findings: {rule_ids}"
            raise AssertionError(msg)


def _selftest_hedges_protected() -> None:
    """Fail unless hedged sentences stay unflagged.

    Raises
    ------
    AssertionError
        When hedges or modality are flagged.

    """
    hedges = (
        "The request may have failed. It could be a timeout. "
        "The disk might have filled."
    )
    findings = lint_text(hedges).findings
    if findings:
        msg = f"Hedges flagged: {findings}"
        raise AssertionError(msg)


def _selftest_code_blocks_skipped() -> None:
    """Fail unless fenced code block content stays unflagged.

    Raises
    ------
    AssertionError
        When fence content is linted.

    """
    fenced = "```python\nx = a; y = b\n```"
    tilted = "~~~text\n- code and\n~~~"
    for text, what in ((fenced, "code"), (tilted, "tilde")):
        findings = lint_text(text).findings
        if findings:
            msg = f"{what} block content flagging: {findings}"
            raise AssertionError(msg)


def _selftest_dangling_conjunctions() -> None:
    """Fail unless dangling conjunctions are located as expected.

    Raises
    ------
    AssertionError
        When the count, the lines, or the severity diverges.

    """
    list_text = (
        "- Confirm the target and\n"
        "* Record the result OR  \n"
        "+ Close the panel\n"
        "1. Start the task and\n"
        "2) Stop the task OR"
    )
    dangling = [
        finding
        for finding in lint_text(list_text).findings
        if finding.rule == "dangling-conjunction"
    ]
    if len(dangling) != DANGLING_EXPECTED_COUNT:
        msg = (
            f"Expected {DANGLING_EXPECTED_COUNT} dangling findings, got {len(dangling)}"
        )
        raise AssertionError(msg)
    if [item.line for item in dangling] != [1, 2, 4, 5]:
        found = [item.line for item in dangling]
        msg = f"Expected dangling lines [1, 2, 4, 5], got {found}"
        raise AssertionError(msg)
    if any(item.severity != Severity.HARD for item in dangling):
        msg = f"Dangling findings not all hard: {dangling}"
        raise AssertionError(msg)


def _selftest_list_continuations() -> None:
    """Fail when continuation lines or inline code spans get flagged.

    Raises
    ------
    AssertionError
        When a continued item or an inline code span is flagged.

    """
    continuation = "  - Confirm the target and\n    record the result."
    inline_code = "- Use `and` as a label\n- Combine `left` and `right`"
    for text, what in ((continuation, "continuation"), (inline_code, "inline code")):
        findings = [
            finding
            for finding in lint_text(text).findings
            if finding.rule == "dangling-conjunction"
        ]
        if findings:
            msg = f"dangling-conjunction flagged in {what}: {findings}"
            raise AssertionError(msg)


def _selftest_long_sentences() -> None:
    """Fail unless a 30-word sentence is flagged as long.

    Raises
    ------
    AssertionError
        When the long sentence rule stays silent.

    """
    long_prose = ("word " * 30).strip() + "."
    findings = lint_text(long_prose).findings
    if not any(finding.rule == "long-sentence" for finding in findings):
        msg = "long-sentence not flagged: 30-word prose"
        raise AssertionError(msg)


def _selftest_table_cells() -> None:
    """Fail unless table cells are linted independently of one another.

    Raises
    ------
    AssertionError
        When a short cell is flagged or a long cell stays silent.

    """
    short_cell = " ".join(f"term{i}" for i in range(1, 25)) + "."
    long_cell = " ".join(f"term{i}" for i in range(1, 27)) + "."
    short_table = f"| Label | Detail |\n| --- | --- |\n| Clear | {short_cell} |"
    long_table = f"| Label | Detail |\n| --- | --- |\n| Clear | {long_cell} |"
    if any(
        finding.rule == "long-sentence" for finding in lint_text(short_table).findings
    ):
        msg = "long-sentence flagged inside a short table cell"
        raise AssertionError(msg)
    long_findings = lint_text(long_table).findings
    if not any(finding.rule == "long-sentence" for finding in long_findings):
        msg = "long-sentence not flagged inside a long table cell"
        raise AssertionError(msg)


def _selftest_synonym_rotation() -> None:
    """Fail unless the rotating synonyms in the sample are flagged once.

    Raises
    ------
    AssertionError
        When the count or the message text diverges.

    """
    text = "Check the config file. Then verify the output. Verify twice."
    findings = [
        finding
        for finding in lint_text(text).findings
        if finding.rule == "synonym-rotation"
    ]
    if len(findings) != 1:
        msg = f"Expected 1 synonym finding, got {len(findings)}: {findings}"
        raise AssertionError(msg)
    if "'verify' and 'check'" not in findings[0].message:
        msg = f"synonym message wrong: {findings[0].message}"
        raise AssertionError(msg)


def _selftest_containers() -> None:
    """Fail unless the alert and the frontmatter description are linted.

    Raises
    ------
    AssertionError
        When the nominalization rule stays silent in either container.

    """
    alert = "> [!NOTE]\n> Perform an analysis of the log."
    frontmatter = (
        "---\n"
        "name: my-skill\n"
        "description: Perform an analysis of state.\n"
        "---\n"
        "# Heading\n"
        "Body content."
    )
    for text, what in ((alert, "alert"), (frontmatter, "frontmatter")):
        findings = lint_text(text).findings
        if not any(finding.rule == "nominalization" for finding in findings):
            msg = f"nominalization not flagged in {what}: {findings}"
            raise AssertionError(msg)


def _selftest_inline_suppressions() -> None:
    """Fail unless a disabled rule stays silent and re-enables afterwards.

    Raises
    ------
    AssertionError
        When the count or the line of semicolon findings diverges.

    """
    suppressed = (
        "<!-- ste-lint-disable semicolon -->\n"
        "This has; a semicolon.\n"
        "<!-- ste-lint-enable semicolon -->\n"
        "This has; another semicolon."
    )
    findings = [
        finding
        for finding in lint_text(suppressed).findings
        if finding.rule == "semicolon"
    ]
    if len(findings) != 1:
        found = len(findings)
        msg = f"Expected 1 suppressed finding, got {found}: {findings}"
        raise AssertionError(msg)
    if findings[0].line != EXPECTED_SEMICOLON_LINE:
        msg = f"Expected line {EXPECTED_SEMICOLON_LINE}, got {findings[0].line}"
        raise AssertionError(msg)


def _list_rules() -> int:
    """Print every registered rule with its severity and description.

    Returns
    -------
    int
        Exit code, always 0.

    """
    for rule in ALL_RULES:
        console.print(
            f"- {rule.id} [{rule.severity.value}]: {rule.description}",
            soft_wrap=True,
        )
    return 0


def _markdown_in(directory: Path) -> Iterator[Path]:
    """Yield Markdown files under `directory`, skipping noise directories.

    Parameters
    ----------
    directory : Path
        Root to walk for Markdown files.

    Yields
    ------
    Path
        Sorted Markdown file paths in traversal order.

    """
    for root, dirs, files in directory.walk(follow_symlinks=True):
        dirs[:] = [name for name in dirs if name not in SKIPPED_DIRS]
        if any(part in SKIPPED_DIRS for part in root.parts):
            continue
        yield from (root / name for name in sorted(files) if name.endswith(".md"))


def _resolve_target_files(entries: Sequence[Path]) -> list[Path] | None:
    """Expand file and directory arguments into Markdown file targets.

    Parameters
    ----------
    entries : Sequence[Path]
        File and directory arguments given on the command line.

    Returns
    -------
    list[Path] | None
        Markdown targets, or `None` when an entry is neither file nor dir.

    """
    target_files: list[Path] = []
    for entry in entries:
        if entry.is_dir():
            target_files.extend(_markdown_in(entry))
        elif entry.is_file():
            target_files.append(entry)
        else:
            error_console.print(
                f"Error reading {entry}: file or directory not found",
                soft_wrap=True,
            )
            return None
    return target_files


def _fix_target_files(target_files: Sequence[Path]) -> int:
    """Apply in-place fixes to every target and report the totals.

    Parameters
    ----------
    target_files : Sequence[Path]
        Markdown files to rewrite in place.

    Returns
    -------
    int
        Exit code: 0 on success, 1 on an unreadable or unwritable file.

    """
    total_fixed = 0
    for file_path in target_files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            error_console.print(f"Error reading {file_path}: {exc}", soft_wrap=True)
            return 1
        fixed, count = fix_text(content)
        if count == 0:
            continue
        try:
            file_path.write_text(fixed, encoding="utf-8")
        except OSError as exc:
            error_console.print(f"Error writing {file_path}: {exc}", soft_wrap=True)
            return 1
        total_fixed += count
        console.print(f"Fixed {count} violation(s) in {file_path}", soft_wrap=True)
    console.print(f"Total violations fixed: {total_fixed}", soft_wrap=True)
    return 0


def _lint_target_files(
    target_files: Sequence[Path],
    rules: Sequence[Rule] | None,
) -> tuple[list[Finding], int] | None:
    """Lint every target and merge the results into one aggregate.

    Parameters
    ----------
    target_files : Sequence[Path]
        Markdown files to lint.
    rules : Sequence[Rule] | None
        Active rules; `None` selects every rule.

    Returns
    -------
    tuple[list[Finding], int] | None
        Merged findings and word total, or `None` when a file cannot
        be read.

    """
    findings: list[Finding] = []
    words_total = 0
    for file_path in target_files:
        try:
            content = file_path.read_text(encoding="utf-8")
        except OSError as exc:
            error_console.print(f"Error reading {file_path}: {exc}", soft_wrap=True)
            return None
        result = lint_text(content, filename=str(file_path), rules=rules)
        findings.extend(result.findings)
        words_total += result.words_total
    return findings, words_total


def _report(
    findings: Sequence[Finding],
    words_total: int,
    baseline: int,
    files_count: int,
    *,
    as_json: bool,
) -> int:
    """Print the aggregated results and return the process exit code.

    Parameters
    ----------
    findings : Sequence[Finding]
        All findings of the run, whatever their source.
    words_total : int
        Total prose words across the run.
    baseline : int
        Hard violations tolerated before a non-zero exit.
    files_count : int
        Number of files in the run, counting stdin as one.
    as_json : bool
        Choose JSON output over the standard text format.

    Returns
    -------
    int
        0 when the baseline absorbs every hard violation, else 1.

    """
    findings = sorted(findings, key=lambda finding: finding.sort_key)
    hard_count = sum(1 for finding in findings if finding.severity == Severity.HARD)
    formatter = format_json if as_json else format_text
    output = formatter(
        findings,
        words_total,
        hard_count,
        baseline=baseline,
        files_count=files_count,
    )
    console.print(output, soft_wrap=True)
    return 1 if hard_count > baseline else 0


def _run_file_mode(args: argparse.Namespace, rules: Sequence[Rule] | None) -> int:
    """Resolve targets, then fix or lint them, and return the exit code.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line options.
    rules : Sequence[Rule] | None
        Active rules; `None` selects every rule.

    Returns
    -------
    int
        Exit code for the file-based run.

    """
    targets = _resolve_target_files(args.files)
    if targets is None:
        return 1
    if args.fix:
        return _fix_target_files(targets)
    batch = _lint_target_files(targets, rules)
    if batch is None:
        return 1
    findings, words_total = batch
    return _report(
        findings,
        words_total,
        args.baseline,
        files_count=len(targets),
        as_json=args.json,
    )


def main(argv: list[str] | None = None, stdin: TextIO = sys.stdin) -> int:
    """Parse the arguments and dispatch the linter flow.

    Parameters
    ----------
    argv : list[str] | None
        Arguments to parse; defaults to the process arguments.
    stdin : TextIO
        Stream read when no file arguments are given.

    Returns
    -------
    int
        Process exit code: 0 on success, non-zero on failure or excess
        hard violations.

    """
    args = build_parser().parse_args(argv)

    if args.selftest:
        return run_selftest()

    if args.list_rules:
        return _list_rules()

    disabled = [item.strip() for item in args.disable.split(",") if item.strip()]
    rules = get_rules(disabled=disabled)

    if args.files:
        return _run_file_mode(args, rules)

    content = stdin.read()
    if args.fix:
        fixed, _ = fix_text(content)
        sys.stdout.write(fixed)
        return 0
    result = lint_text(content, filename="<stdin>", rules=rules)
    return _report(
        result.findings,
        result.words_total,
        args.baseline,
        files_count=1,
        as_json=args.json,
    )


if __name__ == "__main__":
    sys.exit(main())
