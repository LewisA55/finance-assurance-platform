"""Semantic private execution harness for bounded Artifact S v0.12."""

from __future__ import annotations

import copy
import re
from dataclasses import dataclass
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
from .v10_logical_resolver import LogicalValue
from .v11_logical_resolver import LogicalFixtureResolver as V11Resolver
from .v11_logical_resolver import load_json
from .v12_authority_builder import (
    _noncanonical_manifest_value,
    _r_cache_values,
    _r_model_values,
    _s_canonical_values,
    _staged_r_cache_values,
    _staged_values,
    _xlsx_values,
    read_seal,
    seal_target_ref,
)


@dataclass(frozen=True, slots=True)
class SemanticRule:
    operation: str
    checkpoint_ref: str
    failure_code: str
    target_ref: str
    predicate_ref: str


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    recipe_ref: str
    changed_targets: tuple[str, ...]
    reseal_steps_executed: tuple[str, ...]
    reseal_binding_changes: tuple[str, ...]
    request_mutation_executed: str | None
    validators_executed: tuple[str, ...]
    first_failure_checkpoint: str | None
    first_failure_code: str | None


SEMANTIC_RULES = (
    SemanticRule("S-C01", "C01_SOURCE_PACKAGE_VERIFIED", "SOURCE_PACKAGE_VERIFICATION_FAILED", SOURCE_PACKAGE_AMOUNT_TARGET, "MATCH_VERIFIED_PACKAGE_VALUE"),
    SemanticRule("S-C01", "C01_SOURCE_MODEL_VERIFIED", "MODEL_VERIFICATION_FAILED", "SOURCE_MODEL::schemas/p-evidence-v1/P-D06.schema.json", "MATCH_MANIFEST_FILE_HASH"),
    SemanticRule("S-C02", "C02_R3_CACHE_VERIFIED", "R3_CACHE_INVALID", DUCKDB_AMOUNT_TARGET, "CACHE_EQUALS_VERIFIED_PACKAGE"),
    SemanticRule("S-C02", "C02_PACKAGE_INVENTORY_VERIFIED", "INVENTORY_MISMATCH", "SOURCE_HANDOFF::handoff-manifest.json#/handoff_digest", "FORBID_RECURSIVE_HANDOFF_DIGEST"),
    SemanticRule("S-C02", "C02_XLSX_LOGICAL_VERIFIED", "XLSX_LOGICAL_MISMATCH", XLSX_AMOUNT_TARGET, "XLSX_INTEGER_REPRESENTATION_SAFE"),
    SemanticRule("S-C02", "C02_XLSX_LOGICAL_VERIFIED", "XLSX_LOGICAL_MISMATCH", XLSX_NULL_TARGET, "XLSX_NULL_CELL_ABSENT"),
    SemanticRule("S-C02", "C02_XLSX_STRUCTURE_VERIFIED", "XLSX_STRUCTURE_INVALID", XLSX_AMOUNT_TARGET, "XLSX_FORMULA_FREE"),
    SemanticRule("S-C02", "C02_XLSX_STRUCTURE_VERIFIED", "XLSX_STRUCTURE_INVALID", XLSX_EXTERNAL_LINK_TARGET, "XLSX_EXTERNAL_LINK_FREE"),
    SemanticRule("S-C02", "C02_METADATA_VERIFIED", "METADATA_DERIVATION_MISMATCH", "SOURCE_HANDOFF::metadata/data-dictionary.json#/source_datasets/5/logical_table_digest", "METADATA_DIGEST_MATCHES_MODEL"),
    SemanticRule("S-C02", "C02_METADATA_VERIFIED", "METADATA_DERIVATION_MISMATCH", "SOURCE_HANDOFF::metadata/lineage.json#/field_provenance/0/source_pointers", "PROVENANCE_MATCHES_AUTHENTICATED_MAPPING"),
    SemanticRule("S-C02", "C02_VALIDATION_REGISTRY_VERIFIED", "VALIDATION_REGISTRY_MISMATCH", "SOURCE_HANDOFF::metadata/validation-checks.json#/payload/checks/0/assertions/0/kind", "VALIDATION_ASSERTION_KIND_AUTHORISED"),
    SemanticRule("S-C02", "C02_SQL_REGISTRY_VERIFIED", "SQL_REGISTRY_MISMATCH", "SOURCE_HANDOFF::examples/reconciliation-queries.sql::S-QV03", "SQL_QUERY_MATCHES_AUTHORITY"),
    SemanticRule("S-C02", "C02_SQL_REGISTRY_VERIFIED", "SQL_REGISTRY_MISMATCH", "SOURCE_HANDOFF::examples/starter-queries.sql::S-QS01", "SQL_QUERY_MATCHES_AUTHORITY"),
    SemanticRule("S-C02", "C02_VALIDATION_REGISTRY_VERIFIED", "VALIDATION_REGISTRY_MISMATCH", "SOURCE_HANDOFF::metadata/validation-checks.json#/payload/checks/10/assertions/0/left/selector_ref", "VALIDATION_SELECTOR_MATCHES_AUTHORITY"),
    SemanticRule("S-C02", "C02_VALIDATION_REGISTRY_VERIFIED", "VALIDATION_REGISTRY_MISMATCH", "SOURCE_HANDOFF::metadata/validation-checks.json#/payload/checks/11/assertions/0/direction", "TRACE_DIRECTION_SOURCE_TO_TARGET"),
    SemanticRule("S-C02", "C02_PACKAGE_INVENTORY_VERIFIED", "INVENTORY_MISMATCH", "SOURCE_HANDOFF::unexpected.txt", "PACKAGE_PATH_ABSENT"),
    SemanticRule("S-C01", "C01_PATH_FIREWALL_PASSED", "PATH_FIREWALL_VIOLATION", "REQUEST::source_model_path", "SOURCE_PATH_IS_DIRECTORY"),
    SemanticRule("S-C01", "C01_OUTPUT_ABSENCE_VERIFIED", "OUTPUT_OCCUPIED", "REQUEST::output_path", "OUTPUT_PATH_ABSENT"),
    SemanticRule("S-C01", "C01_PUBLICATION_RENAME_COMPLETED", "ATOMIC_PUBLICATION_FAILED", "RUNTIME::atomic_rename(staging_path,output_path)", "RUNTIME_CALLABLE"),
    SemanticRule("S-C01", "C01_WRITER_PROFILE_RESOLVED", "XLSX_PROFILE_UNAVAILABLE", "REQUEST::xlsx_writer_profile_ref", "WRITER_PROFILE_SUPPORTED"),
    SemanticRule("S-C01", "C01_SOURCE_R3_CACHE_VERIFIED", "R3_CACHE_INVALID", "SOURCE_MODEL::noncanonical-cache.json#/profile_coordinate/profile_version", "CACHE_PROFILE_VERSION_MATCHES"),
    SemanticRule("S-C01", "C01_XLSX_CAPACITY_VERIFIED", "XLSX_CAPACITY_EXCEEDED", "SOURCE_MODEL::model-manifest.json#/table_entries/5/row_count", "XLSX_CAPACITY_WITHIN_LIMIT"),
    SemanticRule("S-C03", "C03_SOURCE_VALIDATION_REGISTRY_VERIFIED", "VALIDATION_REGISTRY_MISMATCH", "SOURCE_HANDOFF::metadata/validation-checks.json#/payload/checks/0/assertions/0/expected/value", "VALIDATION_EXPECTED_VALUE_MATCHES_AUTHORITY"),
    SemanticRule("S-C03", "C03_SOURCE_PACKAGE_PATH_RESOLVED", "SOURCE_PACKAGE_UNAVAILABLE", "REQUEST::source_package_path", "SOURCE_PACKAGE_IS_DIRECTORY"),
    SemanticRule("S-C03", "C03_REPRO_R3_CACHE_VERIFIED", "R3_CACHE_INVALID", STAGING_DUCKDB_AMOUNT_TARGET, "REPRO_CACHE_EQUALS_SOURCE_CACHE"),
    SemanticRule("S-C03", "C03_SOURCE_WRITER_PROFILE_RESOLVED", "XLSX_PROFILE_UNAVAILABLE", "RUNTIME::xlsx_writer_profile/XLSXWRITER-3.2.9@v1", "WRITER_RUNTIME_AVAILABLE"),
    SemanticRule("S-C03", "C03_REPRO_CANONICAL_DIGEST_VERIFIED", "DIGEST_MISMATCH", "STAGING::limitations.json#/limitations", "REPRO_DIGEST_MATCHES_POSITIVE"),
    SemanticRule("S-C03", "C03_OUTPUT_ABSENCE_VERIFIED", "OUTPUT_OCCUPIED", "REQUEST::reproduction_output_path", "OUTPUT_PATH_ABSENT"),
    SemanticRule("S-C03", "C03_REPRO_SOURCE_PACKAGE_AVAILABLE", "SOURCE_PACKAGE_UNAVAILABLE", "REQUEST::source_package_path", "SOURCE_PACKAGE_IS_DIRECTORY"),
    SemanticRule("S-C01", "C01_STAGE_CREATE_STARTED", "BUILD_FAILED", "RUNTIME::create_staging_directory", "RUNTIME_CALLABLE"),
    SemanticRule("S-C01", "C01_COPY_STARTED", "BUILD_FAILED", "RUNTIME::copy_source_model", "RUNTIME_CALLABLE"),
    SemanticRule("S-C01", "C01_DERIVATION_STARTED", "BUILD_FAILED", "RUNTIME::derive_metadata_and_sql", "RUNTIME_CALLABLE"),
    SemanticRule("S-C01", "C01_XLSX_WRITE_STARTED", "BUILD_FAILED", "RUNTIME::write_xlsx_projection", "RUNTIME_CALLABLE"),
    SemanticRule("S-C01", "C01_SEAL_STARTED", "BUILD_FAILED", "RUNTIME::seal_staged_handoff", "RUNTIME_CALLABLE"),
    SemanticRule("S-C01", "C01_STAGED_VERIFY_STARTED", "BUILD_FAILED", "RUNTIME::verify_staged_handoff", "RUNTIME_CALLABLE"),
    SemanticRule("S-C02", "C02_VERIFY_STARTED", "BUILD_FAILED", "RUNTIME::verify_source_handoff", "RUNTIME_CALLABLE"),
    SemanticRule("S-C03", "C03_REPRODUCTION_STARTED", "BUILD_FAILED", "RUNTIME::reproduce_handoff", "RUNTIME_CALLABLE"),
    SemanticRule("S-C01", "C01_REQUEST_PARSED", "INVALID_REQUEST", "REQUEST::expected_model_digest", "REQUEST_DIGEST_SYNTAX_VALID"),
    SemanticRule("S-C01", "C01_SOURCE_COPY_STABILITY_VERIFIED", "SOURCE_CHANGED_DURING_COPY", "SOURCE_MODEL::model-manifest.json", "SOURCE_MODEL_COPY_STABLE"),
    SemanticRule("S-C02", "C02_NONCANONICAL_BINARY_VERIFIED", "NONCANONICAL_BINARY_MISMATCH", XLSX_CORE_TARGET, "XLSX_MEMBER_DIGEST_MATCHES_MANIFEST"),
    SemanticRule("S-C03", "C03_SOURCE_VERIFY_STARTED", "BUILD_FAILED", "RUNTIME::verify_source_handoff", "RUNTIME_CALLABLE"),
)


