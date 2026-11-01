#!/usr/bin/env python3
"""Pre-flight verification for built wheel distributions.

Installs the built wheel in an isolated, temporary virtual environment and
verifies that all package modules and console script entry points can be
imported cleanly without missing runtime dependencies.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import venv
import zipfile
from pathlib import Path
from typing import TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from collections.abc import Sequence

console = Console(highlight=False)
error_console = Console(stderr=True, highlight=False)

CAPTURE_KWARGS = {
    "capture_output": True,
    "text": True,
    "encoding": "utf-8",
}

TEST_PACKAGES = [
    "hypothesis>=6.125.0",
    "pytest>=9.0.0",
    "pytest-cov>=7.0.0",
    "pytest-randomly>=3.16.0",
    "pytest-sugar>=1.1.1",
    "pytest-xdist>=3.8.0",
    "syrupy>=6.1.0",
]

GUIDANCE_TEXT = (
    "\n💡 Diagnostic guidance:\n"
    "  - Missing dependencies? Check [project.dependencies] in "
    "pyproject.toml.\n"
    "  - For packaging workflows, see .agents/skills/tool-uv/SKILL.md.\n"
    "  - For architecture layer contracts, see .agents/skills/tool-tach/"
    "SKILL.md.\n"
)

ISOLATED_CHECK_CODE = """
import importlib
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

modules = [m for m in sys.argv[1].split(",") if m]
entry_points = [e for e in sys.argv[2].split(",") if e]

failed = False

