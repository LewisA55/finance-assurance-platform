"""State-derived private execution harness for bounded Artifact S v0.11."""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finance_assurance.handoff import split_sql_authority
from finance_assurance.runtime.canonical import canonical_sha256

from .v10_authority_builder import (
    DUCKDB_AMOUNT_TARGET,
    SOURCE_PACKAGE_AMOUNT_TARGET,
    STAGING_DUCKDB_AMOUNT_TARGET,
    XLSX_AMOUNT_TARGET,
    XLSX_CORE_TARGET,
    XLSX_EXTERNAL_LINK_TARGET,
    XLSX_NULL_TARGET,
)
from .v10_logical_resolver import LogicalFixtureResolver as V10Resolver
from .v10_logical_resolver import LogicalValue
from .v11_authority_builder import _component_preimage

ROOT = Path(__file__).parents[2]
AUTHORITY = ROOT / "tests" / "fixtures" / "local-analytical-handoff"


def load_json(name: str) -> dict[str, Any]:
    return json.loads((AUTHORITY / name).read_text(encoding="ascii"))


@dataclass(frozen=True, slots=True)
class CheckpointRule:
    operation: str
    checkpoint_ref: str
    failure_code: str
    target_ref: str
    required_kind: str | None = None


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    recipe_ref: str
    changed_targets: tuple[str, ...]
    reseal_steps_executed: tuple[str, ...]
    reseal_state_changes: tuple[str, ...]
    request_mutation_executed: str | None
    validators_executed: tuple[str, ...]
    first_failure_checkpoint: str
    first_failure_code: str


