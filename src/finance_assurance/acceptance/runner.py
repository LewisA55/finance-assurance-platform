"""One-command Milestone 1 and Milestone 2 closure runner."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from finance_assurance.acceptance.report import build_report, parse_junit
from finance_assurance.acceptance.runtime_proof import run_runtime_equivalence
from finance_assurance.acceptance.scope import (
    deferred_surface_violations,
    repository_root,
    runtime_validation_imports,
)
from finance_assurance.runtime.canonical import canonical_bytes
from finance_assurance.runtime.digests import stable_value
from finance_assurance.validation.h7_reporting import run_h7
from finance_assurance.validation.report import JsonFileReportSink

M1_REPORT_PATH = Path("build/validation-report.json")
M2_REPORT_PATH = Path("build/milestone-2-report.json")
JUNIT_PATH = Path("build/milestone-2-tests.xml")
COMMAND_TIMEOUT_SECONDS = 600


def _run(command: tuple[str, ...], root: Path) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=COMMAND_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else error.stdout
        stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else error.stderr
        message = f"command timed out after {COMMAND_TIMEOUT_SECONDS} seconds"
        return subprocess.CompletedProcess(
            command,
            124,
            stdout or "",
            f"{stderr or ''}\n{message}".strip(),
        )


def _revision(root: Path) -> str | None:
    result = _run(("git", "rev-parse", "HEAD"), root)
    return result.stdout.strip() if result.returncode == 0 else None


def _clean(root: Path) -> bool:
    result = _run(("git", "status", "--porcelain", "--untracked-files=all"), root)
    return result.returncode == 0 and not result.stdout.strip()


def main(argv: tuple[str, ...] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="block M2-A19 unless the Git worktree is clean",
    )
    args = parser.parse_args(argv)
    root = repository_root()
    build = root / "build"
    build.mkdir(exist_ok=True)
    for generated in (M1_REPORT_PATH, M2_REPORT_PATH, JUNIT_PATH):
        (root / generated).unlink(missing_ok=True)

    # Artifact H's optional root is a fixture-directory override, not a repository
    # root. The default resolves the ratified fixture corpus and repository revision.
    h7 = run_h7()
    JsonFileReportSink(root / M1_REPORT_PATH).write(h7.report)
    ruff = _run((sys.executable, "-m", "ruff", "check", "."), root)
    pytest = _run(
        (
            sys.executable,
            "-m",
            "pytest",
            "-q",
            f"--junitxml={JUNIT_PATH.as_posix()}",
        ),
        root,
    )
    junit = root / JUNIT_PATH
    test_cases = parse_junit(junit.read_bytes()) if junit.exists() else ()
    proofs_a = run_runtime_equivalence()
    proofs_b = run_runtime_equivalence()
    proofs_reproducible = stable_value(proofs_a) == stable_value(proofs_b)
    clean = _clean(root) if args.require_clean else False
    report = build_report(
        repository_revision=_revision(root),
        h0_h7_report=h7.semantic_bytes,
        h0_h7_passed=h7.report.overall.value == "PASS",
        test_cases=test_cases,
        pytest_passed=pytest.returncode == 0,
        ruff_passed=ruff.returncode == 0,
        runtime_proofs=proofs_a,
        runtime_proofs_reproducible=proofs_reproducible,
        runtime_independent=not runtime_validation_imports(root),
        bounded_scope=not deferred_surface_violations(root),
        clean_checkout=clean,
    )
    report_path = root / M2_REPORT_PATH
    report_path.write_bytes(canonical_bytes(stable_value(report)))

    print("finance-assurance acceptance: Milestone 1 + Milestone 2")
    print(f"H0-H7 {report.quality_gates.h0_h7}")
    print(f"RUFF {report.quality_gates.ruff}")
    print(f"PYTEST {report.quality_gates.pytest} ({report.test_count} tests)")
    for proof in report.runtime_proofs:
        status = "PASS" if proof.passed else "FAIL"
        print(f"{proof.family} RESTART-REBUILD {status}")
    print(
        "M2 "
        f"{report.overall} "
        f"({report.status_counts['PASS']}/{len(report.criteria)})"
    )
    print(f"M1-REPORT {M1_REPORT_PATH.as_posix()}")
    print(f"M2-REPORT {M2_REPORT_PATH.as_posix()}")
    if ruff.returncode != 0 and ruff.stdout:
        print(ruff.stdout)
    if pytest.returncode != 0 and pytest.stdout:
        print(pytest.stdout)
    return 0 if report.overall == "PASS" else 1