print(f"Testing {len(modules)} module(s)...")
for mod in modules:
    try:
        importlib.import_module(mod)
        print(f"  ✓ {mod}")
    except Exception as exc:
        print(f"  ✗ {mod}: {exc}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        failed = True

if entry_points:
    print(f"Testing {len(entry_points)} console script entry point(s)...")
    for ep_str in entry_points:
        try:
            name, target = ep_str.split("=", 1)
            name = name.strip()
            target = target.strip()
            mod_name, func_name = target.split(":", 1)
            mod = importlib.import_module(mod_name)
            func = getattr(mod, func_name)
            if not callable(func):
                raise TypeError(f"Target '{target}' is not callable")
            print(f"  ✓ {name} -> {target}")
        except Exception as exc:
            print(f"  ✗ {ep_str}: {exc}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            failed = True

if failed:
    sys.exit(1)
"""


def _collect_wheels(dist_dir: Path) -> list[Path]:
    """Collect wheels in the directory sorted newest first.

    Args:
        dist_dir: Directory to search for ``*.whl`` files.

    Returns:
        Wheels sorted by modification time, newest first.

    """
    return sorted(
        dist_dir.glob("*.whl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )


def find_wheel(dist_dir: Path, explicit_path: Path | None) -> Path:
    """Locate the wheel file to verify, building it if none exists.

    Args:
        dist_dir: Directory searched for ``*.whl`` files.
        explicit_path: Explicit wheel path; bypasses directory search when set.

    Returns:
        Path to the newest available wheel file.

    Raises:
        FileNotFoundError: If the explicit path does not exist or no wheel is
            present in the directory after the build attempt.

    """
    if explicit_path is not None:
        if not explicit_path.is_file():
            msg = f"Specified wheel does not exist: {explicit_path}"
            raise FileNotFoundError(msg)
        return explicit_path

    dist_dir.mkdir(parents=True, exist_ok=True)
    wheels = _collect_wheels(dist_dir)
    if not wheels:
        console.print("📦 No wheel found in dist/. Building with `uv build --wheel`...")
        # Repo-owned tooling on repo-controlled paths; no untrusted input.
        subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
            [str(shutil.which("uv")), "build", "--wheel"],
            check=True,
        )
        wheels = _collect_wheels(dist_dir)
        if not wheels:
            msg = f"No .whl files found in {dist_dir} after build."
            raise FileNotFoundError(msg)

    return wheels[0]


def _find_dist_info(namelist: list[str]) -> str:
    """Find the ``.dist-info`` directory prefix inside the wheel archive.

    Args:
        namelist: Zip archive member names.

    Returns:
        The dist-info directory name, or an empty string when absent.

    """
    return next(
        (
            name.split("/")[0]
            for name in namelist
            if name.endswith(".dist-info/")
            or "/.dist-info/" in name
            or (name.split("/")[0].endswith(".dist-info") and "/" in name)
        ),
        "",
    )


def _read_dist_name(zf: zipfile.ZipFile, namelist: list[str], dist_info: str) -> str:
    """Extract the distribution name from wheel METADATA when available.

    Args:
        zf: Open wheel archive.
        namelist: Zip archive member names.
        dist_info: The dist-info directory prefix, or an empty string.

    Returns:
        The distribution name, or an empty string when unavailable.

    """
    member = f"{dist_info}/METADATA" if dist_info else ""
    if not member or member not in namelist:
        return ""
    metadata_content = zf.read(member).decode("utf-8", errors="replace")
    for line in metadata_content.splitlines():
        if line.startswith("Name:"):
            return line.split(":", 1)[1].strip()
    return ""


def _discover_modules(namelist: list[str]) -> list[str]:
    """Discover Python module dotted names in the wheel archive.

    Args:
        namelist: Zip archive member names.

    Returns:
        Module dotted names sorted so parent packages import first.

    """
    modules: set[str] = set()
    for name in namelist:
        if not name.endswith(".py"):
            continue
        parts = name.split("/")
        # Skip .dist-info and .data directories
        if parts[0].endswith((".dist-info", ".data")):
            continue
        if parts[-1] == "__init__.py":
            mod_parts = parts[:-1]
        else:
            mod_parts = [*parts[:-1], parts[-1][:-3]]
        if mod_parts:
            modules.add(".".join(mod_parts))

    return sorted(modules, key=lambda module: (module.count("."), module))


def _parse_console_scripts(entry_points_content: str) -> list[str]:
    """Extract console script entry point definitions from ``entry_points.txt``.

    Args:
        entry_points_content: Raw content of ``entry_points.txt``.

    Returns:
        Entry point definition lines under ``[console_scripts]``.

    """
    entry_points: list[str] = []
    in_console_scripts = False
    for line in entry_points_content.splitlines():
        stripped = line.strip()
        if stripped == "[console_scripts]":
            in_console_scripts = True
        elif stripped.startswith("["):
            in_console_scripts = False
        elif (
            in_console_scripts
            and stripped
            and not stripped.startswith("#")
            and "=" in stripped
        ):
            entry_points.append(stripped)

    return entry_points


def _discover_entry_points(
    zf: zipfile.ZipFile, namelist: list[str], dist_info: str
) -> list[str]:
    """Extract console script entry point definitions from the wheel archive.

    Args:
        zf: Open wheel archive.
        namelist: Zip archive member names.
        dist_info: The dist-info directory prefix, or an empty string.

    Returns:
        Entry point definition lines; empty when the archive has none.

    """
    member = f"{dist_info}/entry_points.txt" if dist_info else ""
    if not member or member not in namelist:
        return []
    entry_points_content = zf.read(member).decode("utf-8", errors="replace")
    return _parse_console_scripts(entry_points_content)


def inspect_wheel(wheel_path: Path) -> tuple[str, list[str], list[str]]:
    """Inspect the wheel archive for distribution name, modules, and scripts.

    Args:
        wheel_path: Path to the ``.whl`` archive.

    Returns:
        A ``(distribution_name, modules, entry_points)`` tuple.

    """
    with zipfile.ZipFile(wheel_path) as zf:
        namelist = zf.namelist()
        dist_info = _find_dist_info(namelist)

        dist_name = _read_dist_name(zf, namelist, dist_info)
        if not dist_name:
            dist_name = wheel_path.name.split("-")[0].replace("_", "-")

        modules = _discover_modules(namelist)
        entry_points = _discover_entry_points(zf, namelist, dist_info)

    return dist_name, modules, entry_points


def create_isolated_environment(tmp_dir: Path) -> Path:
    """Create a temporary virtual environment using uv or standard venv.

    Args:
        tmp_dir: Base directory for the ``.venv``.

    Returns:
        Path to the venv's Python interpreter.

    Raises:
        FileNotFoundError: If the expected venv interpreter is absent.

    """
    venv_dir = tmp_dir / ".venv"
    uv_tool = shutil.which("uv")
    if uv_tool is not None:
        # Repo-owned tooling on repo-controlled paths; no untrusted input.
        subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
            [uv_tool, "venv", "--no-project", str(venv_dir)],
            check=True,
            **CAPTURE_KWARGS,
        )
    else:
        venv.create(venv_dir, with_pip=True)

    if sys.platform == "win32":
        python_exe = venv_dir / "Scripts" / "python.exe"
    else:
        python_exe = venv_dir / "bin" / "python"

    if not python_exe.exists():
        msg = f"Python interpreter not found in venv at {python_exe}"
        raise FileNotFoundError(msg)

    return python_exe


def install_wheel_in_env(python_exe: Path, wheel_path: Path) -> None:
    """Install the wheel and its declared dependencies into the environment.

    Args:
        python_exe: Python interpreter of the isolated venv.
        wheel_path: Wheel archive to install.

    """
    uv_tool = shutil.which("uv")
    if uv_tool is not None:
        # Repo-owned tooling on repo-controlled paths; no untrusted input.
        subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
            [
                uv_tool,
                "pip",
                "install",
                "--python",
                str(python_exe),
                "--no-config",
                str(wheel_path.resolve()),
            ],
            check=True,
            **CAPTURE_KWARGS,
        )
    else:
        # Isolated venv interpreter driven with fixed repo-owned arguments.
        subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
            [str(python_exe), "-m", "pip", "install", str(wheel_path.resolve())],
            check=True,
            **CAPTURE_KWARGS,
        )


def verify_in_venv(
    python_exe: Path,
    modules: Sequence[str],
    entry_points: Sequence[str],
    cwd: Path,
) -> None:
    """Run module import and entry-point checks inside the isolated venv.

    Args:
        python_exe: Python interpreter of the isolated venv.
        modules: Module dotted names to import.
        entry_points: Console script specifications to verify.
        cwd: Target working directory for the check subprocess.

    Raises:
        RuntimeError: If the check subprocess exits non-zero.

    """
    # Hermetic interpreter running repo-owned check code; no untrusted input.
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        [
            str(python_exe),
            "-X",
            "utf8",
            "-I",
            "-c",
            ISOLATED_CHECK_CODE,
            ",".join(modules),
            ",".join(entry_points),
        ],
        cwd=cwd,
        check=False,
        **CAPTURE_KWARGS,
    )
    if result.stdout:
        console.print(result.stdout.strip(), markup=False, soft_wrap=True)
    if result.returncode == 0:
        return
    if result.stderr:
        error_console.print(result.stderr.strip(), markup=False, soft_wrap=True)
    msg = f"Wheel verification failed with exit code {result.returncode}"
    raise RuntimeError(msg)


def _install_test_dependencies(python_exe: Path) -> None:
    """Install the pytest toolchain into the isolated environment.

    Args:
        python_exe: Python interpreter of the isolated venv.

    """
    uv_tool = shutil.which("uv")
    if uv_tool is not None:
        # Repo-owned tooling on repo-controlled paths; no untrusted input.
        subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
            [
                uv_tool,
                "pip",
                "install",
                "--python",
                str(python_exe),
                "--no-config",
                *TEST_PACKAGES,
            ],
            check=True,
            **CAPTURE_KWARGS,
        )
    else:
        # Isolated venv interpreter driven with fixed repo-owned arguments.
        subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
            [str(python_exe), "-m", "pip", "install", *TEST_PACKAGES],
            check=True,
            **CAPTURE_KWARGS,
        )


def _pytest_command(python_exe: Path, project_root: Path) -> list[str]:
    """Build the pytest command line for the installed distribution.

    Args:
        python_exe: Python interpreter of the isolated venv.
        project_root: Generated project root containing ``tests``.

    Returns:
        Command vector running pytest against the distribution's test suite.

    """
    tests_dir = project_root / "tests"
    command = [
        str(python_exe),
        "-I",
        "-m",
        "pytest",
    ]
    pytest_ini = project_root / "pytest.ini"
    if pytest_ini.is_file():
        command.extend(["-c", str(pytest_ini.resolve())])
    command.extend(
        [
            "-o",
            f"testpaths={tests_dir.resolve()}",
            str(tests_dir.resolve()),
        ]
    )

    return command


def run_distribution_tests(
    python_exe: Path,
    project_root: Path,
    temp_dir: Path,
) -> None:
    """Run the pytest suite against the installed wheel distribution.

    Args:
        python_exe: Python interpreter of the isolated venv.
        project_root: Generated project root containing ``tests``.
        temp_dir: Working directory for pytest execution.

    Raises:
        RuntimeError: If the pytest suite exits non-zero.

    """
    console.print("🧪 Installing test dependencies into isolated environment...")
    _install_test_dependencies(python_exe)

    tests_dir = project_root / "tests"
    if not tests_dir.is_dir():
        console.print(
            f"(info) No tests directory found at {tests_dir}; skipping test execution."
        )
        return

    console.print("🚀 Executing pytest against installed wheel distribution...")
    env = os.environ.copy()
    env["PYTHONWARNDEFAULTENCODING"] = "1"
    # Hermetic interpreter driven with fixed repo-owned pytest arguments.
    result = subprocess.run(  # ruff: ignore[subprocess-without-shell-equals-true]
        _pytest_command(python_exe, project_root),
        cwd=temp_dir,
        env=env,
        check=False,
        **CAPTURE_KWARGS,
    )
    if result.stdout:
        console.print(result.stdout.strip(), markup=False, soft_wrap=True)
    if result.returncode == 0:
        console.print("✅ Distribution test suite passed successfully!")
        return
    if result.stderr:
        error_console.print(result.stderr.strip(), markup=False, soft_wrap=True)
    msg = f"Distribution pytest execution failed with exit code {result.returncode}"
    raise RuntimeError(msg)


def _run_verification(args: argparse.Namespace, temp_dir: Path) -> None:
    """Execute the full wheel-verification pipeline.

    Args:
        args: Parsed CLI arguments.
        temp_dir: Temporary directory reserved for the isolated venv.

    """
    wheel_path = find_wheel(args.dist_dir, args.wheel)
    console.print(f"🔍 Inspecting wheel: {wheel_path}")
    _dist_name, modules, entry_points = inspect_wheel(wheel_path)

    if not modules:
        console.print(f"⚠️ Warning: No Python modules found in {wheel_path.name}")

    console.print("📦 Installing into isolated virtual environment...")
    python_exe = create_isolated_environment(temp_dir)
    install_wheel_in_env(python_exe, wheel_path)

    console.print("🧪 Verifying module imports and entry points...")
    verify_in_venv(python_exe, modules, entry_points, cwd=temp_dir)
    console.print(
        f"✅ Wheel verification successful! All {len(modules)} module(s) and "
        f"{len(entry_points)} entry point(s) imported cleanly."
    )

    if args.run_tests:
        project_root = Path(__file__).resolve().parent.parent
        run_distribution_tests(python_exe, project_root, temp_dir)


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv`` when None.

    Returns:
        The parsed argument namespace.

    """
    parser = argparse.ArgumentParser(
        description="Verify clean module imports and entry points in a built wheel.",
    )
    parser.add_argument(
        "wheel",
        nargs="?",
        type=Path,
        default=None,
        help="Path to .whl file (default: newest file in dist/)",
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=Path("dist"),
        help="Directory to search for wheels (default: dist/)",
    )
    parser.add_argument(
        "--run-tests",
        action="store_true",
        help=(
            "Run pytest test suite against the installed distribution "
            "in the isolated environment"
        ),
    )
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Preserve temporary virtual environment for inspection",
    )

    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Verify clean module imports and entry points in a built wheel.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv`` when None.

    Returns:
        Process exit code: 0 on success, 1 on verification failure.

    """
    args = _parse_args(argv)

    try:
        temp_dir = Path(tempfile.mkdtemp(prefix="wheel_verify_"))
        _run_verification(args, temp_dir)
    except (
        OSError,
        RuntimeError,
        ValueError,
        zipfile.BadZipFile,
        subprocess.SubprocessError,
    ) as exc:
        error_console.print(f"❌ Verification failed: {exc}")
        error_console.print(GUIDANCE_TEXT, markup=False)
        return 1
    else:
        return 0
    finally:
        if args.no_cleanup:
            console.print(f"(info) Temporary environment preserved at: {temp_dir}")
        else:
            shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
