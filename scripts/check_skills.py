#!/usr/bin/env python3
"""Validate structural invariants of agent skills in .agents/skills/.

Ensures each skill adheres to the Zenith skill standard:
- Directory contains SKILL.md.
- Valid YAML frontmatter with `name` matching directory and non-empty `description`.
- Internal links to templates/, references/, examples/, and scripts/
  resolve to actual files.
- Optional/auto-detected documentation coverage in docs/skills/*.md.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from rich.console import Console

console = Console(highlight=False)
error_console = Console(stderr=True, highlight=False)

MIN_DESCRIPTION_LENGTH = 20
MIN_FRONTMATTER_PARTS = 3


def _handle_key_value(
    line: str,
    metadata: dict[str, str],
    current_key: str | None,
    multiline_buf: list[str],
) -> tuple[str, list[str]]:
    """Handle a key: value line in YAML frontmatter.

    Args:
        line: Raw frontmatter line.
        metadata: Accumulated key-value metadata.
        current_key: Key whose value is being accumulated, if any.
        multiline_buf: Buffered lines of the current multiline value.

    Returns:
        The parsed key and the (possibly cleared) multiline buffer.

    """
    if current_key and multiline_buf:
        metadata[current_key] = " ".join(multiline_buf).strip()
    key, val = line.split(":", 1)
    new_key = key.strip()
    val_clean = val.strip().strip("'\"")
    if val_clean in {">", ">-", "|", "|-"}:
        return new_key, []
    if val_clean:
        metadata[new_key] = val_clean
    return new_key, []


def _process_yaml_line(
    line: str,
    metadata: dict[str, str],
    current_key: str | None,
    multiline_buf: list[str],
) -> tuple[str | None, list[str]]:
    """Process a single line of YAML frontmatter.

    Args:
        line: Raw frontmatter line.
        metadata: Accumulated key-value metadata.
        current_key: Key whose value is being accumulated, if any.
        multiline_buf: Buffered lines of the current multiline value.

    Returns:
        The current key (possibly None) and the multiline buffer.

    """
    trimmed = line.strip()
    if not trimmed or trimmed.startswith("#"):
        return current_key, multiline_buf

    if ":" in line and not line.startswith((" ", "\t")):
        return _handle_key_value(line, metadata, current_key, multiline_buf)

    if current_key:
        multiline_buf.append(trimmed)

    return current_key, multiline_buf


def parse_frontmatter(content: str) -> dict[str, str]:
    """Parse simple YAML frontmatter between leading `---` markers.

    Args:
        content: Raw SKILL.md content.

    Returns:
        The parsed frontmatter key-value mapping.

    Raises:
        ValueError: When the frontmatter boundaries are malformed.

    """
    if not content.startswith("---"):
        msg = "Missing leading '---' frontmatter boundary"
        raise ValueError(msg)

    parts = content.split("---", 2)
    if len(parts) < MIN_FRONTMATTER_PARTS:
        msg = "Unclosed frontmatter; expected closing '---'"
        raise ValueError(msg)

    raw_yaml = parts[1]
    metadata: dict[str, str] = {}
    current_key: str | None = None
    multiline_buf: list[str] = []

    for line in raw_yaml.splitlines():
        current_key, multiline_buf = _process_yaml_line(
            line, metadata, current_key, multiline_buf
        )

    if current_key and multiline_buf:
        metadata[current_key] = " ".join(multiline_buf).strip()

    return metadata


def validate_skill(skill_dir: Path) -> list[str]:
    """Validate a single skill directory and report structural violations.

    Args:
        skill_dir: Directory holding the skill definition.

    Returns:
        A list of error messages; empty when the skill is valid.

    """
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.is_file():
        return [f"Missing required SKILL.md in {skill_dir.name}"]

    try:
        content = skill_file.read_text(encoding="utf-8")
    except OSError as exc:
        return [f"Failed to read {skill_file}: {exc}"]

    try:
        frontmatter = parse_frontmatter(content)
    except (ValueError, KeyError, IndexError) as exc:
        return [f"Invalid frontmatter in {skill_dir.name}/SKILL.md: {exc}"]

    # Validate name
    name = frontmatter.get("name")
    if not name:
        errors.append(f"{skill_dir.name}/SKILL.md: missing 'name' in frontmatter")
    elif name != skill_dir.name:
        errors.append(
            f"{skill_dir.name}/SKILL.md: frontmatter name '{name}' does not "
            f"match directory '{skill_dir.name}'"
        )

    # Validate description
    desc = frontmatter.get("description")
    if not desc:
        errors.append(
            f"{skill_dir.name}/SKILL.md: missing 'description' in frontmatter"
        )
    elif len(desc) < MIN_DESCRIPTION_LENGTH:
        errors.append(
            f"{skill_dir.name}/SKILL.md: description is too brief (min 20 chars)"
        )

    # Validate internal file links (e.g. [templates/...](./templates/...))
    link_pattern = re.compile(
        r"\[([^\]]+)\]\((\./(templates|references|examples|scripts)/[^\)]+)\)"
    )
    for match in link_pattern.finditer(content):
        rel_target = match.group(2).lstrip("./")
        target_path = skill_dir / rel_target
        if not target_path.exists():
            errors.append(
                f"{skill_dir.name}/SKILL.md: broken link to missing file: "
                f"{match.group(2)}"
            )

    return errors


def validate_docs_coverage(skill_names: list[str], docs_dir: Path) -> list[str]:
    """Validate that every skill is documented in the documentation directory.

    Args:
        skill_names: Names of all discovered skills.
        docs_dir: Documentation directory to scan.

    Returns:
        A list of error messages; empty when coverage is complete.

    """
    if not docs_dir.is_dir():
        return [f"Docs directory not found: {docs_dir}"]

    doc_files = sorted(docs_dir.glob("*.md"))
    if not doc_files:
        return [f"No markdown documentation files found in {docs_dir}"]

    combined_docs: dict[Path, str] = {}
    for doc_file in doc_files:
        try:
            combined_docs[doc_file] = doc_file.read_text(encoding="utf-8")
        except OSError as exc:
            return [f"Failed to read {doc_file}: {exc}"]

    missing: list[str] = []
    for skill in skill_names:
        pattern = re.compile(rf"\b{re.escape(skill)}\b")
        found = any(pattern.search(text) for text in combined_docs.values())
        if not found:
            missing.append(
                f"Skill '{skill}' is not documented in any file under {docs_dir}"
            )

    return missing


def _validate_all_skills(skill_subdirs: list[Path]) -> bool:
    """Validate all individual skill directories.

    Args:
        skill_subdirs: Directories to validate.

    Returns:
        True when any validation error occurred.

    """
    failed = False
    for s_dir in skill_subdirs:
        errs = validate_skill(s_dir)
        if errs:
            failed = True
            console.print(f"  [red bold]✗[/] {s_dir.name}:")
            for err in errs:
                error_console.print(f"      [red]✗ {err}[/]")
        else:
            console.print(f"  [green]✓[/] {s_dir.name}")
    return failed


def _check_docs_coverage(
    args: argparse.Namespace, skills_dir: Path, skill_subdirs: list[Path]
) -> bool:
    """Check documentation coverage when a docs directory is present.

    Args:
        args: Parsed CLI arguments.
        skills_dir: Resolved skills directory.
        skill_subdirs: Directories to check.

    Returns:
        True when coverage validation failed.

    """
    if args.no_docs_check:
        return False

    docs_dir = args.docs_dir
    if docs_dir is None:
        candidate = skills_dir.parent.parent / "docs" / "skills"
        if candidate.is_dir():
            docs_dir = candidate

    if docs_dir is None:
        return False

    skill_names = [d.name for d in skill_subdirs]
    console.print(
        f"\n[bold cyan]📚 Validating documentation coverage in {docs_dir}...[/]"
    )
    doc_errs = validate_docs_coverage(skill_names, docs_dir)
    if doc_errs:
        for err in doc_errs:
            error_console.print(f"  [red]✗ {err}[/]")
        return True

    console.print(
        f"  [green]✓ All {len(skill_names)} skill(s) documented in {docs_dir.name}/[/]"
    )
    return False


def main(argv: list[str] | None = None) -> int:
    """Run skill-structure validation over the given skills directory.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv`` when None.

    Returns:
        Process exit code: 0 on success, 1 on validation failure.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Validate agent skills structural invariants and documentation coverage."
        )
    )
    parser.add_argument(
        "skills_dir",
        nargs="?",
        type=Path,
        default=Path(".agents/skills"),
        help="Path to .agents/skills directory (default: .agents/skills)",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=None,
        help=(
            "Path to documentation directory to verify all skills are documented "
            "(auto-detected if docs/skills exists)"
        ),
    )
    parser.add_argument(
        "--no-docs-check",
        action="store_true",
        help="Skip checking documentation coverage even if docs directory exists",
    )
    args = parser.parse_args(argv)

    skills_dir = args.skills_dir.resolve()
    if not skills_dir.is_dir():
        error_console.print(f"[bold red]❌ Skills directory not found: {skills_dir}[/]")
        return 1

    skill_subdirs = sorted(
        [d for d in skills_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    )

    if not skill_subdirs:
        console.print(f"[bold yellow]⚠️ No skill directories found in {skills_dir}[/]")
        return 0

    total_skills = len(skill_subdirs)
    console.print(
        f"[bold cyan]🔍 Validating {total_skills} agent skill(s) in {skills_dir}...[/]"
    )
    skills_failed = _validate_all_skills(skill_subdirs)
    docs_failed = _check_docs_coverage(args, skills_dir, skill_subdirs)

    if skills_failed or docs_failed:
        error_console.print("\n[bold red]❌ Skill validation failed with errors.[/]")
        return 1

    console.print(
        f"\n[bold green]✅ All {total_skills} skill(s) satisfied "
        f"structural invariants![/]"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
