from __future__ import annotations

import copy
import hashlib
from pathlib import Path
from typing import Any

from finance_assurance.runtime.canonical import canonical_sha256

from .v11_logical_resolver import load_json
from .v12_authority_builder import (
    SEAL_LOCATIONS,
    build_context,
    build_documents,
    compute_seal_values,
    read_seal,
)
from .v12_logical_resolver import SEMANTIC_RULES, LogicalFixtureResolver

ROOT = Path(__file__).parents[2]
AUTHORITY = ROOT / "tests" / "fixtures" / "local-analytical-handoff"


def _file_sha256(name: str) -> str:
    return "sha256:" + hashlib.sha256((AUTHORITY / name).read_bytes()).hexdigest()


def _recipes() -> list[list[Any]]:
    return load_json("negative-mutation-recipes-v2.json")["recipes"]


def _recipe(recipe_ref: str) -> list[Any]:
    return next(row for row in _recipes() if row[0] == recipe_ref)


def test_v12_positive_seals_are_authoritative_and_self_consistent() -> None:
    context = load_json("mutation-positive-context-v4.json")
    assert context["contract_version"] == "handoff-mutation-positive-context@v4"
    assert "seal_state" not in context
    assert set(context["seal_bindings"]) == set(SEAL_LOCATIONS)
    expected = compute_seal_values(context)
    assert set(expected) == set(SEAL_LOCATIONS)
    for key, value in expected.items():
        assert read_seal(context, key) == value
        assert context["seal_bindings"][key].startswith(
            ("SOURCE_MODEL::", "SOURCE_HANDOFF::", "STAGING::")
        )
    assert context["direct_targets"]["REQUEST::expected_model_digest"][
        "value"
    ] == read_seal(context, "r_model_digest")
    assert context["direct_targets"]["REQUEST::expected_handoff_digest"][
        "value"
    ] == read_seal(context, "handoff_digest")
    assert read_seal(context, "r_cache_logical_digest") == read_seal(
        context, "staged_r_cache_logical_digest"
    )


def test_v12_every_clean_reseal_is_idempotent() -> None:
    resolver = LogicalFixtureResolver()
    for reseal_ref, expected_steps in resolver.context["reseal_contracts"].items():
        candidate = LogicalFixtureResolver()
        before = {
            key: copy.deepcopy(read_seal(candidate.context, key))
            for key in SEAL_LOCATIONS
        }
        steps, changes = candidate._execute_reseal(reseal_ref)
        assert steps == expected_steps
        assert changes == [], reseal_ref
        assert {
            key: read_seal(candidate.context, key) for key in SEAL_LOCATIONS
        } == before


def test_v12_derives_all_failures_from_semantic_predicates() -> None:
    fixtures = load_json("negative-fixture-registry-v3.json")["fixtures"]
    fixture_by_recipe = {row[2]: row for row in fixtures}
    assert len(SEMANTIC_RULES) == 41
    resealed = 0
    request_mutated = 0
    for recipe in _recipes():
        resolver = LogicalFixtureResolver()
        authority_before = load_json("mutation-positive-context-v4.json")
        result = resolver.execute_recipe(recipe)
        fixture = fixture_by_recipe[recipe[0]]
        assert result.first_failure_checkpoint == fixture[6], recipe[0]
        assert result.first_failure_code == fixture[4], recipe[0]
        assert result.validators_executed[-1] == fixture[6], recipe[0]
        assert result.validators_executed.index(recipe[2]) < (
            len(result.validators_executed) - 1
        )
        assert resolver.authority_context == authority_before
        if recipe[7] != "NONE":
            assert result.reseal_steps_executed == tuple(
                sorted(result.reseal_steps_executed)
            )
            assert result.reseal_binding_changes
            recomputed = compute_seal_values(resolver.context)
            for key in SEAL_LOCATIONS:
                assert read_seal(resolver.context, key) == recomputed[key]
            resealed += 1
        else:
            assert result.reseal_steps_executed == ()
            assert result.reseal_binding_changes == ()
        if recipe[8] != "NONE":
            assert result.request_mutation_executed == recipe[8]
            request_mutated += 1
            if recipe[8] == "USE_RESEALED_MUTANT_HANDOFF_DIGEST":
                assert resolver.resolve_target(
                    recipe[0], "REQUEST::expected_handoff_digest"
                ).value == read_seal(resolver.context, "handoff_digest")
        else:
            assert result.request_mutation_executed is None
    assert len(_recipes()) == 41
    assert resealed == 17
    assert request_mutated == 15


def test_v12_benign_changes_do_not_inherit_negative_outcomes() -> None:
    capacity = _recipe("XLSX_CAPACITY_OVERFLOW")
    for row_count in (3, 1_048_575):
        benign = capacity.copy()
        benign[6] = f"INTEGER:{row_count}"
        result = LogicalFixtureResolver().execute_recipe(
            benign, require_failure=False
        )
        assert result.first_failure_checkpoint is None
        assert result.first_failure_code is None

    alternate_directory = _recipe("SYMLINK_PATH_ESCAPE").copy()
    alternate_directory[4] = "SET_REQUEST_FIELD"
    alternate_directory[6] = "DIRECTORY:verified-model-copy"
    result = LogicalFixtureResolver().execute_recipe(
        alternate_directory, require_failure=False
    )
    assert result.first_failure_checkpoint is None
    assert result.first_failure_code is None


def test_v12_expected_checkpoint_cannot_drive_semantic_observation() -> None:
    recipe = _recipe("XLSX_CAPACITY_OVERFLOW")
    observed = LogicalFixtureResolver().execute_recipe(recipe)
    adversarial = recipe.copy()
    adversarial[9] = "C01_ENTRY"
    adversarial_observed = LogicalFixtureResolver().execute_recipe(adversarial)
    assert adversarial_observed.first_failure_checkpoint == (
        observed.first_failure_checkpoint
    )
    assert adversarial_observed.first_failure_code == observed.first_failure_code

    benign = adversarial.copy()
    benign[6] = "INTEGER:3"
    benign_observed = LogicalFixtureResolver().execute_recipe(
        benign, require_failure=False
    )
    assert benign_observed.first_failure_checkpoint is None
    assert benign_observed.first_failure_code is None


def test_v12_context_is_ascii_lf_reproducible_and_hash_stable() -> None:
    name = "mutation-positive-context-v4.json"
    payload = (AUTHORITY / name).read_bytes()
    assert payload.endswith(b"\n") and b"\r" not in payload
    payload.decode("ascii")
    context = load_json(name)
    assert context == build_context(build_documents())
    assert _file_sha256("metadata-positive-logical-vectors-v4.json") == (
        "sha256:bcff1b1aabb2d94ce113178b192b12a6dd7187ff9315d33a2e80728ffaec98e8"
    )
    assert _file_sha256(name) == (
        "sha256:323b56bb4089b8ba9415f3890c1656a17908c35e1eed2df3297cf1792cb935b7"
    )
    assert canonical_sha256(context) == (
        "sha256:997e59acd3416dc2645cceb8123de8d43456dca79f0785523261a0e7743292d2"
    )
