from __future__ import annotations

import hashlib
import json
from pathlib import Path

from finance_assurance.exports.registry import DATASET_BY_ID, DATASETS
from finance_assurance.handoff.metadata import (
    ConsumerSuitabilityEntry,
    DataDictionaryColumn,
    DataDictionaryTable,
    DatasetCellPointer,
    DatasetPointer,
    DirectedJoinStep,
    EvidenceStatusField,
    FieldProvenance,
    FieldRoleProjection,
    HandoffBinding,
    JsonSourcePointer,
    MeasureDefinition,
    RCacheBinding,
    RelationshipPlanEntry,
    SourceBindingTableEntry,
    SourceDatasetBinding,
    SourceDocumentBinding,
)
from finance_assurance.runtime.canonical import canonical_sha256

_ROOT = Path(__file__).parents[2]
_AUTHORITY = _ROOT / "tests" / "fixtures" / "local-analytical-handoff"


def _load(name: str) -> dict[str, object]:
    return json.loads((_AUTHORITY / name).read_text(encoding="ascii"))


def _sha256(name: str) -> str:
    return "sha256:" + hashlib.sha256((_AUTHORITY / name).read_bytes()).hexdigest()


def test_v08_authority_hashes_and_metadata_vectors_are_exact() -> None:
    vectors = _load("metadata-construction-vectors-v1.json")
    recipes = _load("negative-mutation-recipes-v2.json")
    fixtures = _load("negative-fixture-registry-v3.json")

    assert _sha256("metadata-construction-vectors-v1.json") == (
        "sha256:13ab23aed3d86e79d5fc0f7a26caa946848e99b9fb5753d7339e7d256ea8221e"
    )
    assert canonical_sha256(vectors) == (
        "sha256:8fd2724b7e67df394e441147939ead38709bbe3c6691ea9dbc0084df7089afa3"
    )
    assert _sha256("negative-mutation-recipes-v2.json") == (
        "sha256:d37b83e707f7c5e9df18637fcfabd4662db3493445081a46c78b8180be21a51e"
    )
    assert canonical_sha256(recipes) == (
        "sha256:353836caecffdc2a17a515d8c7e90287845192bea17334bfa66352e23e50c5c3"
    )
    assert _sha256("negative-fixture-registry-v3.json") == (
        "sha256:e343a0a81d75a61d22fb44b411019137ba73d1436ceb6008c67f43cf39148ecd"
    )
    assert canonical_sha256(fixtures) == (
        "sha256:d57b3ab43204f61d351554bf79117d916e59d007b66b99aeb8ae158becb01073"
    )

    rows = vectors["vectors"]
    assert [row[0] for row in rows] == [f"S-MV{number:02d}" for number in range(1, 9)]
    assert all(canonical_sha256(row[:9]) == row[9] for row in rows)
    assert vectors["source_model_document_contract_versions"] == {
        "source-model/model-manifest.json": "consumer-model@v1",
        "source-model/semantic-model.json": "semantic-catalogue@v1",
        "source-model/relationships.json": "relationship-catalogue@v1",
        "source-model/checksums.json": "checksum-ledger@v1",
        "source-model/model.digest": "detached-model-digest@v1",
        "source-model/noncanonical-cache.json": "duckdb-cache-manifest@v1",
    }


def test_v08_nested_field_names_equal_the_executable_models() -> None:
    vectors = _load("metadata-construction-vectors-v1.json")
    exact_models = {
        "HandoffBinding@v1": HandoffBinding,
        "SourceDocumentBinding@v1": SourceDocumentBinding,
        "SourceDatasetBinding@v1": SourceDatasetBinding,
        "JsonSourcePointer@v1": JsonSourcePointer,
        "DatasetCellPointer@v1": DatasetCellPointer,
        "FieldProvenance@v1": FieldProvenance,
        "RCacheBinding@v1": RCacheBinding,
        "FieldRoleProjection@v1": FieldRoleProjection,
        "DatasetPointer@v1": DatasetPointer,
        "DirectedJoinStep@v1": DirectedJoinStep,
        "EvidenceStatusField@v1": EvidenceStatusField,
        "ConsumerSuitabilityEntry@v1": ConsumerSuitabilityEntry,
    }
    inherited_models = {
        "SourceBindingTableEntry@v1": SourceBindingTableEntry,
        "DataDictionaryTable@v1": DataDictionaryTable,
        "DataDictionaryColumn@v1": DataDictionaryColumn,
        "RelationshipProjection@v1": RelationshipPlanEntry,
        "MeasureProjection@v1": MeasureDefinition,
    }
    assert {
        name: list(model.model_fields) for name, model in exact_models.items()
    } == vectors["exact_s_model_fields"]
    assert {
        name: list(model.model_fields) for name, model in inherited_models.items()
    } == vectors["inherited_r_model_fields"]

    assert [item.dataset_id for item in DATASETS].index("P-D06") == 5
    assert all(
        column.type != "enum"
        for dataset_id in ("P-D16", "P-D17")
        for column in DATASET_BY_ID[dataset_id].columns
    )
    assert vectors["lineage_literal_selection"]["evidence_status_fields"] == []


