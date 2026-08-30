from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from finance_assurance.digestion.registry import (
    COLUMN_ROLE_REGISTRY,
    MEASURE_REGISTRY,
    datasets_for_profile,
    relationship_plan,
)
from finance_assurance.handoff.metadata import MetadataDocument
from finance_assurance.runtime.canonical import canonical_sha256

from .v10_authority_builder import build_context, build_documents
from .v10_logical_resolver import LogicalFixtureResolver, load_json

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


def _pointer(root: Any, pointer: str) -> Any:
    if pointer in {"", "/"}:
        return root
    current = root
    for raw in pointer.removeprefix("/").split("/"):
        segment = raw.replace("~1", "/").replace("~0", "~")
        current = current[int(segment)] if isinstance(current, list) else current[segment]
    return current


def _file_sha256(name: str) -> str:
    return "sha256:" + hashlib.sha256((AUTHORITY / name).read_bytes()).hexdigest()


def _r_field_role_projection(item: Any) -> dict[str, Any]:
    value = item.model_dump(mode="json")
    return {
        key: value[key]
        for key in (
            "source_coordinate",
            "source_name",
            "source_type",
            "physical_type",
            "column_role",
            "default_visibility",
            "default_summarization",
            "display_label",
            "display_folder",
        )
    }


def _target_identity_sequence(values: list[dict[str, Any]]) -> list[Any]:
    result = []
    for item in values:
        if "relationship_id" in item:
            result.append(item["relationship_id"])
        elif "measure_id" in item:
            result.append(item["measure_id"])
        elif "source_name" in item:
            result.append((item["source_coordinate"], item["source_name"]))
        elif "source_coordinate" in item:
            result.append(item["source_coordinate"])
        else:
            result.append(item)
    return result


def test_v10_projects_complete_exact_r_metadata() -> None:
    authority = load_json("metadata-positive-logical-vectors-v3.json")
    assert authority["contract_version"] == "handoff-metadata-positive-logical-vectors@v3"
    assert len(authority["vectors"]) == 8
    assert [item["vector_ref"] for item in authority["vectors"]] == [
        f"S-MV10-{number:02d}" for number in range(1, 9)
    ]

    payload_by_path = {
        item["metadata_path"]: item["document"]["payload"] for item in authority["vectors"]
    }
    selected = {
        (item.registry_id, item.dataset_id) for item in datasets_for_profile("LINEAGE")
    }
    expected_roles = [
        _r_field_role_projection(item)
        for item in COLUMN_ROLE_REGISTRY
        if (
            item.source_coordinate.registry_id,
            item.source_coordinate.dataset_id,
        )
        in selected
    ]

    assert len(payload_by_path["metadata/source-model.json"]["table_entries"]) == 31
    assert len(payload_by_path["metadata/data-dictionary.json"]["columns"]) == 388
    assert payload_by_path["metadata/relationships.json"]["relationships"] == [
        item.model_dump(mode="json") for item in relationship_plan("LINEAGE")
    ]
    assert payload_by_path["metadata/measures.json"]["measures"] == [
        item.model_dump(mode="json") for item in MEASURE_REGISTRY
    ]
    actual_roles = [
        {key: value for key, value in item.items() if key != "format_hints"}
        for item in payload_by_path["metadata/field-roles.json"]["fields"]
    ]
    assert actual_roles == expected_roles

    amount_role = next(
        item
        for item in payload_by_path["metadata/field-roles.json"]["fields"]
        if item["source_coordinate"]["dataset_id"] == "P-D06"
        and item["source_name"] == "amount_minor"
    )
    assert amount_role["default_visibility"] == "HIDDEN"
    assert amount_role["display_folder"] is None
    first_measure = payload_by_path["metadata/measures.json"]["measures"][0]
    assert first_measure["measure_name"] == "Reporting Value Minor"
    assert first_measure["required_grouping"] == [
        "scenario_ref",
        "reporting_version_ref",
        "statement_field",
    ]
    assert first_measure["default_format"] == "INTEGER_MINOR_UNITS"


