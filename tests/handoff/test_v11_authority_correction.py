from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from finance_assurance.digestion.contracts import (
    ModelManifest,
    NoncanonicalCacheManifest,
    RelationshipPlanEntry,
    SemanticCatalogue,
)
from finance_assurance.digestion.registry import (
    COLUMN_ROLE_REGISTRY,
    MEASURE_REGISTRY,
    datasets_for_profile,
    relationship_plan,
)
from finance_assurance.exports.contracts import ChecksumLedger
from finance_assurance.exports.serialization import sha256_bytes
from finance_assurance.handoff.metadata import MetadataDocument
from finance_assurance.runtime.canonical import canonical_sha256

from .v11_authority_builder import build_context, build_documents
from .v11_logical_resolver import (
    VALIDATOR_RULES,
    LogicalFixtureResolver,
    load_json,
)

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
        current = (
            current[int(segment)] if isinstance(current, list) else current[segment]
        )
    return current


def _identity_sequence(values: list[dict[str, Any]]) -> list[Any]:
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


def test_v11_authenticates_exact_r_source_bytes() -> None:
    authority = load_json("metadata-positive-logical-vectors-v4.json")
    assert authority["contract_version"] == (
        "handoff-metadata-positive-logical-vectors@v4"
    )
    assert [item["vector_ref"] for item in authority["vectors"]] == [
        f"S-MV11-{number:02d}" for number in range(1, 9)
    ]
    observed_bytes: dict[str, bytes] = {}
    for vector in authority["vectors"]:
        construction = vector["construction_inputs"]
        bindings = {
            item["path"]: item for item in vector["document"]["source_documents"]
        }
        assert construction["source_document_bytes_ascii"].keys() == bindings.keys()
        assert construction["source_document_payloads"].keys() == bindings.keys()
        for path, text in construction["source_document_bytes_ascii"].items():
            source_bytes = text.encode("ascii")
            assert sha256_bytes(source_bytes) == bindings[path]["sha256"]
            if path in observed_bytes:
                assert observed_bytes[path] == source_bytes
            observed_bytes[path] = source_bytes
            if path.endswith(".json"):
                assert json.loads(source_bytes) == construction[
                    "source_document_payloads"
                ][path]
            else:
                assert source_bytes.decode("ascii") == construction[
                    "source_document_payloads"
                ][path]

    manifest = ModelManifest.model_validate_json(
        observed_bytes["source-model/model-manifest.json"]
    )
    semantic = SemanticCatalogue.model_validate_json(
        observed_bytes["source-model/semantic-model.json"]
    )
    relationships = json.loads(observed_bytes["source-model/relationships.json"])
    assert [
        RelationshipPlanEntry.model_validate_json(json.dumps(item)).model_dump(
            mode="json"
        )
        for item in relationships
    ] == relationships
    ledger = ChecksumLedger.model_validate_json(
        observed_bytes["source-model/checksums.json"]
    )
    cache = NoncanonicalCacheManifest.model_validate_json(
        observed_bytes["source-model/noncanonical-cache.json"]
    )
    model_digest_text = observed_bytes["source-model/model.digest"].decode("ascii")
    assert re.fullmatch(r"sha256:[0-9a-f]{64}\n", model_digest_text)
    assert model_digest_text == (
        sha256_bytes(observed_bytes["source-model/checksums.json"]) + "\n"
    )
    ledger_by_path = {item.relative_path: item.sha256 for item in ledger.files}
    assert ledger_by_path["model-manifest.json"] == sha256_bytes(
        observed_bytes["source-model/model-manifest.json"]
    )
    assert ledger_by_path["semantic-model.json"] == sha256_bytes(
        observed_bytes["source-model/semantic-model.json"]
    )
    assert ledger_by_path["relationships.json"] == sha256_bytes(
        observed_bytes["source-model/relationships.json"]
    )
    assert tuple(ledger_by_path) == manifest.canonical_digest_scope
    assert semantic.model_ref == manifest.model_ref == cache.model_ref
    assert len(cache.table_entries) == len(manifest.table_entries) == 31


