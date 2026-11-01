#!/usr/bin/env python3
"""Archive approved feature specifications from .specs/ into permanent docs/specs/.

Implements the OpenSpec 'Propose -> Apply -> Archive' pattern:
1. Validates that .specs/<feature-id>/review.md declares an Approved verdict.
2. Copies spec.md, plan.md, and review.md into docs/specs/<feature-id>/.
3. Registers the feature in docs/specs/index.md for long-term project memory.
4. Removes the temporary .specs/<feature-id>/ directory.
"""

from __future__ import annotations

import argparse
import re
import shutil
import sys
from pathlib import Path

from rich.console import Console

console = Console(highlight=False)
err_console = Console(stderr=True, highlight=False)

_VERDICT_PATTERN = re.compile(
    r"\*{0,2}Verdict\*{0,2}:\s*Approved(?!\s*\|)", re.IGNORECASE
)
_REGISTRY_HEADER = (
    "# Feature Specifications Registry\n\n"
    "Permanent archive of approved and delivered Spec-Driven Development (SDD)"
    " features.\n\n"
    "| Feature Identifier | Specification | Implementation Plan | Review Audit |\n"
    "| :--- | :--- | :--- | :--- |\n"
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


def _review_rejection_reason(source_dir: Path, *, force: bool) -> str | None:
    """Check the review document for the approval verdict.

    Returns:
        None when archiving may proceed, otherwise the rejection diagnostic.

    """
    if force:
        return None

    review_file = source_dir / "review.md"
    if not review_file.is_file():
        return (
            f"❌ Cannot archive: missing review report at {review_file}."
            " Pass --force to bypass."
        )

    review_content = review_file.read_text(encoding="utf-8")
    if not _VERDICT_PATTERN.search(review_content):
        return (
            "❌ Cannot archive: review.md verdict is not 'Approved'."
            " Pass --force to bypass."
        )
    return None


_SPEC_FILENAMES = ("spec.md", "plan.md", "review.md")


def _copy_spec_files(source_dir: Path, target_dir: Path) -> list[str]:
    """Copy specification artifacts into the archive directory.

    Returns:
        Names of the files that were copied.

    """
    copied_files: list[str] = []
    for filename in _SPEC_FILENAMES:
        src = source_dir / filename
        if src.is_file():
            shutil.copy2(src, target_dir / filename)
            copied_files.append(filename)
    return copied_files


def _register_in_index(index_file: Path, feature_id: str) -> None:
    """Register the feature in the specification registry, once.

    Args:
        index_file: Path of the registry markdown document.
        feature_id: The identifier row to append to the registry table.

    """
    entry_line = (
        f"| `{feature_id}` | [spec.md](./{feature_id}/spec.md) | "
        f"[plan.md](./{feature_id}/plan.md) | [review.md](./{feature_id}/review.md) |\n"
    )

    if not index_file.is_file():
        index_file.write_text(_REGISTRY_HEADER, encoding="utf-8")

    index_content = index_file.read_text(encoding="utf-8")
    if f"`{feature_id}`" in index_content:
        return

    with index_file.open("a", encoding="utf-8") as handle:
        if index_content and not index_content.endswith("\n"):
            handle.write("\n")
        handle.write(entry_line)


def archive_feature(
    feature_id: str,
    specs_root: Path = Path(".specs"),
    docs_root: Path = Path("docs/specs"),
    *,
    force: bool = False,
    keep_temp: bool = False,
) -> int:
    """Archive approved feature specification into permanent documentation.

    Returns:
        0 when the feature was archived, otherwise 1.

    """
    feature_dir = _resolve_feature_dir(specs_root, feature_id)
    if feature_dir is None:
        return 1

    if not feature_dir.is_dir():
        err_console.print(
            f"❌ Feature directory not found: {feature_dir}",
            markup=False,
            soft_wrap=True,
        )
        return 1

    rejection = _review_rejection_reason(feature_dir, force=force)
    if rejection is not None:
        err_console.print(rejection, markup=False, soft_wrap=True)
        return 1

    target_dir = docs_root / feature_id
    target_dir.mkdir(parents=True, exist_ok=True)
    copied_files = _copy_spec_files(feature_dir, target_dir)

    # Register in docs/specs/index.md
    index_file = docs_root / "index.md"
    _register_in_index(index_file, feature_id)

    if not keep_temp:
        shutil.rmtree(feature_dir)

    console.print(
        f"✓ Archived feature '{feature_id}' to {target_dir}"
        f" ({', '.join(copied_files)})",
        markup=False,
        soft_wrap=True,
    )
    console.print(f"✓ Registered in {index_file}", markup=False, soft_wrap=True)
    if not keep_temp:
        console.print(
            f"✓ Cleaned up temporary directory {feature_dir}",
            markup=False,
            soft_wrap=True,
        )

    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint for feature specification archival.

    Returns:
        0 when the feature was archived, otherwise 1.

    """
    parser = argparse.ArgumentParser(
        description=(
            "Archive approved feature specifications from .specs/ into docs/specs/."
        )
    )
    parser.add_argument(
        "feature_id",
        type=str,
        help="Feature identifier (e.g. user-auth, csv-export)",
    )
    parser.add_argument(
        "--specs-dir",
        type=Path,
        default=Path(".specs"),
        help="Path to .specs directory",
    )
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path("docs/specs"),
        help="Path to docs/specs directory",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Bypass requirement for Approved review verdict",
    )
    parser.add_argument(
        "--keep-temp",
        action="store_true",
        help="Keep temporary files in .specs/ after archiving",
    )
    args = parser.parse_args(argv)

    return archive_feature(
        feature_id=args.feature_id,
        specs_root=args.specs_dir,
        docs_root=args.docs_dir,
        force=args.force,
        keep_temp=args.keep_temp,
    )


if __name__ == "__main__":
    sys.exit(main())