VALIDATOR_RULES = (
    CheckpointRule(
        "S-C01",
        "C01_SOURCE_PACKAGE_VERIFIED",
        "SOURCE_PACKAGE_VERIFICATION_FAILED",
        SOURCE_PACKAGE_AMOUNT_TARGET,
    ),
    CheckpointRule(
        "S-C01",
        "C01_SOURCE_MODEL_VERIFIED",
        "MODEL_VERIFICATION_FAILED",
        "SOURCE_MODEL::schemas/p-evidence-v1/P-D06.schema.json",
    ),
    CheckpointRule(
        "S-C02",
        "C02_R3_CACHE_VERIFIED",
        "R3_CACHE_INVALID",
        DUCKDB_AMOUNT_TARGET,
    ),
    CheckpointRule(
        "S-C02",
        "C02_PACKAGE_INVENTORY_VERIFIED",
        "INVENTORY_MISMATCH",
        "SOURCE_HANDOFF::handoff-manifest.json#/handoff_digest",
    ),
    CheckpointRule(
        "S-C02",
        "C02_XLSX_LOGICAL_VERIFIED",
        "XLSX_LOGICAL_MISMATCH",
        XLSX_AMOUNT_TARGET,
        "INTEGER_NUMERIC",
    ),
    CheckpointRule(
        "S-C02",
        "C02_XLSX_LOGICAL_VERIFIED",
        "XLSX_LOGICAL_MISMATCH",
        XLSX_NULL_TARGET,
    ),
    CheckpointRule(
        "S-C02",
        "C02_XLSX_STRUCTURE_VERIFIED",
        "XLSX_STRUCTURE_INVALID",
        XLSX_AMOUNT_TARGET,
        "FORMULA",
    ),
    CheckpointRule(
        "S-C02",
        "C02_XLSX_STRUCTURE_VERIFIED",
        "XLSX_STRUCTURE_INVALID",
        XLSX_EXTERNAL_LINK_TARGET,
    ),
    CheckpointRule(
        "S-C02",
        "C02_METADATA_VERIFIED",
        "METADATA_DERIVATION_MISMATCH",
        "SOURCE_HANDOFF::metadata/data-dictionary.json#/source_datasets/5/logical_table_digest",
    ),
    CheckpointRule(
        "S-C02",
        "C02_METADATA_VERIFIED",
        "METADATA_DERIVATION_MISMATCH",
        "SOURCE_HANDOFF::metadata/lineage.json#/field_provenance/0/source_pointers",
    ),
    CheckpointRule(
        "S-C02",
        "C02_VALIDATION_REGISTRY_VERIFIED",
        "VALIDATION_REGISTRY_MISMATCH",
        "SOURCE_HANDOFF::metadata/validation-checks.json#/payload/checks/0/assertions/0/kind",
    ),
    CheckpointRule(
        "S-C02",
        "C02_SQL_REGISTRY_VERIFIED",
        "SQL_REGISTRY_MISMATCH",
        "SOURCE_HANDOFF::examples/reconciliation-queries.sql::S-QV03",
    ),
    CheckpointRule(
        "S-C02",
        "C02_SQL_REGISTRY_VERIFIED",
        "SQL_REGISTRY_MISMATCH",
        "SOURCE_HANDOFF::examples/starter-queries.sql::S-QS01",
    ),
    CheckpointRule(
        "S-C02",
        "C02_VALIDATION_REGISTRY_VERIFIED",
        "VALIDATION_REGISTRY_MISMATCH",
        "SOURCE_HANDOFF::metadata/validation-checks.json#/payload/checks/10/assertions/0/left/selector_ref",
    ),
    CheckpointRule(
        "S-C02",
        "C02_VALIDATION_REGISTRY_VERIFIED",
        "VALIDATION_REGISTRY_MISMATCH",
        "SOURCE_HANDOFF::metadata/validation-checks.json#/payload/checks/11/assertions/0/direction",
    ),
    CheckpointRule(
        "S-C02",
        "C02_PACKAGE_INVENTORY_VERIFIED",
        "INVENTORY_MISMATCH",
        "SOURCE_HANDOFF::unexpected.txt",
    ),
    CheckpointRule(
        "S-C01",
        "C01_PATH_FIREWALL_PASSED",
        "PATH_FIREWALL_VIOLATION",
        "REQUEST::source_model_path",
    ),
    CheckpointRule(
        "S-C01",
        "C01_OUTPUT_ABSENCE_VERIFIED",
        "OUTPUT_OCCUPIED",
        "REQUEST::output_path",
    ),
    CheckpointRule(
        "S-C01",
        "C01_PUBLICATION_RENAME_COMPLETED",
        "ATOMIC_PUBLICATION_FAILED",
        "RUNTIME::atomic_rename(staging_path,output_path)",
    ),
    CheckpointRule(
        "S-C01",
        "C01_WRITER_PROFILE_RESOLVED",
        "XLSX_PROFILE_UNAVAILABLE",
        "REQUEST::xlsx_writer_profile_ref",
    ),
    CheckpointRule(
        "S-C01",
        "C01_SOURCE_R3_CACHE_VERIFIED",
        "R3_CACHE_INVALID",
        "SOURCE_MODEL::noncanonical-cache.json#/profile_coordinate/profile_version",
    ),
    CheckpointRule(
        "S-C01",
        "C01_XLSX_CAPACITY_VERIFIED",
        "XLSX_CAPACITY_EXCEEDED",
        "SOURCE_MODEL::model-manifest.json#/table_entries/5/row_count",
    ),
    CheckpointRule(
        "S-C03",
        "C03_SOURCE_VALIDATION_REGISTRY_VERIFIED",
        "VALIDATION_REGISTRY_MISMATCH",
        "SOURCE_HANDOFF::metadata/validation-checks.json#/payload/checks/0/assertions/0/expected/value",
    ),
    CheckpointRule(
        "S-C03",
        "C03_SOURCE_PACKAGE_PATH_RESOLVED",
        "SOURCE_PACKAGE_UNAVAILABLE",
        "REQUEST::source_package_path",
    ),
    CheckpointRule(
        "S-C03",
        "C03_REPRO_R3_CACHE_VERIFIED",
        "R3_CACHE_INVALID",
        STAGING_DUCKDB_AMOUNT_TARGET,
    ),
    CheckpointRule(
        "S-C03",
        "C03_SOURCE_WRITER_PROFILE_RESOLVED",
        "XLSX_PROFILE_UNAVAILABLE",
        "RUNTIME::xlsx_writer_profile/XLSXWRITER-3.2.9@v1",
    ),
    CheckpointRule(
        "S-C03",
        "C03_REPRO_CANONICAL_DIGEST_VERIFIED",
        "DIGEST_MISMATCH",
        "STAGING::limitations.json#/limitations",
    ),
    CheckpointRule(
        "S-C03",
        "C03_OUTPUT_ABSENCE_VERIFIED",
        "OUTPUT_OCCUPIED",
        "REQUEST::reproduction_output_path",
    ),
    CheckpointRule(
        "S-C03",
        "C03_REPRO_SOURCE_PACKAGE_AVAILABLE",
        "SOURCE_PACKAGE_UNAVAILABLE",
        "REQUEST::source_package_path",
    ),
    CheckpointRule(
        "S-C01",
        "C01_STAGE_CREATE_STARTED",
        "BUILD_FAILED",
        "RUNTIME::create_staging_directory",
    ),
    CheckpointRule(
        "S-C01",
        "C01_COPY_STARTED",
        "BUILD_FAILED",
        "RUNTIME::copy_source_model",
    ),
    CheckpointRule(
        "S-C01",
        "C01_DERIVATION_STARTED",
        "BUILD_FAILED",
        "RUNTIME::derive_metadata_and_sql",
    ),
    CheckpointRule(
        "S-C01",
        "C01_XLSX_WRITE_STARTED",
        "BUILD_FAILED",
        "RUNTIME::write_xlsx_projection",
    ),
    CheckpointRule(
        "S-C01",
        "C01_SEAL_STARTED",
        "BUILD_FAILED",
        "RUNTIME::seal_staged_handoff",
    ),
    CheckpointRule(
        "S-C01",
        "C01_STAGED_VERIFY_STARTED",
        "BUILD_FAILED",
        "RUNTIME::verify_staged_handoff",
    ),
    CheckpointRule(
        "S-C02",
        "C02_VERIFY_STARTED",
        "BUILD_FAILED",
        "RUNTIME::verify_source_handoff",
    ),
    CheckpointRule(
        "S-C03",
        "C03_REPRODUCTION_STARTED",
        "BUILD_FAILED",
        "RUNTIME::reproduce_handoff",
    ),
    CheckpointRule(
        "S-C01",
        "C01_REQUEST_PARSED",
        "INVALID_REQUEST",
        "REQUEST::expected_model_digest",
    ),
    CheckpointRule(
        "S-C01",
        "C01_SOURCE_COPY_STABILITY_VERIFIED",
        "SOURCE_CHANGED_DURING_COPY",
        "SOURCE_MODEL::model-manifest.json",
    ),
    CheckpointRule(
        "S-C02",
        "C02_NONCANONICAL_BINARY_VERIFIED",
        "NONCANONICAL_BINARY_MISMATCH",
        XLSX_CORE_TARGET,
    ),
    CheckpointRule(
        "S-C03",
        "C03_SOURCE_VERIFY_STARTED",
        "BUILD_FAILED",
        "RUNTIME::verify_source_handoff",
    ),
)


