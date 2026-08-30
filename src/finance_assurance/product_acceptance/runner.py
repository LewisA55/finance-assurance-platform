"""One-command Milestone 1, 2, and public-product acceptance runner."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from finance_assurance.acceptance.report import parse_junit
from finance_assurance.acceptance.scope import repository_root
from finance_assurance.product_acceptance.manual import evaluate_manual_evidence
from finance_assurance.product_acceptance.report import GateResult, build_report
from finance_assurance.runtime.canonical import canonical_bytes
from finance_assurance.runtime.digests import stable_value

M2_REPORT_PATH = Path("build/milestone-2-report.json")
M2_JUNIT_PATH = Path("build/milestone-2-tests.xml")
M3_REPORT_PATH = Path("build/milestone-3-report.json")
DEFAULT_MANUAL_EVIDENCE = Path("build/milestone-3-manual-browser-evidence.json")


def _run(
    command: tuple[str, ...],
    root: Path,
    *,
    timeout: int = 600,
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout.decode() if isinstance(error.stdout, bytes) else error.stdout
        stderr = error.stderr.decode() if isinstance(error.stderr, bytes) else error.stderr
        message = f"command timed out after {timeout} seconds"
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


def _npm() -> str:
    executable = shutil.which("npm.cmd" if os.name == "nt" else "npm")
    if executable is None:
        raise RuntimeError("Node.js and npm are required for Milestone 3 acceptance")
    return executable


def _gate(gate_id: str, passed: bool, outcome: str) -> GateResult:
    return GateResult(gate_id, "PASS" if passed else "FAIL", outcome)


def _build_digest(output: str) -> str | None:
    match = re.search(r"Deterministic application build: ([0-9a-f]{64})", output)
    return match.group(1) if match else None


def _digest(path: Path) -> str | None:
    if not path.exists():
        return None
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def main(argv: tuple[str, ...] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require-clean",
        action="store_true",
        help="require a clean Git worktree for O-A32",
    )
    parser.add_argument(
        "--manual-evidence",
        type=Path,
        default=DEFAULT_MANUAL_EVIDENCE,
        help="revision-bound manual browser evidence JSON",
    )
    args = parser.parse_args(argv)
    root = repository_root()
    web = root / "web"
    (root / "build").mkdir(exist_ok=True)
    for generated in (M2_REPORT_PATH, M2_JUNIT_PATH, M3_REPORT_PATH):
        (root / generated).unlink(missing_ok=True)

    clean = _clean(root) if args.require_clean else False
    revision = _revision(root)
    m2 = _run(
        (
            sys.executable,
            "-m",
            "finance_assurance.acceptance",
            "--require-clean",
        ),
        root,
        timeout=900,
    )
    typecheck = _run((_npm(), "run", "typecheck"), web)
    lint = _run((_npm(), "run", "lint"), web)
    web_test = _run((_npm(), "test"), web)
    public_verify = _run((sys.executable, "public_product.py", "verify"), root)

    m2_report_path = root / M2_REPORT_PATH
    m2_passed = False
    if m2_report_path.exists():
        try:
            m2_passed = json.loads(m2_report_path.read_bytes())["overall"] == "PASS"
        except (json.JSONDecodeError, KeyError, TypeError):
            m2_passed = False
    junit_path = root / M2_JUNIT_PATH
    test_cases = parse_junit(junit_path.read_bytes()) if junit_path.exists() else ()
    build_digest = _build_digest(public_verify.stdout)
    manual_path = args.manual_evidence
    if not manual_path.is_absolute():
        manual_path = root / manual_path
    manual = evaluate_manual_evidence(manual_path, repository_revision=revision)
    gates = (
        GateResult(
            "clean_checkout",
            "PASS" if clean else "BLOCKED",
            "Git worktree is clean" if clean else "clean-checkout proof not established",
        ),
        _gate("milestone2", m2.returncode == 0 and m2_passed, "unchanged M1/M2 command and report passed"),
        _gate("python_quality", m2.returncode == 0, "M2 Ruff and pytest gates passed"),
        _gate("web_typecheck", typecheck.returncode == 0, "TypeScript passed"),
        _gate("web_lint", lint.returncode == 0, "ESLint passed"),
        _gate("web_test", web_test.returncode == 0, "rendered product tests passed"),
        _gate("public_verify", public_verify.returncode == 0 and build_digest is not None, "deterministic build, local startup, and same-origin boundary passed"),
        GateResult("manual_browser", manual.status, manual.outcome),
        GateResult("report_reproducibility", "PASS", "canonical report reproduced from identical evidence"),
    )
    arguments = {
        "repository_revision": revision,
        "milestone2_report_digest": _digest(m2_report_path),
        "test_cases": test_cases,
        "application_build_digest": build_digest,
        "manual_evidence_digest": manual.evidence_digest,
        "quality_gates": gates,
    }
    first = build_report(**arguments)  # type: ignore[arg-type]
    second = build_report(**arguments)  # type: ignore[arg-type]
    if first.canonical_bytes != second.canonical_bytes:
        gates = tuple(
            GateResult(item.gate_id, "FAIL", "canonical report was not reproducible")
            if item.gate_id == "report_reproducibility"
            else item
            for item in gates
        )
        arguments["quality_gates"] = gates
        first = build_report(**arguments)  # type: ignore[arg-type]
    (root / M3_REPORT_PATH).write_bytes(canonical_bytes(stable_value(first)))

    print("finance-assurance acceptance: Milestone 1 + 2 + public product")
    for gate in first.quality_gates:
        print(f"{gate.gate_id.upper()} {gate.status}")
    print(f"M3 {first.overall} ({first.status_counts['PASS']}/{len(first.criteria)})")
    print(f"M3-REPORT {M3_REPORT_PATH.as_posix()}")
    for result in (m2, typecheck, lint, web_test, public_verify):
        if result.returncode != 0:
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                print(result.stderr)
    return 0 if first.overall == "PASS" else 1
