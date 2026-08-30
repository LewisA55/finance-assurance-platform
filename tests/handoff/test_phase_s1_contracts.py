from __future__ import annotations

import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from finance_assurance.handoff import (
    AUDIT_RENDERER_PROFILE,
    AUDIT_RENDERER_PROFILE_HASH,
    AUTHORITY_SPECS,
    FAILURE_REGISTRY,
    XLSX_TYPE_MAP,
    XLSX_TYPE_MAP_HASH,
    XLSX_WRITER_PROFILE,
    XLSX_WRITER_PROFILE_HASH,
    BuildLocalAnalyticalHandoff,
    HandoffOperationFailure,
    canonical_json_file_bytes,
    load_json_authority,
    read_authority_bytes,
    split_sql_authority,
    validate_authorities,
    validate_workbook_vectors,
)
from finance_assurance.handoff.metadata import (
    HandoffChecksumEntry,
    HandoffChecksumLedger,
    HandoffLimitations,
    ValidationCheckRegistryPayload,
)
from finance_assurance.handoff.paths import (
    S_DETACHED_INTEGRITY_PATHS,
    S_FIXED_CANONICAL_PATHS,
    S_NONCANONICAL_PATHS,
    validate_package_path,
)
from finance_assurance.runtime.canonical import canonical_sha256

_DIGEST = "sha256:" + "1" * 64


def _failure_payload(fixture: dict[str, object]) -> dict[str, object]:
    admission = FAILURE_REGISTRY.admission_for(
        str(fixture["expected_failure_code"]),
        str(fixture["operation"]),
        str(fixture["expected_phase"]),
        str(fixture["expected_checkpoint"]),
    )
    state = next(
        item
        for item in FAILURE_REGISTRY.state_vectors
        if item["state_vector_ref"] == admission["state_vector_ref"]
    )
    digest = next(
        item
        for item in FAILURE_REGISTRY.digest_presence_vectors
        if item["digest_presence_ref"] == admission["digest_presence_ref"]
    )
    digest_fields = (
        "expected_handoff_digest",
        "actual_handoff_digest",
        "expected_model_digest",
        "actual_model_digest",
        "expected_source_package_digest",
        "actual_source_package_digest",
    )
    return {
        "failure_contract_version": "handoff-operation-failure@v2",
        "operation": fixture["operation"],
        "failure_code": fixture["expected_failure_code"],
        "failure_phase": fixture["expected_phase"],
        "failure_checkpoint": fixture["expected_checkpoint"],
        "message": fixture["expected_message_fragment"],
        **{
            field: _DIGEST if digest[field] == "PRESENT" else None
            for field in digest_fields
        },
        **{
            field: state[field]
            for field in (
                "canonical_byte_status",
                "same_build_binary_status",
                "logical_equivalence_status",
                "staging_removed",
                "source_package_path_state",
                "source_model_path_state",
                "source_handoff_path_state",
                "output_path_state",
            )
        },
    }


def _admission_payload(admission: dict[str, object]) -> dict[str, object]:
    state = next(
        item
        for item in FAILURE_REGISTRY.state_vectors
        if item["state_vector_ref"] == admission["state_vector_ref"]
    )
    digest = next(
        item
        for item in FAILURE_REGISTRY.digest_presence_vectors
        if item["digest_presence_ref"] == admission["digest_presence_ref"]
    )
    digest_fields = (
        "expected_handoff_digest",
        "actual_handoff_digest",
        "expected_model_digest",
        "actual_model_digest",
        "expected_source_package_digest",
        "actual_source_package_digest",
    )
    state_fields = (
        "canonical_byte_status",
        "same_build_binary_status",
        "logical_equivalence_status",
        "staging_removed",
        "source_package_path_state",
        "source_model_path_state",
        "source_handoff_path_state",
        "output_path_state",
    )
    return {
        "failure_contract_version": "handoff-operation-failure@v2",
        "operation": admission["operation"],
        "failure_code": admission["failure_code"],
        "failure_phase": admission["failure_phase"],
        "failure_checkpoint": admission["failure_checkpoint"],
        "message": f"{admission['failure_code']}: admitted failure",
        **{
            field: _DIGEST if digest[field] == "PRESENT" else None
            for field in digest_fields
        },
        **{field: state[field] for field in state_fields},
    }


