from __future__ import annotations

from datetime import UTC, datetime
from zoneinfo import ZoneInfo

import pyarrow as pa
import pytest
from pydantic import ValidationError

from finance_assurance.finance_delivery.contracts import FinanceDeliveryBuildRequest
from finance_assurance.finance_delivery.service import (
    NULL_TOKEN,
    _csv_bytes,
    _csv_table,
    _logical_digest,
    _TableSnapshot,
)


def test_build_contract_rejects_non_canonical_digest(tmp_path) -> None:
    with pytest.raises(ValidationError):
        FinanceDeliveryBuildRequest(
            contract_version="q-finance-c2-build-request@v1",
            delivery_ref="Q-FINANCE-C2@v1",
            finance_model_package_path=tmp_path / "c1",
            source_data_package_path=tmp_path / "a24",
            expected_finance_model_digest="not-a-digest",
            expected_source_data_digest=f"sha256:{'a' * 64}",
            output_path=tmp_path / "delivery",
            workbook_output_path=tmp_path / "pack.xlsx",
            preview_output_path=tmp_path / "previews",
            built_at="2026-08-25T09:00:00Z",
            producer_release="test",
        )


def test_logical_digest_normalises_aware_timestamps_to_utc() -> None:
    columns = (
        {
            "name": "recorded_at",
            "data_type": "TIMESTAMP WITH TIME ZONE",
            "ordinal": 1,
            "nullable": False,
        },
    )
    london = pa.Table.from_pylist(
        [{"recorded_at": datetime(2026, 7, 1, 9, tzinfo=ZoneInfo("Europe/London"))}],
        schema=pa.schema([pa.field("recorded_at", pa.timestamp("us", tz="Europe/London"), nullable=False)]),
    )
    utc = pa.Table.from_pylist(
        [{"recorded_at": datetime(2026, 7, 1, 8, tzinfo=UTC)}],
        schema=pa.schema([pa.field("recorded_at", pa.timestamp("us", tz="UTC"), nullable=False)]),
    )
    assert _logical_digest(london, columns) == _logical_digest(utc, columns)


def test_csv_uses_explicit_null_and_replays_exact_types(tmp_path) -> None:
    columns = (
        {"name": "row_id", "data_type": "VARCHAR", "ordinal": 1, "nullable": False},
        {"name": "amount_minor", "data_type": "BIGINT", "ordinal": 2, "nullable": True},
        {"name": "approved_flag", "data_type": "BOOLEAN", "ordinal": 3, "nullable": False},
    )
    arrow = pa.Table.from_pylist(
        [
            {"row_id": "R-001", "amount_minor": None, "approved_flag": True},
            {"row_id": "R-002", "amount_minor": -125, "approved_flag": False},
        ],
        schema=pa.schema(
            [
                pa.field("row_id", pa.string(), nullable=False),
                pa.field("amount_minor", pa.int64()),
                pa.field("approved_flag", pa.bool_(), nullable=False),
            ]
        ),
    )
    snapshot = _TableSnapshot(
        dataset={"dataset_id": "QF-TEST", "relation_name": "mart_test"},
        columns=columns,
        arrow=arrow,
        logical_digest=_logical_digest(arrow, columns),
        partition_column=None,
    )
    payload = _csv_bytes(snapshot)
    assert b"\r" not in payload
    assert NULL_TOKEN.encode("ascii") in payload
    path = tmp_path / "mart_test.csv"
    path.write_bytes(payload)
    replay = _csv_table(path, columns)
    assert _logical_digest(replay, columns) == snapshot.logical_digest
