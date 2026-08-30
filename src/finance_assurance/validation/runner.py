"""Top-level deterministic harness runner."""

from pathlib import Path

from finance_assurance.validation.h7_reporting import exit_code_for, run_h7
from finance_assurance.validation.report import JsonFileReportSink
from finance_assurance.validation.results import AssertionStatus

HARNESS_HEADER = "finance-assurance validation harness: H0-H7"
REPORT_PATH = Path("build/validation-report.json")


def _summary(label: str, results: tuple[object, ...], passed: bool) -> str:
    passed_count = sum(
        getattr(result, "status", None) is AssertionStatus.PASS for result in results
    )
    return f"{label} {'PASS' if passed else 'FAIL'} ({passed_count}/{len(results)})"


def main() -> int:
    """Run H0-H7 once, persist its report, and print a stable summary."""

    run = run_h7()
    JsonFileReportSink(REPORT_PATH).write(run.report)
    lower = run.lower

    print(HARNESS_HEADER)
    print(_summary("H0", lower.h0.results, lower.h0.passed))
    print(_summary("H1", lower.h1.results, lower.h1.passed))
    print(_summary("H2", lower.h2.results, lower.h2.passed))
    print(_summary("H3", lower.h3.results, lower.h3.passed))
    print(_summary("H4", lower.h4.results, lower.h4.passed))
    print(_summary("H5", lower.h5.results, lower.h5.passed))
    print(_summary("H6", lower.h6.results, lower.h6.passed))
    print(_summary("H7", run.results, run.passed))
    print(_summary("H3-GUARD", lower.h3_guards.results, lower.h3_guards.passed))
    print(f"REPORT {REPORT_PATH.as_posix()}")
    print(f"OVERALL {run.report.overall.value}")
    return exit_code_for(run.report)


if __name__ == "__main__":
    raise SystemExit(main())