class LogicalFixtureResolver(V11Resolver):
    """Execute recipes without reading their expected checkpoint or fixture outcome."""

    def __init__(self) -> None:
        self.authority_context = load_json("mutation-positive-context-v4.json")
        self.context = copy.deepcopy(self.authority_context)
        vectors = load_json("metadata-positive-logical-vectors-v4.json")["vectors"]
        self.authority_documents = {
            item["vector_ref"]: item["document"] for item in vectors
        }
        self.documents = copy.deepcopy(self.authority_documents)
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
                    "ordinal": row[3],
                }
                for row in failures["checkpoints"]
            ),
            key=lambda item: (item["operation"], item["ordinal"]),
        )

    def _positive_value(self, recipe_ref: str, target_ref: str) -> LogicalValue:
        active_context = self.context
        active_documents = self.documents
        try:
            self.context = self.authority_context
            self.documents = self.authority_documents
            return copy.deepcopy(self._safe_resolve(recipe_ref, target_ref))
        finally:
            self.context = active_context
            self.documents = active_documents

    def _predicate_passes(self, rule: SemanticRule, recipe_ref: str) -> bool:
        actual = self._safe_resolve(recipe_ref, rule.target_ref)
        constraints = self.context["semantic_constraints"]
        predicate = rule.predicate_ref
        if predicate == "MATCH_VERIFIED_PACKAGE_VALUE":
            return actual == self._positive_value(recipe_ref, rule.target_ref)
        if predicate == "MATCH_MANIFEST_FILE_HASH":
            return actual == LogicalValue(
                "REGULAR_FILE_SHA256",
                self.context["derived_values"]["SOURCE_MODEL_SCHEMA_P-D06_SHA256"],
            )
        if predicate == "CACHE_EQUALS_VERIFIED_PACKAGE":
            expected = self._positive_value(recipe_ref, SOURCE_PACKAGE_AMOUNT_TARGET)
            return actual.kind == "INTEGER" and actual.value == expected.value
        if predicate in {"FORBID_RECURSIVE_HANDOFF_DIGEST", "PACKAGE_PATH_ABSENT", "OUTPUT_PATH_ABSENT"}:
            return actual.kind == "ABSENT" and actual.value is None
        if predicate == "XLSX_INTEGER_REPRESENTATION_SAFE":
            limit = constraints["safe_integer_max"]
            if actual.kind == "INTEGER_NUMERIC":
                return isinstance(actual.value, int) and abs(actual.value) <= limit
            if actual.kind == "INTEGER_TEXT":
                try:
                    return abs(int(actual.value)) > limit
                except (TypeError, ValueError):
                    return False
            return actual.kind == "FORMULA"
        if predicate == "XLSX_NULL_CELL_ABSENT":
            return actual.kind == "ABSENT_CELL" and actual.value is None
        if predicate == "XLSX_FORMULA_FREE":
            return actual.kind != "FORMULA"
        if predicate == "XLSX_EXTERNAL_LINK_FREE":
            return actual.kind == "ABSENT" and actual.value is None
        if predicate == "METADATA_DIGEST_MATCHES_MODEL":
            return actual.value == self.context["derived_values"]["SOURCE_MODEL_P-D06_LOGICAL_TABLE_DIGEST"]
        if predicate in {"PROVENANCE_MATCHES_AUTHENTICATED_MAPPING", "VALIDATION_EXPECTED_VALUE_MATCHES_AUTHORITY"}:
            return actual == self._positive_value(recipe_ref, rule.target_ref)
        if predicate == "VALIDATION_ASSERTION_KIND_AUTHORISED":
            return actual == LogicalValue("TEXT", "FIELD_EQUALS")
        if predicate == "SQL_QUERY_MATCHES_AUTHORITY":
            query_id = rule.target_ref.rsplit("::", 1)[1]
            return actual == LogicalValue("UTF8", self.queries[query_id])
        if predicate == "VALIDATION_SELECTOR_MATCHES_AUTHORITY":
            return actual == LogicalValue("TEXT", "SEL-CT1-AUTHORED-HEADERS")
        if predicate == "TRACE_DIRECTION_SOURCE_TO_TARGET":
            return actual == LogicalValue("TEXT", "SOURCE_TO_TARGET")
        if predicate == "SOURCE_PATH_IS_DIRECTORY":
            return actual.kind == "DIRECTORY"
        if predicate == "RUNTIME_CALLABLE":
            return actual == LogicalValue("CALLABLE", "normal")
        if predicate == "WRITER_PROFILE_SUPPORTED":
            return actual.kind == "TEXT" and actual.value in constraints["supported_writer_profile_refs"]
        if predicate == "CACHE_PROFILE_VERSION_MATCHES":
            return actual == LogicalValue("INTEGER", constraints["source_cache_profile_version"])
        if predicate == "XLSX_CAPACITY_WITHIN_LIMIT":
            maximum = constraints["excel_max_rows"] - constraints["excel_header_rows"]
            return actual.kind == "INTEGER" and isinstance(actual.value, int) and 0 <= actual.value <= maximum
        if predicate == "SOURCE_PACKAGE_IS_DIRECTORY":
            return actual.kind == "DIRECTORY"
        if predicate == "REPRO_CACHE_EQUALS_SOURCE_CACHE":
            source = self._safe_resolve(recipe_ref, DUCKDB_AMOUNT_TARGET)
            return actual.kind == source.kind == "INTEGER" and actual.value == source.value
        if predicate == "WRITER_RUNTIME_AVAILABLE":
            return actual.kind == "AVAILABLE" and str(actual.value).startswith("XlsxWriter-")
        if predicate == "REPRO_DIGEST_MATCHES_POSITIVE":
            return read_seal(self.context, "staged_handoff_digest") == read_seal(
                self.authority_context, "staged_handoff_digest"
            )
        if predicate == "REQUEST_DIGEST_SYNTAX_VALID":
            return actual.kind == "TEXT" and re.fullmatch(r"sha256:[0-9a-f]{64}", str(actual.value)) is not None
        if predicate == "SOURCE_MODEL_COPY_STABLE":
            return actual == LogicalValue(
                "REGULAR_FILE_SHA256",
                self.context["derived_values"]["SOURCE_MODEL_MANIFEST_SHA256"],
            )
        if predicate == "XLSX_MEMBER_DIGEST_MATCHES_MANIFEST":
            return actual == LogicalValue(
                "ZIP_MEMBER_SHA256",
                self.context["derived_values"]["XLSX_MEMBER_docProps/core.xml_SHA256"],
            )
        raise AssertionError(f"unknown semantic predicate: {predicate}")

    def _validate_checkpoint(
        self, recipe_ref: str, operation: str, checkpoint_ref: str
    ) -> str | None:
        for rule in SEMANTIC_RULES:
            if (
                rule.operation == operation
                and rule.checkpoint_ref == checkpoint_ref
                and not self._predicate_passes(rule, recipe_ref)
            ):
                return rule.failure_code
        return None

    def execute_recipe(
        self, recipe: list[Any], *, require_failure: bool = True
    ) -> ExecutionResult:
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
        validators: list[str] = []
        changed_targets: list[str] = []
        reseal_steps: list[str] = []
        reseal_changes: list[str] = []
        request_mutation: str | None = None
        mutation_applied = False

        for checkpoint in (
            item for item in self.checkpoints if item["operation"] == operation
        ):
            checkpoint_ref = checkpoint["checkpoint_ref"]
            validators.append(checkpoint_ref)
            failure_code = self._validate_checkpoint(
                recipe_ref, operation, checkpoint_ref
            )
            if failure_code is not None:
                if not mutation_applied:
                    raise AssertionError(f"{recipe_ref} failed before mutation")
                return ExecutionResult(
                    recipe_ref,
                    tuple(changed_targets),
                    tuple(reseal_steps),
                    tuple(reseal_changes),
                    request_mutation,
                    tuple(validators),
                    checkpoint_ref,
                    failure_code,
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
        if require_failure:
            raise AssertionError(f"{recipe_ref} produced no semantic failure")
        return ExecutionResult(
            recipe_ref,
            tuple(changed_targets),
            tuple(reseal_steps),
            tuple(reseal_changes),
            request_mutation,
            tuple(validators),
            None,
            None,
        )

    def _set_seal(self, key: str, value: str, changed: list[str]) -> None:
        realm, coordinate = self.context["seal_bindings"][key].split("::", 1)
        document, field = coordinate.split("#/", 1)
        current = self.context["json_roots"][realm][document][field]
        if current != value:
            self.context["json_roots"][realm][document][field] = value
            changed.append(seal_target_ref(key))

    def _execute_reseal(self, reseal_ref: str) -> tuple[list[str], list[str]]:
        if reseal_ref == "NONE":
            return [], []
        steps = self.context["reseal_contracts"][reseal_ref]
        if steps != sorted(steps):
            raise AssertionError(f"{reseal_ref} steps are not lexical")
        changed: list[str] = []
        for step in steps:
            if step == "R01_RECOMPUTE_CACHE_LOGICAL":
                self._set_seal(
                    "r_cache_logical_digest",
                    _r_cache_values(self.context)["r_cache_logical_digest"],
                    changed,
                )
            elif step == "R02_REWRITE_CACHE_MANIFEST":
                self._set_seal(
                    "r_cache_manifest_digest",
                    canonical_sha256(
                        {"r_cache": read_seal(self.context, "r_cache_logical_digest")}
                    ),
                    changed,
                )
            elif step == "C01_RECOMPUTE_CACHE_LOGICAL":
                self._set_seal(
                    "staged_r_cache_logical_digest",
                    _staged_r_cache_values(self.context)[
                        "staged_r_cache_logical_digest"
                    ],
                    changed,
                )
            elif step == "C02_REWRITE_CACHE_MANIFEST":
                self._set_seal(
                    "staged_r_cache_manifest_digest",
                    canonical_sha256(
                        {
                            "r_cache": read_seal(
                                self.context, "staged_r_cache_logical_digest"
                            )
                        }
                    ),
                    changed,
                )
            elif step == "R03_REWRITE_S_NONCANONICAL_MANIFEST":
                self._set_seal(
                    "s_noncanonical_manifest_digest",
                    _noncanonical_manifest_value(
                        read_seal(self.context, "r_cache_manifest_digest"),
                        read_seal(self.context, "xlsx_binary_digest"),
                        read_seal(self.context, "xlsx_logical_digest"),
                    ),
                    changed,
                )
            elif step in {"R04_RETAIN_CANONICAL_HANDOFF_DIGEST", "X04_RETAIN_CANONICAL_HANDOFF_DIGEST"}:
                read_seal(self.context, "handoff_digest")
            elif step == "S01_CANONICALIZE_CHANGED_AUTHORITIES":
                self._set_seal(
                    "s_canonical_digest",
                    _s_canonical_values(self.context)["s_canonical_digest"],
                    changed,
                )
            elif step == "S02_RECOMPUTE_CANONICAL_CHECKSUMS":
                self._set_seal(
                    "s_checksums_digest",
                    canonical_sha256(
                        {"s_canonical": read_seal(self.context, "s_canonical_digest")}
                    ),
                    changed,
                )
            elif step == "S03_RECOMPUTE_HANDOFF_DIGEST":
                self._set_seal(
                    "handoff_digest",
                    canonical_sha256(
                        {"checksums": read_seal(self.context, "s_checksums_digest")}
                    ),
                    changed,
                )
            elif step == "X01_RECOMPUTE_XLSX_BINARY_DIGEST":
                self._set_seal(
                    "xlsx_binary_digest",
                    _xlsx_values(self.context)["xlsx_binary_digest"],
                    changed,
                )
            elif step == "X02_RECOMPUTE_XLSX_LOGICAL_DIGEST":
                self._set_seal(
                    "xlsx_logical_digest",
                    canonical_sha256(
                        {"xlsx": read_seal(self.context, "xlsx_binary_digest")}
                    ),
                    changed,
                )
            elif step == "X03_REWRITE_XLSX_NONCANONICAL_MANIFEST":
                self._set_seal(
                    "s_noncanonical_manifest_digest",
                    _noncanonical_manifest_value(
                        read_seal(self.context, "r_cache_manifest_digest"),
                        read_seal(self.context, "xlsx_binary_digest"),
                        read_seal(self.context, "xlsx_logical_digest"),
                    ),
                    changed,
                )
            elif step == "M01_CANONICALIZE_R_MANIFEST":
                self._set_seal(
                    "r_model_canonical_digest",
                    _r_model_values(self.context)["r_model_canonical_digest"],
                    changed,
                )
            elif step == "M02_RECOMPUTE_R_CHECKSUMS":
                self._set_seal(
                    "r_model_checksums_digest",
                    canonical_sha256(
                        {"r_model": read_seal(self.context, "r_model_canonical_digest")}
                    ),
                    changed,
                )
            elif step == "M03_RECOMPUTE_R_MODEL_DIGEST":
                self._set_seal(
                    "r_model_digest",
                    canonical_sha256(
                        {"r_checksums": read_seal(self.context, "r_model_checksums_digest")}
                    ),
                    changed,
                )
            elif step == "T01_CANONICALIZE_STAGED_JSON":
                self._set_seal(
                    "staged_canonical_digest",
                    _staged_values(self.context)["staged_canonical_digest"],
                    changed,
                )
            elif step == "T02_RECOMPUTE_STAGED_CHECKSUMS":
                self._set_seal(
                    "staged_checksums_digest",
                    canonical_sha256(
                        {"staged": read_seal(self.context, "staged_canonical_digest")}
                    ),
                    changed,
                )
            elif step == "T03_RECOMPUTE_STAGED_HANDOFF_DIGEST":
                self._set_seal(
                    "staged_handoff_digest",
                    canonical_sha256(
                        {"checksums": read_seal(self.context, "staged_checksums_digest")}
                    ),
                    changed,
                )
            else:
                raise AssertionError(f"unknown reseal step: {step}")
        self.context.setdefault("executed_reseals", []).append(
            {
                "reseal_ref": reseal_ref,
                "steps": list(steps),
                "changed_binding_targets": list(changed),
            }
        )
        return list(steps), changed

    def _execute_request_mutation(self, request_mutation_ref: str) -> str | None:
        if request_mutation_ref == "NONE":
            return None
        spec = self.context["request_mutations"][request_mutation_ref]
        mutation = spec["mutation"]
        if mutation == "TEXT:CURRENT_RESEALED_HANDOFF_DIGEST":
            mutation = "TEXT:" + read_seal(self.context, "handoff_digest")
        self._apply_mutation(
            request_mutation_ref,
            spec["target_ref"],
            spec["operator"],
            mutation,
        )
        return request_mutation_ref
