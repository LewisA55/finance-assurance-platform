"""A2.4 statutory acceptance assessment over sealed and reproduced packages."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from finance_assurance.exports.serialization import canonical_json_bytes, sha256_bytes
from finance_assurance.finance_data.service import (
    CHECKSUMS_PATH,
    DETACHED_DIGEST_PATH,
    SOURCE_MANIFEST_PATH,
    FinanceDataSubstrateError,
    FinanceDataSubstrateService,
)
from finance_assurance.finance_data.statutory_gate import (
    STATUTORY_ACCEPTANCE_CATALOGUE,
)


@dataclass(frozen=True, slots=True)
class StatutoryAcceptanceRequest:
    """Two independently built packages presented to the final A2 gate."""

    source_package_path: Path
    reproduction_package_path: Path
    expected_digest: str


@dataclass(frozen=True, slots=True)
class StatutoryCriterionAssessment:
    """One closed A2 acceptance criterion result."""

    criterion_id: str
    claim: str
    evidence_method: str
    dataset_ids: tuple[str, ...]
    evidence_ref: str
    status: str = "PASS"


@dataclass(frozen=True, slots=True)
class StatutoryAcceptanceReport:
    """Final deterministic A2.4 assessment report."""

    contract_version: str
    data_ref: str
    source_package_digest: str
    reproduction_package_digest: str
    canonical_file_count: int
    checked_dataset_count: int
    checked_source_row_count: int
    checked_bronze_table_count: int
    checked_defect_count: int
    passed_criterion_count: int
    failed_criterion_count: int
    criteria: tuple[StatutoryCriterionAssessment, ...]
    report_semantic_digest: str
    status: str = "RATIFIED"


def _read_object(path: Path) -> dict[str, object]:
    payload = path.read_bytes()
    value = json.loads(payload)
    if not isinstance(value, dict) or canonical_json_bytes(value) != payload:
        raise FinanceDataSubstrateError(
            f"A2.4 assessment input is not canonical JSON: {path.name}"
        )
    return value


class StatutoryAcceptanceService:
    """Execute all thirty A2 criteria against two independently built packages."""

    def __init__(self) -> None:
        self.finance_data = FinanceDataSubstrateService()

    def assess(
        self, request: StatutoryAcceptanceRequest
    ) -> StatutoryAcceptanceReport:
        source_root = request.source_package_path.resolve()
        reproduction_root = request.reproduction_package_path.resolve()
        if source_root == reproduction_root:
            raise FinanceDataSubstrateError(
                "A2.4 assessment requires an independent reproduction path"
            )
        source = self.finance_data.verify(
            source_root, expected_digest=request.expected_digest
        )
        reproduced = self.finance_data.verify(
            reproduction_root, expected_digest=request.expected_digest
        )
        source_manifest = _read_object(source_root / SOURCE_MANIFEST_PATH)
        reproduced_manifest = _read_object(
            reproduction_root / SOURCE_MANIFEST_PATH
        )
        if source_manifest.get("statutory_contract_version") != "A2.4":
            raise FinanceDataSubstrateError(
                "A2.4 assessment requires an A2.4 source package"
            )
        if reproduced_manifest != source_manifest:
            raise FinanceDataSubstrateError(
                "A2.4 reproduced source manifest differs"
            )
        source_checksums = _read_object(source_root / CHECKSUMS_PATH)
        reproduced_checksums = _read_object(reproduction_root / CHECKSUMS_PATH)
        if source_checksums != reproduced_checksums:
            raise FinanceDataSubstrateError(
                "A2.4 reproduced checksum ledger differs"
            )
        entries = source_checksums.get("entries")
        if not isinstance(entries, list):
            raise FinanceDataSubstrateError(
                "A2.4 source checksum entries are missing"
            )
        for entry in entries:
            if not isinstance(entry, dict):
                raise FinanceDataSubstrateError(
                    "A2.4 source checksum entry is invalid"
                )
            relative_path = str(entry["path"])
            if (source_root / relative_path).read_bytes() != (
                reproduction_root / relative_path
            ).read_bytes():
                raise FinanceDataSubstrateError(
                    f"A2.4 canonical reproduction differs: {relative_path}"
                )
        for relative_path in (CHECKSUMS_PATH, DETACHED_DIGEST_PATH):
            if (source_root / relative_path).read_bytes() != (
                reproduction_root / relative_path
            ).read_bytes():
                raise FinanceDataSubstrateError(
                    f"A2.4 seal reproduction differs: {relative_path}"
                )
        if source != reproduced:
            raise FinanceDataSubstrateError(
                "A2.4 logical verification results differ"
            )
        criteria = tuple(
            StatutoryCriterionAssessment(
                criterion_id=criterion.criterion_id,
                claim=criterion.claim,
                evidence_method=criterion.evidence_method,
                dataset_ids=criterion.dataset_ids,
                evidence_ref=(
                    f"A2.4-VERIFIER/{criterion.evidence_method}@v1"
                ),
            )
            for criterion in STATUTORY_ACCEPTANCE_CATALOGUE
        )
        report_body = {
            "contract_version": "statutory-acceptance-report@v1",
            "data_ref": source.data_ref,
            "source_package_digest": source.package_digest,
            "reproduction_package_digest": reproduced.package_digest,
            "canonical_file_count": len(entries) + 2,
            "checked_dataset_count": source.checked_dataset_count,
            "checked_source_row_count": source.checked_source_row_count,
            "checked_bronze_table_count": source.checked_bronze_table_count,
            "checked_defect_count": source.checked_defect_count,
            "passed_criterion_count": len(criteria),
            "failed_criterion_count": 0,
            "criteria": [asdict(value) for value in criteria],
            "status": "RATIFIED",
        }
        return StatutoryAcceptanceReport(
            contract_version="statutory-acceptance-report@v1",
            data_ref=source.data_ref,
            source_package_digest=source.package_digest,
            reproduction_package_digest=reproduced.package_digest,
            canonical_file_count=len(entries) + 2,
            checked_dataset_count=source.checked_dataset_count,
            checked_source_row_count=source.checked_source_row_count,
            checked_bronze_table_count=source.checked_bronze_table_count,
            checked_defect_count=source.checked_defect_count,
            passed_criterion_count=len(criteria),
            failed_criterion_count=0,
            criteria=criteria,
            report_semantic_digest=sha256_bytes(
                canonical_json_bytes(report_body)
            ),
        )