def test_v08_fourteen_recipe_corrections_and_fixture_closure_are_exact() -> None:
    recipes = _load("negative-mutation-recipes-v2.json")
    fixtures = _load("negative-fixture-registry-v3.json")
    recipe_by_ref = {row[0]: row for row in recipes["recipes"]}
    fixture_by_id = {row[0]: row for row in fixtures["fixtures"]}

    expected = {
        "S-NF02": ("SOURCE_MODEL::schemas/p-evidence-v1/P-D06.schema.json", "REGULAR_FILE_SHA256:SOURCE_MODEL_MANIFEST_ENTRY:schemas/p-evidence-v1/P-D06.schema.json"),
        "S-NF04": ("SOURCE_HANDOFF::handoff-manifest.json#/handoff_digest", "ABSENT"),
        "S-NF09": ("SOURCE_HANDOFF::metadata/data-dictionary.json#/source_datasets/5/logical_table_digest", "TEXT:SOURCE_MODEL_DATASET_DIGEST:P-D06"),
        "S-NF10": ("SOURCE_HANDOFF::metadata/lineage.json#/field_provenance/0/source_pointers", "JSON:CURRENT_TARGET_VALUE"),
        "S-NF11": ("SOURCE_HANDOFF::metadata/validation-checks.json#/payload/checks/0/assertions/0/kind", "TEXT:FIELD_EQUALS"),
        "S-NF14": ("SOURCE_HANDOFF::metadata/validation-checks.json#/payload/checks/10/assertions/0/left/selector_ref", "TEXT:SEL-CT1-AUTHORED-HEADERS"),
        "S-NF15": ("SOURCE_HANDOFF::metadata/validation-checks.json#/payload/checks/11/assertions/0/direction", "TEXT:SOURCE_TO_TARGET"),
        "S-NF21": ("SOURCE_MODEL::noncanonical-cache.json#/profile_coordinate/profile_version", "INTEGER:1"),
        "S-NF22": ("SOURCE_MODEL::model-manifest.json#/table_entries/5/row_count", "INTEGER:SOURCE_MODEL_ROW_COUNT:P-D06"),
        "S-NF23": ("SOURCE_HANDOFF::metadata/validation-checks.json#/payload/checks/0/assertions/0/expected/value", "INTEGER:0"),
        "S-NF26": ("RUNTIME::xlsx_writer_profile/XLSXWRITER-3.2.9@v1", "AVAILABLE:XlsxWriter-3.2.9"),
        "S-NF27": ("STAGING::limitations.json#/limitations", "JSON:CURRENT_TARGET_VALUE"),
        "S-NF38": ("REQUEST::expected_model_digest", "TEXT:sha256:64-lower-hex"),
        "S-NF39": ("SOURCE_MODEL::model-manifest.json", "SHA256:CURRENT_TARGET_BYTES"),
    }
    for fixture_id, target_and_before in expected.items():
        recipe = recipe_by_ref[fixture_by_id[fixture_id][2]]
        assert (recipe[3], recipe[5]) == target_and_before

    assert len(recipe_by_ref) == len(recipes["recipes"]) == 41
    assert len(fixture_by_id) == len(fixtures["fixtures"]) == 41
    assert {row[2] for row in fixtures["fixtures"]} == set(recipe_by_ref)
    grammar = recipes["value_ref_grammar"]
    assert "JSON:CURRENT_TARGET_VALUE" in grammar
    assert "SHA256:CURRENT_TARGET_BYTES" in grammar
