from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

import pytest
from pydantic import ValidationError

from finance_assurance.digestion.contracts import (
    BuildConsumerModel,
    ColumnSemantic,
    ParquetWriterProfile,
)
from finance_assurance.digestion.writer import PARQUET_WRITER_PROFILE

FIXTURES = Path(__file__).parents[1] / "fixtures" / "model-digestion"


def _positive_payload() -> dict[str, object]:
    return json.loads((FIXTURES / "build-request-positive.json").read_text())


def _validate_wire(payload: dict[str, object]) -> BuildConsumerModel:
    return BuildConsumerModel.model_validate_json(json.dumps(payload))


def test_positive_build_request_fixture_is_strict_and_frozen() -> None:
    request = _validate_wire(_positive_payload())

    assert request.profile_id == "LINEAGE"
    assert request.formats == ("CSV", "PARQUET")
    assert request.parquet_writer_profile_hash == PARQUET_WRITER_PROFILE.profile_hash
    with pytest.raises(ValidationError):
        request.model_ref = "MUTATED"  # type: ignore[misc]


@pytest.mark.parametrize(
    "case",
    json.loads((FIXTURES / "build-request-negative.json").read_text()),
    ids=lambda item: item["case"],
)
def test_negative_build_request_fixtures_fail_closed(case: dict[str, object]) -> None:
    payload = deepcopy(_positive_payload())
    payload.update(case["updates"])  # type: ignore[arg-type]

    with pytest.raises(ValidationError, match=str(case["error_contains"])):
        _validate_wire(payload)


def test_writer_profile_rejects_a_tampered_hash() -> None:
    payload = PARQUET_WRITER_PROFILE.model_dump(mode="json")
    payload["profile_hash"] = "sha256:" + "0" * 64

    with pytest.raises(ValidationError, match="profile_hash"):
        ParquetWriterProfile.model_validate(payload)


def test_column_contract_rejects_cross_variant_enum_metadata() -> None:
    payload = {
        "column_role": "DOMAIN_ATTRIBUTE",
        "default_summarization": "NONE",
        "default_visibility": "VISIBLE",
        "display_folder": None,
        "display_label": "Status",
        "enum_values": ("OPEN",),
        "nullable": False,
        "physical_type": "UTF8",
        "source_coordinate": {
            "dataset_id": "P-D09",
            "dataset_version": 1,
            "registry_id": "P-EVIDENCE",
            "registry_version": 1
        },
        "source_name": "status",
        "source_type": "text",
        "transformation": "EXACT_COPY",
        "value_origin": "O_VIEW_FIELD"
    }

    with pytest.raises(ValidationError, match="only source enum"):
        ColumnSemantic.model_validate(payload)


def test_source_column_cannot_use_not_loaded_to_evade_parity() -> None:
    payload = {
        "column_role": "DOMAIN_ATTRIBUTE",
        "default_summarization": "NONE",
        "default_visibility": "NOT_LOADED",
        "display_folder": None,
        "display_label": "Status",
        "enum_values": (),
        "nullable": False,
        "physical_type": "UTF8",
        "source_coordinate": {
            "dataset_id": "P-D09",
            "dataset_version": 1,
            "registry_id": "P-EVIDENCE",
            "registry_version": 1
        },
        "source_name": "status",
        "source_type": "text",
        "transformation": "EXACT_COPY",
        "value_origin": "O_VIEW_FIELD"
    }

    with pytest.raises(ValidationError, match="cannot be NOT_LOADED"):
        ColumnSemantic.model_validate(payload)
