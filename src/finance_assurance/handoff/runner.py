"""Command-line entry point for the local analytical handoff builder."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from finance_assurance.handoff.contracts import (
    BuildLocalAnalyticalHandoff,
    VerifyLocalAnalyticalHandoff,
)
from finance_assurance.handoff.profiles import (
    XLSX_TYPE_MAP_HASH,
    XLSX_WRITER_PROFILE_HASH,
)
from finance_assurance.handoff.service import LocalAnalyticalHandoffService

_VALIDATION_HASH = (
    "sha256:36255992b12b0176f290ec2fa033e5655d8ca4b3a2e4cbd3a522a1de295f7cb8"
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    build = commands.add_parser("build", help="build and atomically publish a handoff")
    build.add_argument("--handoff-ref", required=True)
    build.add_argument("--source-model", type=Path, required=True)
    build.add_argument("--source-package", type=Path, required=True)
    build.add_argument("--model-digest", required=True)
    build.add_argument("--source-package-digest", required=True)
    build.add_argument("--output", type=Path, required=True)
    build.add_argument("--producer-release", required=True)
    build.add_argument("--built-at", required=True)

    verify = commands.add_parser("verify", help="verify an existing handoff")
    verify.add_argument("--handoff", type=Path, required=True)
    verify.add_argument("--source-package", type=Path, required=True)
    verify.add_argument("--handoff-digest", required=True)
    verify.add_argument("--model-digest", required=True)
    verify.add_argument("--source-package-digest", required=True)
    return parser


def main(argv: tuple[str, ...] | None = None) -> int:
    args = _parser().parse_args(argv)
    service = LocalAnalyticalHandoffService()
    if args.command == "build":
        result = service.build(
            BuildLocalAnalyticalHandoff(
                request_contract_version=(
                    "build-local-analytical-handoff-request@v1"
                ),
                handoff_ref=args.handoff_ref,
                source_model_path=args.source_model,
                source_package_path=args.source_package,
                expected_model_digest=args.model_digest,
                expected_source_package_digest=args.source_package_digest,
                required_profile_id="LINEAGE",
                required_profile_version=1,
                required_formats=("CSV", "PARQUET", "DUCKDB"),
                output_path=args.output,
                producer_release=args.producer_release,
                built_at=args.built_at,
                xlsx_type_map_ref="XLSX-TYPE-MAP@v1",
                xlsx_type_map_hash=XLSX_TYPE_MAP_HASH,
                xlsx_writer_profile_ref="XLSXWRITER-3.2.9@v1",
                xlsx_writer_profile_hash=XLSX_WRITER_PROFILE_HASH,
                validation_registry_ref="S-VALIDATION-C001-CT1@v1",
                validation_registry_hash=_VALIDATION_HASH,
            )
        )
    else:
        result = service.verify(
            VerifyLocalAnalyticalHandoff(
                request_contract_version=(
                    "verify-local-analytical-handoff-request@v1"
                ),
                handoff_path=args.handoff,
                source_package_path=args.source_package,
                expected_handoff_digest=args.handoff_digest,
                expected_model_digest=args.model_digest,
                expected_source_package_digest=args.source_package_digest,
                verification_scope="FULL_HANDOFF_EQUIVALENCE",
            )
        )
    print(json.dumps(result.model_dump(mode="json"), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
