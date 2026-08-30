"""CLI for finance source generation and Bronze ingestion."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date
from pathlib import Path

from finance_assurance.finance_data.contracts import (
    FinanceDataBuildRequest,
)
from finance_assurance.finance_data.service import FinanceDataSubstrateService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build or verify finance data substrate")
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build")
    build.add_argument("--data-ref", required=True)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--built-at", required=True)
    build.add_argument("--scale-profile", default="PORTFOLIO")
    build.add_argument("--seed", type=int, default=42)
    build.add_argument("--history-start", type=date.fromisoformat, default=date(2021, 1, 1))
    build.add_argument("--actuals-end", type=date.fromisoformat, default=date(2026, 6, 30))
    build.add_argument("--reporting-currency", default="GBP")
    build.add_argument("--statutory-contract-version", default="A2.4")
    verify = subparsers.add_parser("verify")
    verify.add_argument("--package", required=True, type=Path)
    verify.add_argument("--expected-digest")
    reproduce = subparsers.add_parser("reproduce")
    reproduce.add_argument("--source-package", required=True, type=Path)
    reproduce.add_argument("--output", required=True, type=Path)
    reproduce.add_argument("--expected-digest")
    assess = subparsers.add_parser("assess")
    assess.add_argument("--source-package", required=True, type=Path)
    assess.add_argument("--reproduction-package", required=True, type=Path)
    assess.add_argument("--expected-digest", required=True)
    assess.add_argument("--report-output", type=Path)
    return parser


def _json_result(value: object) -> str:
    payload = asdict(value)  # type: ignore[arg-type]
    for key, item in tuple(payload.items()):
        if isinstance(item, Path):
            payload[key] = str(item)
    return json.dumps(payload, indent=2, sort_keys=True)


def main() -> int:
    args = _parser().parse_args()
    service = FinanceDataSubstrateService()
    if args.command == "build":
        result = service.build(
            FinanceDataBuildRequest(
                data_ref=args.data_ref,
                output_path=args.output,
                built_at=args.built_at,
                scale_profile=args.scale_profile,
                seed=args.seed,
                history_start=args.history_start,
                actuals_end=args.actuals_end,
                reporting_currency=args.reporting_currency,
                statutory_contract_version=args.statutory_contract_version,
            )
        )
    else:
        result = service.verify(
            args.package, expected_digest=args.expected_digest
        )
    print(_json_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