class LogicalFixtureResolver(V10Resolver):
    def __init__(self) -> None:
        self.authority_context = load_json("mutation-positive-context-v3.json")
        self.context = copy.deepcopy(self.authority_context)
        vectors = load_json("metadata-positive-logical-vectors-v4.json")["vectors"]
        self.documents = {item["vector_ref"]: item["document"] for item in vectors}
        self.queries = {
            query_id: sql
            for filename in ("starter-queries-v1.sql", "reconciliation-queries-v1.sql")
            for query_id, sql in split_sql_authority(filename)
        }
        failures = load_json("operation-failure-state-registry-v1.json")
        self.checkpoints = sorted(
            (
                {
                    "checkpoint_ref": row[0],
                    "operation": row[1],
                    "failure_phase": row[2],
                    "ordinal": row[3],
                }
                for row in failures["checkpoints"]
            ),
            key=lambda item: (item["operation"], item["ordinal"]),
        )

    def _safe_resolve(self, recipe_ref: str, target_ref: str) -> LogicalValue:
        try:
            return self.resolve_target(recipe_ref, target_ref)
        except KeyError:
            return LogicalValue("ABSENT", None)

    def _validator_baselines(
        self, recipe_ref: str, operation: str
    ) -> dict[str, LogicalValue]:
        return {
            rule.target_ref: copy.deepcopy(
                self._safe_resolve(recipe_ref, rule.target_ref)
            )
            for rule in VALIDATOR_RULES
            if rule.operation == operation
        }

    def _validate_checkpoint(
        self,
        recipe_ref: str,
        operation: str,
        checkpoint_ref: str,
        baselines: dict[str, LogicalValue],
    ) -> str | None:
        for rule in VALIDATOR_RULES:
            actual = self._safe_resolve(recipe_ref, rule.target_ref)
            if (
                rule.operation == operation
                and rule.checkpoint_ref == checkpoint_ref
                and actual != baselines[rule.target_ref]
                and (rule.required_kind is None or actual.kind == rule.required_kind)
            ):
                return rule.failure_code
        return None

    def execute_recipe(self, recipe: list[Any]) -> ExecutionResult:
        recipe_ref = recipe[0]
        operation = recipe[1]
        apply_after_checkpoint = recipe[2]
        target_ref = recipe[3]
        operator = recipe[4]
        before_ref = recipe[5]
        mutation_ref = recipe[6]
        reseal_ref = recipe[7]
        request_mutation_ref = recipe[8]

        target = self.resolve_target(recipe_ref, target_ref)
        before = self.resolve_before(recipe_ref, before_ref, target)
        if before != target:
            raise AssertionError(f"{recipe_ref} before-state mismatch")
        baselines = self._validator_baselines(recipe_ref, operation)
        operation_checkpoints = [
            item for item in self.checkpoints if item["operation"] == operation
        ]
        validators: list[str] = []
        changed_targets: list[str] = []
        reseal_steps: list[str] = []
        reseal_changes: list[str] = []
        request_mutation: str | None = None
        mutation_applied = False

        for checkpoint in operation_checkpoints:
            checkpoint_ref = checkpoint["checkpoint_ref"]
            validators.append(checkpoint_ref)
            failure_code = self._validate_checkpoint(
                recipe_ref, operation, checkpoint_ref, baselines
            )
            if failure_code is not None:
                if not mutation_applied:
                    raise AssertionError(f"{recipe_ref} failed before mutation")
                return ExecutionResult(
                    recipe_ref=recipe_ref,
                    changed_targets=tuple(changed_targets),
                    reseal_steps_executed=tuple(reseal_steps),
                    reseal_state_changes=tuple(reseal_changes),
                    request_mutation_executed=request_mutation,
                    validators_executed=tuple(validators),
                    first_failure_checkpoint=checkpoint_ref,
                    first_failure_code=failure_code,
                )
            if checkpoint_ref == apply_after_checkpoint:
                changed_targets.append(
                    self._apply_mutation(
                        recipe_ref, target_ref, operator, mutation_ref
                    )
                )
                reseal_steps, reseal_changes = self._execute_reseal(reseal_ref)
                request_mutation = self._execute_request_mutation(
                    request_mutation_ref
                )
                if request_mutation is not None:
                    changed_targets.append(
                        self.context["request_mutations"][request_mutation][
                            "target_ref"
                        ]
                    )
                mutation_applied = True
        raise AssertionError(f"{recipe_ref} produced no state-derived failure")

    def _set_seal(self, key: str, value: str, changed: list[str]) -> None:
        if self.context["seal_state"][key] != value:
            self.context["seal_state"][key] = value
            changed.append(key)

    def _execute_reseal(self, reseal_ref: str) -> tuple[list[str], list[str]]:
        if reseal_ref == "NONE":
            return [], []
        steps = self.context["reseal_contracts"][reseal_ref]
        if steps != sorted(steps):
            raise AssertionError(f"{reseal_ref} steps are not lexical")
        changed: list[str] = []
        state = self.context["seal_state"]
        for step in steps:
            if step in {
                "R01_RECOMPUTE_CACHE_LOGICAL",
                "C01_RECOMPUTE_CACHE_LOGICAL",
            }:
                self._set_seal(
                    "r_cache_logical_digest",
                    canonical_sha256(_component_preimage(self.context, "R_CACHE")),
                    changed,
                )
            elif step in {
                "R02_REWRITE_CACHE_MANIFEST",
                "C02_REWRITE_CACHE_MANIFEST",
            }:
                self._set_seal(
                    "r_cache_manifest_digest",
                    canonical_sha256(
                        {"r_cache": state["r_cache_logical_digest"]}
                    ),
                    changed,
                )
            elif step == "R03_REWRITE_S_NONCANONICAL_MANIFEST":
                self._set_seal(
                    "s_noncanonical_manifest_digest",
                    canonical_sha256(
                        {
                            "r_cache": state["r_cache_manifest_digest"],
                            "xlsx": state["xlsx_binary_digest"],
                        }
                    ),
                    changed,
                )
            elif step == "R04_RETAIN_CANONICAL_HANDOFF_DIGEST":
                canonical_sha256({"retained": state["handoff_digest"]})
            elif step == "S01_CANONICALIZE_CHANGED_AUTHORITIES":
                self._set_seal(
                    "s_canonical_digest",
                    canonical_sha256(
                        _component_preimage(self.context, "S_CANONICAL")
                    ),
                    changed,
                )
            elif step == "S02_RECOMPUTE_CANONICAL_CHECKSUMS":
                self._set_seal(
                    "s_checksums_digest",
                    canonical_sha256(
                        {"s_canonical": state["s_canonical_digest"]}
                    ),
                    changed,
                )
            elif step == "S03_RECOMPUTE_HANDOFF_DIGEST":
                self._set_seal(
                    "handoff_digest",
                    canonical_sha256({"checksums": state["s_checksums_digest"]}),
                    changed,
                )
            elif step == "X01_RECOMPUTE_XLSX_BINARY_DIGEST":
                self._set_seal(
                    "xlsx_binary_digest",
                    canonical_sha256(_component_preimage(self.context, "XLSX")),
                    changed,
                )
            elif step == "X02_RECOMPUTE_XLSX_LOGICAL_DIGEST":
                self._set_seal(
                    "xlsx_logical_digest",
                    canonical_sha256({"xlsx": state["xlsx_binary_digest"]}),
                    changed,
                )
            elif step == "X03_REWRITE_XLSX_NONCANONICAL_MANIFEST":
                self._set_seal(
                    "s_noncanonical_manifest_digest",
                    canonical_sha256(
                        {
                            "r_cache": state["r_cache_manifest_digest"],
                            "xlsx_binary": state["xlsx_binary_digest"],
                            "xlsx_logical": state["xlsx_logical_digest"],
                        }
                    ),
                    changed,
                )
            elif step == "X04_RETAIN_CANONICAL_HANDOFF_DIGEST":
                canonical_sha256({"retained": state["handoff_digest"]})
            elif step == "M01_CANONICALIZE_R_MANIFEST":
                self._set_seal(
                    "r_model_canonical_digest",
                    canonical_sha256(_component_preimage(self.context, "R_MODEL")),
                    changed,
                )
            elif step == "M02_RECOMPUTE_R_CHECKSUMS":
                self._set_seal(
                    "r_model_checksums_digest",
                    canonical_sha256(
                        {"r_model": state["r_model_canonical_digest"]}
                    ),
                    changed,
                )
            elif step == "M03_RECOMPUTE_R_MODEL_DIGEST":
                self._set_seal(
                    "r_model_digest",
                    canonical_sha256(
                        {"r_checksums": state["r_model_checksums_digest"]}
                    ),
                    changed,
                )
            elif step == "T01_CANONICALIZE_STAGED_JSON":
                self._set_seal(
                    "staged_canonical_digest",
                    canonical_sha256(
                        _component_preimage(self.context, "STAGED_CANONICAL")
                    ),
                    changed,
                )
            elif step == "T02_RECOMPUTE_STAGED_CHECKSUMS":
                self._set_seal(
                    "staged_checksums_digest",
                    canonical_sha256(
                        {"staged": state["staged_canonical_digest"]}
                    ),
                    changed,
                )
            elif step == "T03_RECOMPUTE_STAGED_HANDOFF_DIGEST":
                self._set_seal(
                    "staged_handoff_digest",
                    canonical_sha256(
                        {"checksums": state["staged_checksums_digest"]}
                    ),
                    changed,
                )
            else:
                raise AssertionError(f"unknown reseal step: {step}")
        self.context.setdefault("executed_reseals", []).append(
            {
                "reseal_ref": reseal_ref,
                "steps": list(steps),
                "changed_seal_state_keys": list(changed),
            }
        )
        return list(steps), changed

    def _execute_request_mutation(self, request_mutation_ref: str) -> str | None:
        if request_mutation_ref == "NONE":
            return None
        spec = self.context["request_mutations"][request_mutation_ref]
        mutation = spec["mutation"]
        if mutation == "TEXT:CURRENT_RESEALED_HANDOFF_DIGEST":
            mutation = "TEXT:" + self.context["seal_state"]["handoff_digest"]
        self._apply_mutation(
            request_mutation_ref,
            spec["target_ref"],
            spec["operator"],
            mutation,
        )
        return request_mutation_ref
