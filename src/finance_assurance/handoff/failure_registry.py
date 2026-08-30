"""Closed Artifact S failure, mutation, and negative-fixture registries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from finance_assurance.handoff.authorities import load_json_authority

if TYPE_CHECKING:
    from finance_assurance.handoff.contracts import HandoffOperationFailure


def _records(
    payload: dict[str, Any], field_order_key: str, records_key: str
) -> tuple[dict[str, Any], ...]:
    fields = payload[field_order_key]
    if not isinstance(fields, list) or not all(
        isinstance(item, str) for item in fields
    ):
        raise ValueError(f"{field_order_key} must be a string array")
    records = payload[records_key]
    if not isinstance(records, list):
        raise ValueError(f"{records_key} must be an array")
    output: list[dict[str, Any]] = []
    for row in records:
        if not isinstance(row, list) or len(row) != len(fields):
            raise ValueError(f"{records_key} tuple width does not match field order")
        output.append(dict(zip(fields, row, strict=True)))
    return tuple(output)


@dataclass(frozen=True, slots=True)
class FailureRegistry:
    checkpoints: tuple[dict[str, Any], ...]
    state_vectors: tuple[dict[str, Any], ...]
    digest_presence_vectors: tuple[dict[str, Any], ...]
    admissions: tuple[dict[str, Any], ...]
    fixtures: tuple[dict[str, Any], ...]
    recipes: tuple[dict[str, Any], ...]
    operators: frozenset[str]
    operator_contracts: tuple[dict[str, Any], ...]
    reseal_contracts: dict[str, tuple[str, ...]]
    request_mutation_contracts: dict[str, tuple[str, ...]]

    def recipe_for(self, recipe_ref: str) -> dict[str, Any]:
        matches = tuple(
            item for item in self.recipes if item["recipe_ref"] == recipe_ref
        )
        if len(matches) != 1:
            raise ValueError("mutation recipe reference is not exact")
        return matches[0]

    def operator_contract_for(self, operator: str) -> dict[str, Any]:
        matches = tuple(
            item for item in self.operator_contracts if item["operator"] == operator
        )
        if len(matches) != 1:
            raise ValueError("mutation operator is not exact")
        return matches[0]

    def admission_for(
        self,
        failure_code: str,
        operation: str,
        failure_phase: str,
        failure_checkpoint: str,
    ) -> dict[str, Any]:
        matches = tuple(
            item
            for item in self.admissions
            if (
                item["failure_code"],
                item["operation"],
                item["failure_phase"],
                item["failure_checkpoint"],
            )
            == (failure_code, operation, failure_phase, failure_checkpoint)
        )
        if len(matches) != 1:
            raise ValueError("failure is not one exact Artifact S admission")
        return matches[0]

    def validate_failure(self, failure: HandoffOperationFailure) -> None:
        admission = self.admission_for(
            failure.failure_code,
            failure.operation,
            failure.failure_phase,
            failure.failure_checkpoint,
        )
        state = next(
            item
            for item in self.state_vectors
            if item["state_vector_ref"] == admission["state_vector_ref"]
        )
        for field in (
            "canonical_byte_status",
            "same_build_binary_status",
            "logical_equivalence_status",
            "staging_removed",
            "source_package_path_state",
            "source_model_path_state",
            "source_handoff_path_state",
            "output_path_state",
        ):
            if getattr(failure, field) != state[field]:
                raise ValueError(f"{field} does not match the admitted state vector")
        digest_vector = next(
            item
            for item in self.digest_presence_vectors
            if item["digest_presence_ref"] == admission["digest_presence_ref"]
        )
        for field in (
            "expected_handoff_digest",
            "actual_handoff_digest",
            "expected_model_digest",
            "actual_model_digest",
            "expected_source_package_digest",
            "actual_source_package_digest",
        ):
            expected_presence = digest_vector[field]
            actual_presence = "NULL" if getattr(failure, field) is None else "PRESENT"
            if actual_presence != expected_presence:
                raise ValueError(f"{field} does not match admitted digest presence")


def _load_registry() -> FailureRegistry:
    try:
        failure = load_json_authority("operation-failure-state-registry-v1.json")
        fixture = load_json_authority("negative-fixture-registry-v2.json")
        mutation = load_json_authority("negative-mutation-recipes-v1.json")
    except FileNotFoundError:
        # Forensic recovery mode: the generated authority files are rebuilt from
        # the original release during the recovery validation pass. Keep imports
        # usable without silently asserting the missing registries are valid.
        return FailureRegistry((), (), (), (), (), (), frozenset(), (), {}, {})
    checkpoints = _records(failure, "checkpoint_field_order", "checkpoints")
    states = _records(failure, "state_vector_field_order", "state_vectors")
    digests = _records(
        failure, "digest_presence_field_order", "digest_presence_vectors"
    )
    admissions = _records(failure, "admission_field_order", "admissions")
    fixtures = _records(fixture, "field_order", "fixtures")
    recipes = _records(mutation, "recipe_field_order", "recipes")
    operators = frozenset(mutation["operator_vocabulary"])
    operator_contracts = _records(
        mutation, "operator_contract_field_order", "operator_contracts"
    )
    reseal_contracts = {
        key: tuple(value) for key, value in mutation["reseal_contracts"].items()
    }
    request_mutation_contracts = {
        key: tuple(value)
        for key, value in mutation["request_mutation_contracts"].items()
    }

    checkpoint_ordinals = tuple(item["ordinal"] for item in checkpoints)
    if len(checkpoints) != 90 or checkpoint_ordinals != tuple(range(1, 91)):
        raise ValueError("failure checkpoints must have exact ordinals 1 through 90")
    checkpoint_by_ref = {item["checkpoint_ref"]: item for item in checkpoints}
    state_by_ref = {item["state_vector_ref"]: item for item in states}
    digest_by_ref = {item["digest_presence_ref"]: item for item in digests}
    if (
        len(checkpoint_by_ref) != 90
        or len(state_by_ref) != 28
        or len(digest_by_ref) != 10
    ):
        raise ValueError("failure checkpoint or vector registry is not exact")
    admission_keys = {
        (
            item["failure_code"],
            item["operation"],
            item["failure_phase"],
            item["failure_checkpoint"],
            item["state_vector_ref"],
            item["digest_presence_ref"],
        )
        for item in admissions
    }
    if len(admissions) != 80 or len(admission_keys) != 80:
        raise ValueError("failure admission registry must contain 80 unique rows")
    for admission in admissions:
        checkpoint = checkpoint_by_ref[admission["failure_checkpoint"]]
        if (checkpoint["operation"], checkpoint["failure_phase"]) != (
            admission["operation"],
            admission["failure_phase"],
        ):
            raise ValueError("admission checkpoint operation or phase differs")
        state_by_ref[admission["state_vector_ref"]]
        digest_by_ref[admission["digest_presence_ref"]]

    recipe_by_ref = {item["recipe_ref"]: item for item in recipes}
    if (
        len(fixtures) != 41
        or len(recipe_by_ref) != 41
        or len(operators) != 19
        or len(operator_contracts) != 19
    ):
        raise ValueError("negative fixture, recipe, or operator inventory is not exact")
    if {item["operator"] for item in operator_contracts} != operators:
        raise ValueError("operator vocabulary and contracts differ")
    if {item["reseal_steps"] for item in recipes} != set(reseal_contracts):
        raise ValueError("recipe resealing reference is not exact")
    if {item["request_mutation_ref"] for item in recipes} != set(
        request_mutation_contracts
    ):
        raise ValueError("recipe request-mutation reference is not exact")
    fixture_admissions: set[tuple[str, str, str, str]] = set()
    fixture_codes: set[str] = set()
    checkpoint_ordinals = {
        item["checkpoint_ref"]: item["ordinal"] for item in checkpoints
    }
    for item in fixtures:
        matching = tuple(
            admission
            for admission in admissions
            if (
                admission["failure_code"],
                admission["operation"],
                admission["failure_phase"],
                admission["failure_checkpoint"],
            )
            == (
                item["expected_failure_code"],
                item["operation"],
                item["expected_phase"],
                item["expected_checkpoint"],
            )
        )
        if len(matching) != 1:
            raise ValueError(f"{item['fixture_id']} does not resolve one admission")
        admission = matching[0]
        state = state_by_ref[admission["state_vector_ref"]]
        for field in failure["state_vector_field_order"][1:]:
            if item[field] != state[field]:
                raise ValueError(f"{item['fixture_id']} differs from its state vector")
        recipe = recipe_by_ref[item["mutation_recipe_ref"]]
        if (
            recipe["operation"],
            recipe["request_mutation_ref"],
            recipe["expected_first_failure_checkpoint"],
        ) != (
            item["operation"],
            item["request_mutation_ref"],
            item["expected_checkpoint"],
        ):
            raise ValueError(f"{item['fixture_id']} recipe binding differs")
        if recipe["operator"] not in operators:
            raise ValueError(f"{item['fixture_id']} uses an unknown operator")
        if checkpoint_ordinals[recipe["apply_after_checkpoint"]] >= checkpoint_ordinals[
            recipe["expected_first_failure_checkpoint"]
        ]:
            raise ValueError(f"{item['fixture_id']} mutation is not applied earlier")
        fixture_admissions.add(
            (
                admission["failure_code"],
                admission["operation"],
                admission["failure_phase"],
                admission["failure_checkpoint"],
            )
        )
        fixture_codes.add(admission["failure_code"])
    if len(fixture_admissions) != 34 or len(fixture_codes) != 20:
        raise ValueError("fixture subset must cover 34 admissions and 20 codes")
    return FailureRegistry(
        checkpoints=checkpoints,
        state_vectors=states,
        digest_presence_vectors=digests,
        admissions=admissions,
        fixtures=fixtures,
        recipes=recipes,
        operators=operators,
        operator_contracts=operator_contracts,
        reseal_contracts=reseal_contracts,
        request_mutation_contracts=request_mutation_contracts,
    )


FAILURE_REGISTRY = _load_registry()
