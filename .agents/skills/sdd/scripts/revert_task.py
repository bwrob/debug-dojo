#!/usr/bin/env python3
"""Revert a completed SDD task by commit SHA and reset its status in plan.md.

Implements safe rollback of flawed or rejected tasks:
1. Identifies the target task in .specs/<feature-id>/plan.md by recorded SHA or
   selects the most recent completed task.
2. Verifies the commit exists in Git.
3. Executes a clean `git revert --no-edit <sha>`.
4. Resets the task status from [x] back to [ ] in plan.md.
5. Commits the plan update.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess  # ruff: ignore[suspicious-subprocess-import]
import sys
from dataclasses import dataclass
from pathlib import Path

from rich.console import Console

console = Console(highlight=False)
err_console = Console(stderr=True, highlight=False)

# Resolved at import time; falls back to the bare command name so subprocess
# reports the missing executable in its own FileNotFoundError detail.
_GIT_BIN = shutil.which("git") or "git"


@dataclass(frozen=True, slots=True)
class TaskRevertTarget:
    """Metadata for a task targeted for Git reversion."""

    task_title: str
    sha: str
    original_line: str
    reset_line: str


_REVERT_TASK_PATTERN = re.compile(
    r"^([ \t]*-\s*\[x\]\s*(.+?))\s*\(([0-9a-fA-F]{7,40})\)[ \t]*$",
    re.MULTILINE,
)


def find_revertable_tasks(plan_content: str) -> list[TaskRevertTarget]:
    """Parse plan.md content to find all completed tasks with recorded commit SHAs.

    Returns:
        All completed tasks that record a commit SHA, ordered by document position.

    """
    # Matches: - [x] **Task 1: Title** (a1b2c3d) or - [x] Task 1: Title (a1b2c3d)
    return [
        _target_from_match(match)
        for match in _REVERT_TASK_PATTERN.finditer(plan_content)
    ]


def _target_from_match(match: re.Match[str]) -> TaskRevertTarget:
    """Build one revert target from a completed-task pattern match.

    Returns:
        Target data holding the task title, sha, original, and reset lines.

    """
    full_line = match.group(0)
    prefix_and_title = match.group(1)
    task_title = match.group(2).strip()
    sha = match.group(3).strip()

    # Build reset line: replace [x] with [ ] and strip the (sha) suffix
    reset_line = re.sub(r"-\s*\[x\]", "- [ ]", prefix_and_title)

    return TaskRevertTarget(
        task_title=task_title,
        sha=sha,
        original_line=full_line,
        reset_line=reset_line,
    )


def _resolve_feature_dir(specs_root: Path, feature_id: str) -> Path | None:
    """Resolve the feature directory path and guard against traversal.

    Returns:
        Resolved feature directory, or None when invalid with the diagnostic
        already logged to stderr.

    """
    try:
        resolved_specs = specs_root.resolve()
        resolved_source = (specs_root / feature_id).resolve()
    except (ValueError, RuntimeError):
        err_console.print(
            f"❌ Invalid path for feature directory: {specs_root / feature_id}",
            markup=False,
            soft_wrap=True,
        )
        return None

    inside = (
        resolved_source.is_relative_to(resolved_specs)
        and resolved_source != resolved_specs
    )
    if inside:
        return resolved_source

    err_console.print(
        f"❌ Security violation: invalid feature identifier '{feature_id}'"
        f" traverses outside {specs_root}",
        markup=False,
        soft_wrap=True,
    )
    return None


def _read_plan_file(plan_file: Path) -> str | None:
    """Read the implementation plan content.

    Returns:
        Plan file content, or None when it is missing or unreadable.

    """
    if not plan_file.is_file():
        err_console.print(
            f"❌ Implementation plan not found: {plan_file}",
            markup=False,
            soft_wrap=True,
        )
        return None

    try:
        return plan_file.read_text(encoding="utf-8")
    except OSError as exc:
        err_console.print(
            f"❌ Failed to read plan file: {exc}", markup=False, soft_wrap=True
        )
        return None


def _matching_target(
    targets: list[TaskRevertTarget],
    target_sha: str,
) -> TaskRevertTarget | None:
    """Match a task by its recorded commit SHA, allowing shared prefixes.

    Returns:
        The first task whose sha shares a prefix with the requested one.

    """
    clean_sha = target_sha.strip().lower()
    for target in targets:
        recorded = target.sha.lower()
        if recorded.startswith(clean_sha) or clean_sha.startswith(recorded):
            return target
    return None


def _verify_commit(sha: str, repo_root: Path) -> bool:
    """Verify the commit exists in the local Git history.

    Returns:
        True when the commit resolves, False after logging the failure.

    """
    proc = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        [_GIT_BIN, "rev-parse", "--verify", f"{sha}^0"],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )
    if proc.returncode == 0:
        return True

    err_console.print(
        f"❌ Commit '{sha}' does not exist in local Git history.",
        markup=False,
        soft_wrap=True,
    )
    return False


def _perform_revert(target: TaskRevertTarget, repo_root: Path) -> bool:
    """Execute the git revert, aborting it on conflict.

    Returns:
        True when the revert commit was created cleanly.

    """
    revert_proc = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        [_GIT_BIN, "revert", "--no-edit", target.sha],
        capture_output=True,
        text=True,
        check=False,
        cwd=repo_root,
    )
    if revert_proc.returncode == 0:
        return True

    subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        [_GIT_BIN, "revert", "--abort"], capture_output=True, check=False, cwd=repo_root
    )
    detail = revert_proc.stderr.strip() or revert_proc.stdout.strip()
    err_console.print(
        f"❌ Failed to revert commit {target.sha} due to conflict.\n"
        "   Revert aborted to preserve clean repository state.\n"
        f"   Details: {detail}",
        markup=False,
        soft_wrap=True,
    )
    return False


def _reset_plan_status(
    plan_file: Path,
    plan_content: str,
    target: TaskRevertTarget,
    repo_root: Path,
) -> bool:
    """Reset the task status in plan.md and commit the change.

    Returns:
        True when the plan was updated and committed.

    """
    updated_content = plan_content.replace(
        target.original_line,
        target.reset_line,
        1,
    )
    try:
        plan_file.write_text(updated_content, encoding="utf-8")
    except OSError as exc:
        err_console.print(
            f"❌ Failed to write updated plan: {exc}", markup=False, soft_wrap=True
        )
        return False

    # Commit plan reset
    subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        [_GIT_BIN, "add", str(plan_file)], check=False, cwd=repo_root
    )
    subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        [
            _GIT_BIN,
            "commit",
            "-m",
            f"docs(plan): reset '{target.task_title}' after revert of {target.sha}",
        ],
        capture_output=True,
        check=False,
        cwd=repo_root,
    )
    return True


def _revert_selected_task(
    target: TaskRevertTarget,
    plan_file: Path,
    plan_content: str,
    repo_root: Path,
    *,
    dry_run: bool,
) -> int:
    """Revert one selected task commit and reset its plan status.

    Returns:
        0 on success, 1 when the commit is missing or the revert or plan reset fails.

    """
    if not _verify_commit(target.sha, repo_root):
        return 1

    if dry_run:
        console.print(
            f"[Dry Run] Would revert commit '{target.sha}' for task"
            f" '{target.task_title}'.",
            markup=False,
            soft_wrap=True,
        )
        console.print(
            f"[Dry Run] Would update {plan_file} to reset task status to pending: [ ].",
            markup=False,
            soft_wrap=True,
        )
        return 0

    if not _perform_revert(target, repo_root):
        return 1

    if not _reset_plan_status(plan_file, plan_content, target, repo_root):
        return 1

    console.print(
        f"✓ Successfully reverted commit {target.sha} for task '{target.task_title}'",
        markup=False,
        soft_wrap=True,
    )
    console.print(
        f"✓ Reset task status to pending in {plan_file}",
        markup=False,
        soft_wrap=True,
    )
    return 0


def revert_task(
    feature_id: str,
    target_sha: str | None = None,
    specs_root: Path = Path(".specs"),
    repo_root: Path | None = None,
    *,
    dry_run: bool = False,
) -> int:
    """Revert a task commit and reset its status in plan.md.

    Returns:
        0 when the revert (or dry run inspection) succeeded, otherwise 1.

    """
    try:
        feature_dir = _resolve_feature_dir(specs_root, feature_id)
    except (ValueError, RuntimeError):
        feature_dir = None

    if feature_dir is None:
        return 1

    effective_repo = repo_root.resolve() if repo_root is not None else None
    if effective_repo is None:
        effective_repo = specs_root.parent

    plan_file = feature_dir / "plan.md"
    plan_content = _read_plan_file(plan_file)
    if plan_content is None:
        return 1

    targets = find_revertable_tasks(plan_content)
    if not targets:
        err_console.print(
            f"❌ No completed tasks with recorded commit SHAs found in {plan_file}.\n"
            "   Ensure completed tasks are recorded as '- [x] Task Title (<sha>)'.",
            markup=False,
            soft_wrap=True,
        )
        return 1

    selected_target = (
        targets[-1] if target_sha is None else _matching_target(targets, target_sha)
    )
    if selected_target is None:
        err_console.print(
            f"❌ No task with recorded commit SHA matching '{target_sha}'"
            f" found in {plan_file}.",
            markup=False,
            soft_wrap=True,
        )
        return 1

    return _revert_selected_task(
        selected_target,
        plan_file,
        plan_content,
        effective_repo,
        dry_run=dry_run,
    )


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for SDD task revert.

    Returns:
        The revert task exit code, 0 on success or 1 on failure.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Revert a completed SDD task commit and reset its status in plan.md."
        )
    )
    parser.add_argument(
        "feature_id", type=str, help="Feature identifier (e.g. user-auth)"
    )
    parser.add_argument(
        "sha",
        nargs="?",
        default=None,
        help="Optional commit SHA to revert (defaults to last completed task)",
    )
    parser.add_argument(
        "--specs-dir",
        type=Path,
        default=Path(".specs"),
        help="Path to .specs directory",
    )
    parser.add_argument(
        "--repo-dir", type=Path, default=None, help="Path to Git repository root"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Inspect revert target without executing git revert",
    )
    args = parser.parse_args(argv)

    return revert_task(
        args.feature_id,
        target_sha=args.sha,
        specs_root=args.specs_dir,
        repo_root=args.repo_dir,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    sys.exit(main())
