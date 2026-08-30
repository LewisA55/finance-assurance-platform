"""Command-line entry point for Q-FINANCE C2 consumer materialisation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from finance_assurance.finance_delivery.contracts import (
    FinanceDeliveryBuildRequest,
    FinanceDeliveryVerifyRequest,
)
from finance_assurance.finance_delivery.service import FinanceDeliveryService


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build")
    build.add_argument("--finance-model-package", type=Path, required=True)
    build.add_argument("--source-data-package", type=Path, required=True)
    build.add_argument("--finance-model-digest", required=True)
    build.add_argument("--source-data-digest", required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--workbook-output", type=Path, required=True)
    build.add_argument("--preview-output", type=Path, required=True)
    build.add_argument("--built-at", required=True)
    build.add_argument("--producer-release", required=True)

    verify = commands.add_parser("verify")
    verify.add_argument("--delivery", type=Path, required=True)
    verify.add_argument("--finance-model-package", type=Path, required=True)
    verify.add_argument("--source-data-package", type=Path, required=True)
    verify.add_argument("--delivery-digest", required=True)
    verify.add_argument("--finance-model-digest", required=True)
    verify.add_argument("--source-data-digest", required=True)
    return parser


def main(argv: tuple[str, ...] | None = None) -> int:
    args = _parser().parse_args(argv)
    service = FinanceDeliveryService()
    if args.command == "build":
        result = service.build(
            FinanceDeliveryBuildRequest(
                contract_version="q-finance-c2-build-request@v1",
                delivery_ref="Q-FINANCE-C2@v1",
                finance_model_package_path=args.finance_model_package,
                source_data_package_path=args.source_data_package,
                expected_finance_model_digest=args.finance_model_digest,
                expected_source_data_digest=args.source_data_digest,
                output_path=args.output,
                workbook_output_path=args.workbook_output,
                preview_output_path=args.preview_output,
                built_at=args.built_at,
                producer_release=args.producer_release,
            )
        )
    else:
        result = service.verify(
            FinanceDeliveryVerifyRequest(
                contract_version="q-finance-c2-verify-request@v1",
                delivery_path=args.delivery,
                finance_model_package_path=args.finance_model_package,
                source_data_package_path=args.source_data_package,
                expected_delivery_digest=args.delivery_digest,
                expected_finance_model_digest=args.finance_model_digest,
                expected_source_data_digest=args.source_data_digest,
            )
        )
    print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
