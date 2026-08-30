"""CLI for governed Q-FINANCE model profiles."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from finance_assurance.finance_model.contracts import (
    FinanceModelBuildRequest,
    FinanceModelVerifyRequest,
)
from finance_assurance.finance_model.service import FinanceModelService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build or verify a Q-FINANCE profile")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--source-package", required=True, type=Path)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--expected-source-digest", required=True)
    build.add_argument("--built-at", required=True)
    build.add_argument("--model-ref", default="Q-FINANCE-B1@v1")
    verify = commands.add_parser("verify")
    verify.add_argument("--source-package", required=True, type=Path)
    verify.add_argument("--package", required=True, type=Path)
    verify.add_argument("--expected-source-digest", required=True)
    verify.add_argument("--expected-package-digest")
    return parser


def _json_result(value: object) -> str:
    payload = asdict(value)  # type: ignore[arg-type]
    for key, item in tuple(payload.items()):
        if isinstance(item, Path):
            payload[key] = str(item)
    return json.dumps(payload, indent=2, sort_keys=True)


def main() -> int:
    args = _parser().parse_args()
    service = FinanceModelService()
    if args.command == "build":
        result = service.build(
            FinanceModelBuildRequest(
                source_package_path=args.source_package,
                output_path=args.output,
                expected_source_digest=args.expected_source_digest,
                built_at=args.built_at,
                model_ref=args.model_ref,
            )
        )
    else:
        result = service.verify(
            FinanceModelVerifyRequest(
                source_package_path=args.source_package,
                package_path=args.package,
                expected_source_digest=args.expected_source_digest,
                expected_package_digest=args.expected_package_digest,
            )
        )
    print(_json_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