def test_all_exact_s1_authorities_and_sql_inventories_validate() -> None:
    validate_authorities()

    assert len(AUTHORITY_SPECS) == 9
    assert tuple(
        query_id
        for query_id, _ in split_sql_authority("starter-queries-v1.sql")
    ) == tuple(f"S-QS{number:02d}" for number in range(1, 6))
    assert tuple(
        query_id
        for query_id, _ in split_sql_authority("reconciliation-queries-v1.sql")
    ) == tuple(f"S-QV{number:02d}" for number in range(1, 13))


def test_exact_profiles_reproduce_pinned_hashes() -> None:
    assert canonical_sha256(XLSX_TYPE_MAP.model_dump(mode="json")) == (
        XLSX_TYPE_MAP_HASH
    )
    assert canonical_sha256(XLSX_WRITER_PROFILE.model_dump(mode="json")) == (
        XLSX_WRITER_PROFILE_HASH
    )
    assert canonical_sha256(AUDIT_RENDERER_PROFILE.model_dump(mode="json")) == (
        AUDIT_RENDERER_PROFILE_HASH
    )
    validate_workbook_vectors()


def test_canonical_json_file_bytes_are_ascii_lf_and_float_free() -> None:
    assert canonical_json_file_bytes({"b": True, "a": 1}) == (
        b'{"a":1,"b":true}\n'
    )
    with pytest.raises(TypeError, match="floating-point"):
        canonical_json_file_bytes({"amount": 1.5})
    with pytest.raises(ValueError, match="ASCII"):
        canonical_json_file_bytes({"label": "pound \N{POUND SIGN}"})


def test_exact_limitations_and_validation_registry_schemas_reject_mutation() -> None:
    limitations = HandoffLimitations.model_validate_json(
        read_authority_bytes("limitations-v1.json")
    )
    registry = ValidationCheckRegistryPayload.model_validate_json(
        read_authority_bytes("validation-registry-v1.json")
    )
    assert len(limitations.limitations) == 4
    assert len(registry.selectors) == 19
    assert len(registry.checks) == 12

    changed = load_json_authority("validation-registry-v1.json")
    changed["registry_id"] = "S-VALIDATION-MUTATED@v1"
    with pytest.raises(ValidationError):
        ValidationCheckRegistryPayload.model_validate_json(json.dumps(changed))


def test_failure_registry_closes_every_admission_fixture_and_recipe() -> None:
    assert len(FAILURE_REGISTRY.checkpoints) == 90
    assert len(FAILURE_REGISTRY.state_vectors) == 28
    assert len(FAILURE_REGISTRY.digest_presence_vectors) == 10
    assert len(FAILURE_REGISTRY.admissions) == 80
    assert len(FAILURE_REGISTRY.fixtures) == 41
    assert len(FAILURE_REGISTRY.recipes) == 41
    assert len(FAILURE_REGISTRY.operators) == 19
    assert len(FAILURE_REGISTRY.operator_contracts) == 19
    assert len(FAILURE_REGISTRY.reseal_contracts) == 7
    assert len(FAILURE_REGISTRY.request_mutation_contracts) == 3
    assert all(
        FAILURE_REGISTRY.operator_contract_for(operator)["operator"] == operator
        for operator in FAILURE_REGISTRY.operators
    )

    failures = tuple(
        HandoffOperationFailure.model_validate(_failure_payload(fixture))
        for fixture in FAILURE_REGISTRY.fixtures
    )
    assert len(failures) == 41
    assert len({item.failure_code for item in failures}) == 20

    admitted = tuple(
        HandoffOperationFailure.model_validate(_admission_payload(admission))
        for admission in FAILURE_REGISTRY.admissions
    )
    assert len(admitted) == 80


