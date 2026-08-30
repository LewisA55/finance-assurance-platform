from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

from finance_assurance.analytics.registry import DATASETS as Q_DATASETS
from finance_assurance.digestion.registry import (
    ALL_DATASET_COORDINATES,
    COLUMN_ROLE_REGISTRY,
    COMPOSITE_RELATIONSHIP_IDS,
    MEASURE_REGISTRY,
    PROFILE_DATASET_IDS,
    RELATIONSHIP_KEY_PROJECTIONS,
    SOURCE_COLUMN_REGISTRY,
    portable_alias,
    registry_contract_hash,
    relationship_plan,
    validate_registry,
    validate_relationship_graph,
)
from finance_assurance.exports.registry import DATASETS as P_DATASETS

FIXTURES = Path(__file__).parents[1] / "fixtures" / "model-digestion"


def _expectations() -> dict[str, object]:
    return json.loads((FIXTURES / "r1-registry-expectations.json").read_text())


def test_registry_closes_exact_source_inventory() -> None:
    expected = _expectations()
    validate_registry()

    assert len(ALL_DATASET_COORDINATES) == expected["dataset_count"]
    assert len(SOURCE_COLUMN_REGISTRY) == expected["source_column_count"]
    assert len(COLUMN_ROLE_REGISTRY) - len(SOURCE_COLUMN_REGISTRY) == expected[
        "technical_column_placements"
    ]
    assert sum(
        column.type == "integer"
        for dataset in (*P_DATASETS, *Q_DATASETS)
        for column in dataset.columns
    ) == expected["raw_integer_columns"]
    assert all(item.default_summarization == "NONE" for item in COLUMN_ROLE_REGISTRY)
    assert registry_contract_hash().startswith("sha256:")


def test_profiles_are_exact_and_cumulative() -> None:
    expected = _expectations()["profile_counts"]

    assert {key: len(value) for key, value in PROFILE_DATASET_IDS.items()} == expected
    assert PROFILE_DATASET_IDS["CORE"] < PROFILE_DATASET_IDS["LINEAGE"]
    assert PROFILE_DATASET_IDS["LINEAGE"] < PROFILE_DATASET_IDS["DIAGNOSTIC"]
    assert set().union(*PROFILE_DATASET_IDS.values()) == {
        item.dataset_id for item in ALL_DATASET_COORDINATES
    }


def test_composite_keys_are_exact_and_endpoint_typed() -> None:
    expected = _expectations()["composite_relationship_ids"]

    assert [item.relationship_id for item in RELATIONSHIP_KEY_PROJECTIONS] == expected
    assert (
        tuple(item.relationship_id for item in RELATIONSHIP_KEY_PROJECTIONS)
        == COMPOSITE_RELATIONSHIP_IDS
    )
    assert all(
        item.from_types == item.to_types for item in RELATIONSHIP_KEY_PROJECTIONS
    )
    assert all(item.role == "R_TECHNICAL" for item in RELATIONSHIP_KEY_PROJECTIONS)
    assert all(item.visibility == "HIDDEN" for item in RELATIONSHIP_KEY_PROJECTIONS)


def test_each_profile_has_one_finite_safe_relationship_plan() -> None:
    expected = _expectations()["profile_relationship_counts"]
    for profile_id in ("CORE", "LINEAGE", "DIAGNOSTIC"):
        plan = relationship_plan(profile_id)  # type: ignore[arg-type]
        counts = Counter(item.load_disposition for item in plan)
        validate_relationship_graph(plan)
        assert len(plan) == expected[profile_id]["TOTAL"]
        assert counts == Counter(
            {
                key: value
                for key, value in expected[profile_id].items()
                if key != "TOTAL"
            }
        )
        assert all(
            item.cross_filter_direction == "ONE_TO_MANY"
            for item in plan
            if item.load_disposition == "ACTIVE"
        )
        assert all(
            item.cross_filter_direction == "NONE"
            for item in plan
            if item.load_disposition != "ACTIVE"
        )


def test_relationship_graph_rejects_cycles_and_duplicate_paths() -> None:
    template = next(
        item
        for item in relationship_plan("DIAGNOSTIC")
        if item.load_disposition == "ACTIVE"
    )
    edge_ab = template.model_copy(
        update={"from_dataset": "B", "relationship_id": "TEST-AB", "to_dataset": "A"}
    )
    edge_ba = template.model_copy(
        update={"from_dataset": "A", "relationship_id": "TEST-BA", "to_dataset": "B"}
    )
    with pytest.raises(ValueError, match="cycle"):
        validate_relationship_graph((edge_ab, edge_ba))

    edge_ac = template.model_copy(
        update={"from_dataset": "C", "relationship_id": "TEST-AC", "to_dataset": "A"}
    )
    edge_bc = template.model_copy(
        update={"from_dataset": "C", "relationship_id": "TEST-BC", "to_dataset": "B"}
    )
    with pytest.raises(ValueError, match="duplicate paths"):
        validate_relationship_graph((edge_ab, edge_ac, edge_bc))


def test_measure_registry_closes_double_counting_guards() -> None:
    assert len(MEASURE_REGISTRY) == _expectations()["measure_count"]
    assert tuple(item.measure_id for item in MEASURE_REGISTRY) == tuple(
        f"R-M{number:02d}" for number in range(1, 13)
    )
    assert all(
        item.currency_policy == "SINGLE_EXACT_CURRENCY"
        for item in MEASURE_REGISTRY
    )
    authored = {"R-M09", "R-M10"}
    referenced = {"R-M11", "R-M12"}
    by_id = {item.measure_id: item for item in MEASURE_REGISTRY}
    assert all(set(by_id[item].non_combinable_with) == referenced for item in authored)
    assert all(set(by_id[item].non_combinable_with) == authored for item in referenced)
    assert all(
        "Gross Activity" in item.measure_name
        for item in MEASURE_REGISTRY
        if item.classification == "ADDITIVE_GOVERNED_TOTAL"
    )


def test_portable_aliases_are_unique_and_bounded() -> None:
    datasets = {
        "P-EVIDENCE": {item.dataset_id: item for item in P_DATASETS},
        "Q-ANALYTICS": {item.dataset_id: item for item in Q_DATASETS},
    }
    aliases = [
        portable_alias(
            coordinate.registry_id,
            coordinate.dataset_id,
            datasets[coordinate.registry_id][coordinate.dataset_id].name,
        )
        for coordinate in ALL_DATASET_COORDINATES
    ]

    assert len(aliases) == len(set(aliases)) == 37
    assert all(alias.startswith("r_") and len(alias) <= 63 for alias in aliases)


def test_digestion_cold_start_does_not_load_product_or_persistence() -> None:
    script = """
import sys
import finance_assurance.digestion
forbidden = [
    name for name in sys.modules
    if name.startswith('finance_assurance.product')
    or name.startswith('finance_assurance.runtime.persistence')
]
if forbidden:
    raise SystemExit(','.join(sorted(forbidden)))
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        check=False,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