def test_v10_provenance_dereferences_r_sources() -> None:
    authority = load_json("metadata-positive-logical-vectors-v3.json")
    for vector in authority["vectors"]:
        document = MetadataDocument.model_validate_json(json.dumps(vector["document"]))
        logical = document.model_dump(mode="json")
        assert canonical_sha256(logical) == vector["expected_object_digest"]
        expected_coverage = _covered_paths(logical["payload"])
        actual_coverage = {
            (item["target_json_pointer"], item["coverage"])
            for item in logical["field_provenance"]
        }
        assert actual_coverage == expected_coverage
        assert (
            vector["construction_inputs"]["source_document_payloads"].keys()
            == {item["path"] for item in logical["source_documents"]}
        )

        source_payloads = vector["construction_inputs"]["source_document_payloads"]
        for provenance in logical["field_provenance"]:
            pointers = provenance["source_pointers"]
            if provenance["derivation_class"] == "S_GUIDANCE":
                assert pointers == []
                continue
            assert pointers, provenance["target_json_pointer"]
            source_values = [
                _pointer(
                    source_payloads[pointer["source_document_path"]],
                    pointer["json_pointer"],
                )
                for pointer in pointers
                if pointer["pointer_kind"] == "JSON_POINTER"
            ]
            assert len(source_values) == len(pointers)
            target = _pointer(logical, provenance["target_json_pointer"])
            if provenance["coverage"] == "VALUE":
                assert target in source_values, provenance["target_json_pointer"]
            else:
                if len(source_values) == 1 and target == source_values[0]:
                    continue
                if (
                    len(source_values) == 1
                    and isinstance(target, list)
                    and isinstance(source_values[0], list)
                ):
                    assert _target_identity_sequence(target) == _target_identity_sequence(
                        source_values[0]
                    ), provenance["target_json_pointer"]
                    continue
                assert _target_identity_sequence(target) == _target_identity_sequence(
                    source_values
                ), provenance["target_json_pointer"]

    lineage = next(
        item
        for item in authority["vectors"]
        if item["metadata_path"] == "metadata/lineage.json"
    )
    relationship_source = lineage["construction_inputs"]["source_document_payloads"][
        "source-model/relationships.json"
    ]
    assert relationship_source[25]["relationship_id"] == "P-RL11"
    assert relationship_source[26]["relationship_id"] == "P-RL12"


def test_v10_mutates_private_context_and_observes_first_failures() -> None:
    recipes = load_json("negative-mutation-recipes-v2.json")["recipes"]
    fixtures = load_json("negative-fixture-registry-v3.json")["fixtures"]
    fixture_by_recipe = {row[2]: row for row in fixtures}
    observed = []
    resealed = 0
    request_mutated = 0
    validator_count = 0

    for recipe in recipes:
        resolver = LogicalFixtureResolver()
        target_before = resolver.resolve_target(recipe[0], recipe[3])
        result = resolver.execute_recipe(recipe)
        target_after = resolver.resolve_target(recipe[0], recipe[3])
        fixture = fixture_by_recipe[recipe[0]]

        assert target_after != target_before, recipe[0]
        assert result.changed_targets[0] == recipe[3], recipe[0]
        assert result.first_failure_checkpoint == recipe[9], recipe[0]
        assert result.first_failure_checkpoint == fixture[6], recipe[0]
        assert result.first_failure_code == fixture[4], recipe[0]
        assert result.validators_executed[-1] == recipe[9], recipe[0]
        assert recipe[9] not in result.validators_executed[:-1], recipe[0]
        assert resolver.authority_context == load_json(
            "mutation-positive-context-v2.json"
        )
        if recipe[7] != "NONE":
            assert result.reseal_steps_executed, recipe[0]
            resealed += 1
        else:
            assert result.reseal_steps_executed == (), recipe[0]
        if recipe[8] != "NONE":
            assert result.request_mutation_executed == recipe[8], recipe[0]
            request_mutated += 1
        else:
            assert result.request_mutation_executed is None, recipe[0]
        validator_count += len(result.validators_executed)
        observed.append(result)

    assert len(observed) == len({item.recipe_ref for item in observed}) == 41
    assert resealed == 17
    assert request_mutated == 15
    assert validator_count > len(observed)


def test_v10_generated_authorities_are_ascii_lf_and_hash_stable() -> None:
    for name in (
        "metadata-positive-logical-vectors-v3.json",
        "mutation-positive-context-v2.json",
    ):
        payload = (AUTHORITY / name).read_bytes()
        assert payload.endswith(b"\n") and b"\r" not in payload
        payload.decode("ascii")
    metadata = load_json("metadata-positive-logical-vectors-v3.json")
    context = load_json("mutation-positive-context-v2.json")
    assert metadata["vectors"] == build_documents()
    assert context == build_context(metadata["vectors"])
    assert _file_sha256("metadata-positive-logical-vectors-v3.json") == (
        "sha256:e2eafd5219822547e06513191165180ba7283bb44de342c60a79314579de945f"
    )
    assert canonical_sha256(metadata) == (
        "sha256:9568d76a28acd4c44eb881fa50022bc86ad3c1a6bdd693404decaae464a14268"
    )
    assert _file_sha256("mutation-positive-context-v2.json") == (
        "sha256:c32461aa324f71a6ef9a23a6035afe6198edd523af47f7d3e062b4a1b7a3488d"
    )
    assert canonical_sha256(context) == (
        "sha256:4b25e5332ab2b3a7fafa7cc7aab5175efb01c360ef744ec06a8b1ab727748517"
    )