def test_v11_retains_exact_r_projection_and_authenticated_provenance() -> None:
    authority = load_json("metadata-positive-logical-vectors-v4.json")
    payload_by_path = {
        item["metadata_path"]: item["document"]["payload"]
        for item in authority["vectors"]
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
    assert [
        {key: value for key, value in item.items() if key != "format_hints"}
        for item in payload_by_path["metadata/field-roles.json"]["fields"]
    ] == expected_roles

    for vector in authority["vectors"]:
        document = MetadataDocument.model_validate_json(
            json.dumps(vector["document"])
        )
        logical = document.model_dump(mode="json")
        assert canonical_sha256(logical) == vector["expected_object_digest"]
        preimage = {
            key: value
            for key, value in vector.items()
            if key != "expected_vector_digest"
        }
        assert canonical_sha256(preimage) == vector["expected_vector_digest"]
        assert {
            (item["target_json_pointer"], item["coverage"])
            for item in logical["field_provenance"]
        } == _covered_paths(logical["payload"])
        source_payloads = vector["construction_inputs"]["source_document_payloads"]
        for provenance in logical["field_provenance"]:
            if provenance["derivation_class"] == "S_GUIDANCE":
                assert provenance["source_pointers"] == []
                continue
            source_values = [
                _pointer(
                    source_payloads[pointer["source_document_path"]],
                    pointer["json_pointer"],
                )
                for pointer in provenance["source_pointers"]
            ]
            target = _pointer(logical, provenance["target_json_pointer"])
            algorithm = provenance["algorithm_ref"]
            if algorithm == "R-CACHE-TABLE-COUNT@v1":
                assert target == len(source_values[0])
            elif algorithm == "R-CACHE-TABLE-BINDINGS-DIGEST@v1":
                assert target == canonical_sha256(source_values[0])
            elif algorithm == "R-LINEAGE-EVIDENCE-STATUS-SELECTION@v1":
                assert target == [
                    item
                    for item in source_values[0]
                    if item["source_coordinate"]["dataset_id"] in {"P-D16", "P-D17"}
                    and item["source_type"] == "enum"
                ]
            elif provenance["coverage"] == "VALUE":
                assert target in source_values, provenance["target_json_pointer"]
            elif len(source_values) == 1 and target == source_values[0]:
                continue
            elif len(source_values) == 1:
                assert _identity_sequence(target) == _identity_sequence(
                    source_values[0]
                )
            else:
                assert _identity_sequence(target) == _identity_sequence(source_values)


def test_v11_derives_reseals_and_first_failures_from_private_state() -> None:
    recipes = load_json("negative-mutation-recipes-v2.json")["recipes"]
    fixtures = load_json("negative-fixture-registry-v3.json")["fixtures"]
    fixture_by_recipe = {row[2]: row for row in fixtures}
    assert len(VALIDATOR_RULES) == 41
    resealed = 0
    request_mutated = 0
    for recipe in recipes:
        resolver = LogicalFixtureResolver()
        target_before = resolver.resolve_target(recipe[0], recipe[3])
        seal_before = resolver.context["seal_state"].copy()
        result = resolver.execute_recipe(recipe)
        target_after = resolver.resolve_target(recipe[0], recipe[3])
        fixture = fixture_by_recipe[recipe[0]]

        assert target_after != target_before, recipe[0]
        assert result.changed_targets[0] == recipe[3], recipe[0]
        assert result.first_failure_checkpoint == fixture[6], recipe[0]
        assert result.first_failure_code == fixture[4], recipe[0]
        assert result.validators_executed[-1] == fixture[6], recipe[0]
        assert result.validators_executed.index(recipe[2]) < (
            len(result.validators_executed) - 1
        )
        assert resolver.authority_context == load_json(
            "mutation-positive-context-v3.json"
        )
        if recipe[7] != "NONE":
            assert result.reseal_steps_executed == tuple(
                sorted(result.reseal_steps_executed)
            )
            assert result.reseal_state_changes
            assert resolver.context["seal_state"] != seal_before
            resealed += 1
        else:
            assert result.reseal_steps_executed == ()
            assert result.reseal_state_changes == ()
            assert resolver.context["seal_state"] == seal_before
        if recipe[8] != "NONE":
            assert result.request_mutation_executed == recipe[8]
            request_mutated += 1
            if recipe[8] == "USE_RESEALED_MUTANT_HANDOFF_DIGEST":
                assert resolver.resolve_target(
                    recipe[0], "REQUEST::expected_handoff_digest"
                ).value == resolver.context["seal_state"]["handoff_digest"]
        else:
            assert result.request_mutation_executed is None
    assert len(recipes) == 41
    assert resealed == 17
    assert request_mutated == 15


def test_v11_expected_checkpoint_cannot_drive_observation() -> None:
    recipe = load_json("negative-mutation-recipes-v2.json")["recipes"][0]
    observed = LogicalFixtureResolver().execute_recipe(recipe)
    adversarial = recipe.copy()
    adversarial[9] = "C01_ENTRY"
    adversarial_observed = LogicalFixtureResolver().execute_recipe(adversarial)
    assert (
        adversarial_observed.first_failure_checkpoint
        == observed.first_failure_checkpoint
        == "C01_SOURCE_PACKAGE_VERIFIED"
    )
    assert (
        adversarial_observed.first_failure_code
        == observed.first_failure_code
        == "SOURCE_PACKAGE_VERIFICATION_FAILED"
    )


def test_v11_generated_authorities_are_ascii_lf_and_hash_stable() -> None:
    for name in (
        "metadata-positive-logical-vectors-v4.json",
        "mutation-positive-context-v3.json",
    ):
        payload = (AUTHORITY / name).read_bytes()
        assert payload.endswith(b"\n") and b"\r" not in payload
        payload.decode("ascii")
    metadata = load_json("metadata-positive-logical-vectors-v4.json")
    context = load_json("mutation-positive-context-v3.json")
    assert metadata["vectors"] == build_documents()
    assert context == build_context(metadata["vectors"])
    assert _file_sha256("metadata-positive-logical-vectors-v4.json") == (
        "sha256:bcff1b1aabb2d94ce113178b192b12a6dd7187ff9315d33a2e80728ffaec98e8"
    )
    assert canonical_sha256(metadata) == (
        "sha256:117917c3ebbfb160086ece7c34d665b53cd4fdb9eb59088e393a32246c3dfc23"
    )
    assert _file_sha256("mutation-positive-context-v3.json") == (
        "sha256:60eb028f3a06a90d8bc29dffa50b619632c7bcdd37ea60ed9e51db2c4e0284a2"
    )
    assert canonical_sha256(context) == (
        "sha256:7f529803f4c5b1917628a062587a2cb878da31d4c8adfe0c27909870b7a1d329"
    )