def test_failure_serializer_rejects_nonadmitted_checkpoint_and_state() -> None:
    payload = _failure_payload(FAILURE_REGISTRY.fixtures[0])
    invalid_checkpoint = {**payload, "failure_checkpoint": "C01_ENTRY"}
    with pytest.raises(ValidationError, match="not one exact Artifact S admission"):
        HandoffOperationFailure.model_validate(invalid_checkpoint)

    invalid_state = {**payload, "canonical_byte_status": "FAILED"}
    with pytest.raises(ValidationError, match="admitted state vector"):
        HandoffOperationFailure.model_validate(invalid_state)

    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        HandoffOperationFailure.model_validate({**payload, "unexpected": True})


def test_build_request_closes_profile_formats_and_extra_fields() -> None:
    body = {
        "request_contract_version": "build-local-analytical-handoff-request@v1",
        "handoff_ref": "S-HANDOFF-01",
        "source_model_path": Path("model"),
        "source_package_path": Path("package"),
        "expected_model_digest": _DIGEST,
        "expected_source_package_digest": _DIGEST,
        "required_profile_id": "LINEAGE",
        "required_profile_version": 1,
        "required_formats": ("CSV", "PARQUET", "DUCKDB"),
        "output_path": Path("handoff"),
        "producer_release": "finance-assurance-s1@v1",
        "built_at": "2026-08-13T15:00:00Z",
        "xlsx_type_map_ref": "XLSX-TYPE-MAP@v1",
        "xlsx_type_map_hash": XLSX_TYPE_MAP_HASH,
        "xlsx_writer_profile_ref": "XLSXWRITER-3.2.9@v1",
        "xlsx_writer_profile_hash": XLSX_WRITER_PROFILE_HASH,
        "validation_registry_ref": "S-VALIDATION-C001-CT1@v1",
        "validation_registry_hash": (
            "sha256:36255992b12b0176f290ec2fa033e5655d8ca4b3a2e4cbd3a522a1de295f7cb8"
        ),
    }
    request = BuildLocalAnalyticalHandoff.model_validate(body)
    assert request.required_formats == ("CSV", "PARQUET", "DUCKDB")

    with pytest.raises(ValidationError, match="required formats must be exact"):
        BuildLocalAnalyticalHandoff.model_validate(
            {**body, "required_formats": ("CSV", "PARQUET")}
        )
    with pytest.raises(ValidationError, match="Extra inputs are not permitted"):
        BuildLocalAnalyticalHandoff.model_validate({**body, "dashboard": True})


def test_static_package_paths_are_disjoint_normalized_and_firewalled() -> None:
    paths = (
        *S_FIXED_CANONICAL_PATHS,
        *S_DETACHED_INTEGRITY_PATHS,
        *S_NONCANONICAL_PATHS,
    )
    assert len(paths) == len(set(paths))
    assert all(validate_package_path(path) == path for path in paths)

    for unsafe in ("../outside", "/absolute", "C:/drive", "a\\b", "a//b"):
        with pytest.raises(ValueError):
            validate_package_path(unsafe)


def test_checksum_ledger_requires_lexical_unique_paths() -> None:
    entry_a = HandoffChecksumEntry(path="a.json", sha256=_DIGEST, byte_count=1)
    entry_b = HandoffChecksumEntry(path="b.json", sha256=_DIGEST, byte_count=1)
    ledger = HandoffChecksumLedger(
        contract_version="handoff-checksum-ledger@v1", files=(entry_a, entry_b)
    )
    assert tuple(item.path for item in ledger.files) == ("a.json", "b.json")
    with pytest.raises(ValidationError, match="lexical and unique"):
        HandoffChecksumLedger(
            contract_version="handoff-checksum-ledger@v1",
            files=(entry_b, entry_a),
        )
