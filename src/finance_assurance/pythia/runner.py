"""CLI for the governed Pythia D6 package."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from finance_assurance.pythia import (
    PythiaBuildRequest,
    PythiaService,
    PythiaVerifyRequest,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build or verify PYTHIA-D6@v1")
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--finance-delivery", required=True, type=Path)
    build.add_argument("--expected-finance-delivery-digest", required=True)
    build.add_argument("--output", required=True, type=Path)
    build.add_argument("--built-at", required=True)
    build.add_argument("--producer-release", default="0.1.0")
    verify = commands.add_parser("verify")
    verify.add_argument("--finance-delivery", required=True, type=Path)
    verify.add_argument("--expected-finance-delivery-digest", required=True)
    verify.add_argument("--package", required=True, type=Path)
    verify.add_argument("--expected-pythia-digest", required=True)
    return parser


def main() -> int:
    args = _parser().parse_args()
    service = PythiaService()
    if args.command == "build":
        result = service.build(
            PythiaBuildRequest(
                contract_version="pythia-d6-build-request@v1",
                pythia_ref="PYTHIA-D6@v1",
                finance_delivery_path=args.finance_delivery,
                expected_finance_delivery_digest=args.expected_finance_delivery_digest,
                output_path=args.output,
                built_at=args.built_at,
                producer_release=args.producer_release,
            )
        )
    else:
        result = service.verify(
            PythiaVerifyRequest(
                contract_version="pythia-d6-verify-request@v1",
                package_path=args.package,
                finance_delivery_path=args.finance_delivery,
                expected_pythia_digest=args.expected_pythia_digest,
                expected_finance_delivery_digest=args.expected_finance_delivery_digest,
            )
        )
    print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
