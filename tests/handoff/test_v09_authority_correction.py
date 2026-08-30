from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from finance_assurance.handoff.metadata import MetadataDocument
from finance_assurance.runtime.canonical import canonical_sha256

from .v09_authority_builder import build_context, build_documents
from .v09_logical_resolver import LogicalFixtureResolver, load_json

ROOT = Path(__file__).parents[2]
AUTHORITY = ROOT / "tests" / "fixtures" / "local-analytical-handoff"


def _covered_paths(value: Any, path: str = "/payload") -> set[tuple[str, str]]:
    result: set[tuple[str, str]] = set()
    if isinstance(value, list):
        result.add((path, "ARRAY_ORDER"))
        for index, item in enumerate(value):
            result.update(_covered_paths(item, f"{path}/{index}"))
    elif isinstance(value, dict):
        for key, item in value.items():
            escaped = key.replace("~", "~0").replace("/", "~1")
            result.update(_covered_paths(item, f"{path}/{escaped}"))
    else:
        result.add((path, "VALUE"))
    return result


def _file_sha256(name: str) -> str:
    return "sha256:" + hashlib.sha256((AUTHORITY / name).read_bytes()).hexdigest()


def test_v09_contains_eight_complete_positive_metadata_objects() -> None:
    authority = load_json("metadata-positive-logical-vectors-v2.json")
    assert authority["contract_version"] == "handoff-metadata-positive-logical-vectors@v2"
    assert len(authority["vectors"]) == 8
    assert [item["vector_ref"] for item in authority["vectors"]] == [
        f"S-MV09-{number:02d}" for number in range(1, 9)
    ]
    source_model = authority["vectors"][0]["document"]["payload"]
    data_dictionary = authority["vectors"][1]["document"]["payload"]
    assert len(source_model["table_entries"]) == 31
    assert len(data_dictionary["tables"]) == 31
    assert len(data_dictionary["columns"]) == 388

    for vector in authority["vectors"]:
        vector_preimage = {
            key: value
            for key, value in vector.items()
            if key != "expected_vector_digest"
        }
        assert canonical_sha256(vector_preimage) == vector["expected_vector_digest"]
        document = MetadataDocument.model_validate_json(json.dumps(vector["document"]))
        logical = document.model_dump(mode="json")
        assert canonical_sha256(logical) == vector["expected_object_digest"]
        construction = vector["construction_inputs"]
        assert construction["contract_version"] == logical["contract_version"]
        assert construction["handoff_binding"] == logical["handoff_binding"]
        assert construction["source_documents"] == logical["source_documents"]
        assert construction["source_datasets"] == logical["source_datasets"]
        assert construction["payload_projection"] == logical["payload"]
        assert construction["provenance_mapping"] == logical["field_provenance"]
        expected_coverage = _covered_paths(logical["payload"])
        actual_coverage = {
            (item["target_json_pointer"], item["coverage"])
            for item in logical["field_provenance"]
        }
        assert actual_coverage == expected_coverage
        assert all(
            item["source_pointers"]
            if item["derivation_class"] in {"R_COPY", "R_PROJECTION"}
            else not item["source_pointers"]
            for item in logical["field_provenance"]
        )
        document_paths = {item["path"] for item in logical["source_documents"]}
        dataset_coordinates = {
            tuple(item["source_coordinate"].values())
            for item in logical["source_datasets"]
        }
        for provenance in logical["field_provenance"]:
            for pointer in provenance["source_pointers"]:
                if pointer["pointer_kind"] == "JSON_POINTER":
                    assert pointer["source_document_path"] in document_paths
                    assert pointer["json_pointer"].startswith("/")
                    assert pointer["json_pointer"] != "/"
                else:
                    assert tuple(pointer["source_coordinate"].values()) in dataset_coordinates
                    assert pointer["selector_ref"].startswith("SEL-")
                    assert pointer["field_name"]


def test_v09_lineage_vectors_retain_complete_composite_fields() -> None:
    authority = load_json("metadata-positive-logical-vectors-v2.json")
    lineage = next(
        item["document"]["payload"]
        for item in authority["vectors"]
        if item["metadata_path"] == "metadata/lineage.json"
    )
    assert [step["from_fields"] for step in lineage["directed_join_steps"]] == [
        ["scenario_ref", "reporting_version_ref", "statement_field", "source_ref"],
        ["scenario_ref", "reporting_version_ref", "statement_field", "target_ref"],
    ]
    assert [step["to_fields"] for step in lineage["directed_join_steps"]] == [
        ["scenario_ref", "reporting_version_ref", "statement_field", "node_ref"],
        ["scenario_ref", "reporting_version_ref", "statement_field", "node_ref"],
    ]


def test_v09_resolves_and_mutates_all_forty_one_recipe_targets() -> None:
    resolver = LogicalFixtureResolver()
    recipes = load_json("negative-mutation-recipes-v2.json")["recipes"]
    failures = load_json("operation-failure-state-registry-v1.json")
    fixtures = load_json("negative-fixture-registry-v3.json")["fixtures"]
    checkpoints = {row[0]: row[3] for row in failures["checkpoints"]}
    fixture_by_recipe = {row[2]: row for row in fixtures}
    admitted_failures = {tuple(row[:4]) for row in failures["admissions"]}

    resolved_refs: list[str] = []
    for recipe in recipes:
        recipe_ref = recipe[0]
        fixture = fixture_by_recipe[recipe_ref]
        target = resolver.resolve_target(recipe_ref, recipe[3])
        before = resolver.resolve_before(recipe_ref, recipe[5], target)
        assert before == target, recipe_ref
        mutated = resolver.apply_mutation(recipe[4], recipe[6], target)
        assert mutated != target, recipe_ref
        assert recipe[1] == fixture[1], recipe_ref
        assert recipe[8] == fixture[3], recipe_ref
        assert recipe[9] == fixture[6], recipe_ref
        assert tuple([fixture[4], fixture[1], fixture[5], fixture[6]]) in (
            admitted_failures
        ), recipe_ref
        assert checkpoints[recipe[2]] < checkpoints[recipe[9]], recipe_ref
        resolved_refs.append(recipe_ref)

    assert len(resolved_refs) == len(set(resolved_refs)) == 41


def test_v09_generated_authorities_are_ascii_lf_and_hash_stable() -> None:
    for name in (
        "metadata-positive-logical-vectors-v2.json",
        "mutation-positive-context-v1.json",
    ):
        payload = (AUTHORITY / name).read_bytes()
        assert payload.endswith(b"\n") and b"\r" not in payload
        payload.decode("ascii")
    metadata = load_json("metadata-positive-logical-vectors-v2.json")
    context = load_json("mutation-positive-context-v1.json")
    assert metadata["vectors"] == build_documents()
    assert context == build_context(metadata["vectors"])
    assert _file_sha256("metadata-positive-logical-vectors-v2.json") == (
        "sha256:febfb07b82465ac8204db036d9fd758a023526d86faa4ff7ae70cf7662f3460b"
    )
    assert canonical_sha256(metadata) == (
        "sha256:f372e26b65872e9b64ec2e80266b8b14ce75c75623ee33990c076f5af722454d"
    )
    assert _file_sha256("mutation-positive-context-v1.json") == (
        "sha256:a44d58028a0fa0db7f5c7ff9d549ab42abc731bac54e078a74782d4a67b39ae6"
    )
    assert canonical_sha256(context) == (
        "sha256:8f56e97f27e8668eeb2d1614d1527a79fb2653fe5bd6eab3faefa91e19406ca4"
    )
