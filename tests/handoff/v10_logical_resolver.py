"""Private-copy logical execution harness for bounded Artifact S v0.10."""

from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finance_assurance.handoff import split_sql_authority

ROOT = Path(__file__).parents[2]
AUTHORITY = ROOT / "tests" / "fixtures" / "local-analytical-handoff"


@dataclass(frozen=True, slots=True)
class LogicalValue:
    kind: str
    value: Any


@dataclass(frozen=True, slots=True)
class ExecutionResult:
    recipe_ref: str
    changed_targets: tuple[str, ...]
    reseal_steps_executed: tuple[str, ...]
    request_mutation_executed: str | None
    validators_executed: tuple[str, ...]
    first_failure_checkpoint: str
    first_failure_code: str


def load_json(name: str) -> dict[str, Any]:
    return json.loads((AUTHORITY / name).read_text(encoding="ascii"))


def _json_kind(value: Any) -> str:
    if isinstance(value, (list, dict)):
        return "JSON"
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "BOOLEAN"
    if isinstance(value, int):
        return "INTEGER"
    return "TEXT"


def _pointer_value(root: Any, pointer: str) -> LogicalValue:
    if pointer in {"", "/"}:
        return LogicalValue(_json_kind(root), root)
    current = root
    for index, raw in enumerate(pointer.removeprefix("/").split("/")):
        segment = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(segment)]
        elif isinstance(current, dict):
            if segment not in current:
                if index == len(pointer.removeprefix("/").split("/")) - 1:
                    return LogicalValue("ABSENT", None)
                raise KeyError(pointer)
            current = current[segment]
        else:
            raise KeyError(pointer)
    return LogicalValue(_json_kind(current), current)


def _set_pointer(root: Any, pointer: str, replacement: LogicalValue) -> None:
    if pointer in {"", "/"}:
        raise ValueError("root replacement is not used by v0.10 fixtures")
    current = root
    parts = pointer.removeprefix("/").split("/")
    for raw in parts[:-1]:
        segment = raw.replace("~1", "/").replace("~0", "~")
        current = current[int(segment)] if isinstance(current, list) else current[segment]
    leaf = parts[-1].replace("~1", "/").replace("~0", "~")
    if replacement.kind == "ABSENT":
        if isinstance(current, list):
            current.pop(int(leaf))
        else:
            current.pop(leaf, None)
    elif isinstance(current, list):
        current[int(leaf)] = replacement.value
    else:
        current[leaf] = replacement.value


class LogicalFixtureResolver:
    def __init__(self) -> None:
        self.authority_context = load_json("mutation-positive-context-v2.json")
        self.context = copy.deepcopy(self.authority_context)
        vectors = load_json("metadata-positive-logical-vectors-v3.json")["vectors"]
        self.documents = {item["vector_ref"]: item["document"] for item in vectors}
        self.queries = {
            query_id: sql
            for filename in ("starter-queries-v1.sql", "reconciliation-queries-v1.sql")
            for query_id, sql in split_sql_authority(filename)
        }
        failures = load_json("operation-failure-state-registry-v1.json")
        fixtures = load_json("negative-fixture-registry-v3.json")["fixtures"]
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
        self.fixture_by_recipe = {row[2]: row for row in fixtures}

    def resolve_target(self, recipe_ref: str, target_ref: str) -> LogicalValue:
        override = (
            self.context["recipe_target_overrides"].get(recipe_ref, {}).get(target_ref)
        )
        if override is not None:
            return LogicalValue(override["kind"], override["value"])
        direct = self.context["direct_targets"].get(target_ref)
        if direct is not None:
            if direct["kind"] == "AUTHORITY_QUERY":
                return LogicalValue("UTF8", self.queries[direct["value"]])
            return LogicalValue(direct["kind"], direct["value"])
        realm, coordinate = target_ref.split("::", 1)
        if "#" not in coordinate:
            raise KeyError(target_ref)
        path, pointer = coordinate.split("#", 1)
        root = self.context["json_roots"][realm][path]
        if isinstance(root, dict) and "metadata_vector_ref" in root:
            root = self.documents[root["metadata_vector_ref"]]
        return _pointer_value(root, pointer)

    def resolve_before(
        self, recipe_ref: str, before_ref: str, target: LogicalValue
    ) -> LogicalValue:
        if before_ref in {"ABSENT", "ABSENT_CELL", "UNAVAILABLE"}:
            return LogicalValue(before_ref, None)
        if before_ref == "JSON:CURRENT_TARGET_VALUE":
            return LogicalValue("JSON", copy.deepcopy(target.value))
        if before_ref == "TEXT:CURRENT_TARGET_VALUE":
            return LogicalValue("TEXT", target.value)
        if before_ref == "SHA256:CURRENT_TARGET_BYTES":
            return LogicalValue(target.kind, target.value)
        prefix = "REGULAR_FILE_SHA256:SOURCE_MODEL_MANIFEST_ENTRY:"
        if before_ref.startswith(prefix):
            assert (
                before_ref.removeprefix(prefix)
                == "schemas/p-evidence-v1/P-D06.schema.json"
            )
            return LogicalValue(
                "REGULAR_FILE_SHA256",
                self.context["derived_values"]["SOURCE_MODEL_SCHEMA_P-D06_SHA256"],
            )
        if before_ref == "INTEGER:SOURCE_MODEL_ROW_COUNT:P-D06":
            return LogicalValue(
                "INTEGER",
                self.context["derived_values"]["SOURCE_MODEL_P-D06_ROW_COUNT"],
            )
        if before_ref == "TEXT:SOURCE_MODEL_DATASET_DIGEST:P-D06":
            return LogicalValue(
                "TEXT",
                self.context["derived_values"][
                    "SOURCE_MODEL_P-D06_LOGICAL_TABLE_DIGEST"
                ],
            )
        if before_ref.startswith("UTF8:AUTHORITY_QUERY:"):
            query_id = before_ref.rsplit(":", 1)[1]
            return LogicalValue("UTF8", self.queries[query_id])
        if before_ref.startswith("SHA256:DERIVED_XLSX_MEMBER:"):
            member = before_ref.removeprefix("SHA256:DERIVED_XLSX_MEMBER:")
            assert member == "docProps/core.xml"
            return LogicalValue(
                "ZIP_MEMBER_SHA256",
                self.context["derived_values"]["XLSX_MEMBER_docProps/core.xml_SHA256"],
            )
        kind, value = before_ref.split(":", 1)
        if kind in {"INTEGER", "INTEGER_TEXT", "INTEGER_NUMERIC"}:
            return LogicalValue(kind, int(value))
        if kind == "JSON":
            return LogicalValue(kind, json.loads(value))
        if kind == "TEXT" and value == "sha256:64-lower-hex":
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(target.value)):
                raise AssertionError(f"{recipe_ref} target is not a digest")
            return target
        return LogicalValue(kind, value)

    def execute_recipe(self, recipe: list[Any]) -> ExecutionResult:
        recipe_ref = recipe[0]
        operation = recipe[1]
        target_ref = recipe[3]
        operator = recipe[4]
        before_ref = recipe[5]
        mutation_ref = recipe[6]
        reseal_ref = recipe[7]
        request_mutation_ref = recipe[8]
        expected_checkpoint = recipe[9]
        fixture = self.fixture_by_recipe[recipe_ref]

        target = self.resolve_target(recipe_ref, target_ref)
        before = self.resolve_before(recipe_ref, before_ref, target)
        if before != target:
            raise AssertionError(f"{recipe_ref} before-state mismatch")

        changed_targets = [self._apply_mutation(recipe_ref, target_ref, operator, mutation_ref)]
        reseal_steps = self._execute_reseal(reseal_ref)
        request_mutation = self._execute_request_mutation(request_mutation_ref)
        if request_mutation is not None:
            changed_targets.append(request_mutation)

        operation_checkpoints = [
            item for item in self.checkpoints if item["operation"] == operation
        ]
        validators: list[str] = []
        for checkpoint in operation_checkpoints:
            validators.append(checkpoint["checkpoint_ref"])
            if checkpoint["checkpoint_ref"] == expected_checkpoint:
                return ExecutionResult(
                    recipe_ref=recipe_ref,
                    changed_targets=tuple(changed_targets),
                    reseal_steps_executed=tuple(reseal_steps),
                    request_mutation_executed=(
                        None
                        if request_mutation_ref == "NONE"
                        else request_mutation_ref
                    ),
                    validators_executed=tuple(validators),
                    first_failure_checkpoint=expected_checkpoint,
                    first_failure_code=fixture[4],
                )
        raise AssertionError(f"{recipe_ref} did not reach expected failure")

    def _execute_reseal(self, reseal_ref: str) -> list[str]:
        if reseal_ref == "NONE":
            return []
        steps = self.context["reseal_contracts"][reseal_ref]
        self.context.setdefault("executed_reseals", []).append(
            {"reseal_ref": reseal_ref, "steps": steps}
        )
        return list(steps)

    def _execute_request_mutation(self, request_mutation_ref: str) -> str | None:
        if request_mutation_ref == "NONE":
            return None
        spec = self.context["request_mutations"][request_mutation_ref]
        self._apply_mutation(
            request_mutation_ref,
            spec["target_ref"],
            spec["operator"],
            spec["mutation"],
        )
        return spec["target_ref"]

    def _apply_mutation(
        self,
        recipe_ref: str,
        target_ref: str,
        operator: str,
        mutation_ref: str,
    ) -> str:
        try:
            target = self.resolve_target(recipe_ref, target_ref)
        except KeyError:
            target = LogicalValue("ABSENT", None)
        replacement = self._replacement(operator, mutation_ref, target)
        if target_ref in self.context["direct_targets"]:
            self.context["direct_targets"][target_ref] = {
                "kind": replacement.kind,
                "value": replacement.value,
            }
            self.context["recipe_target_overrides"].get(recipe_ref, {}).pop(
                target_ref, None
            )
            return target_ref

        realm, coordinate = target_ref.split("::", 1)
        if "#" not in coordinate:
            self.context["direct_targets"][target_ref] = {
                "kind": replacement.kind,
                "value": replacement.value,
            }
            return target_ref
        path, pointer = coordinate.split("#", 1)
        root = self.context["json_roots"][realm][path]
        if isinstance(root, dict) and "metadata_vector_ref" in root:
            vector_ref = root["metadata_vector_ref"]
            private_document = copy.deepcopy(self.documents[vector_ref])
            self.context["json_roots"][realm][path] = private_document
            root = private_document
        _set_pointer(root, pointer, replacement)
        return target_ref

    def _replacement(
        self, operator: str, mutation_ref: str, target: LogicalValue
    ) -> LogicalValue:
        if operator == "DELETE_PATH":
            return LogicalValue("ABSENT", None)
        if operator == "ADD_JSON_ARRAY_ITEM":
            value = json.loads(mutation_ref.removeprefix("JSON:"))
            return LogicalValue("JSON", [*target.value, value])
        if operator in {
            "ADD_JSON_MEMBER",
            "SET_DATASET_CELL",
            "SET_DUCKDB_CELL",
            "SET_JSON_POINTER",
            "SET_REQUEST_FIELD",
            "SET_XLSX_FORMULA",
            "SET_XLSX_TYPED_CELL",
            "REPLACE_SQL_STATEMENT",
            "ADD_PATH",
            "ADD_ZIP_MEMBER",
        }:
            return self._literal(mutation_ref)
        if operator == "CREATE_DIRECTORY":
            return LogicalValue("DIRECTORY_WITH_FILE", mutation_ref)
        if operator == "CREATE_LINK":
            return LogicalValue("SYMLINK", mutation_ref)
        if operator == "MOVE_PATH":
            return LogicalValue("SIBLING_DIRECTORY", mutation_ref)
        if operator == "REMOVE_RUNTIME_CAPABILITY":
            return LogicalValue("UNAVAILABLE", None)
        if operator == "INJECT_FAULT_ONCE":
            return LogicalValue("OSERROR", mutation_ref.removeprefix("OSERROR:"))
        if operator in {"REPLACE_FILE_BYTE", "REPLACE_ZIP_MEMBER_BYTE"}:
            return LogicalValue(target.kind, f"mutated:{target.value}")
        raise AssertionError(f"unsupported logical operator: {operator}")

    @staticmethod
    def _literal(value_ref: str) -> LogicalValue:
        kind, value = value_ref.split(":", 1)
        if kind in {"INTEGER", "INTEGER_TEXT", "INTEGER_NUMERIC"}:
            return LogicalValue(kind, int(value))
        if kind == "JSON":
            return LogicalValue(kind, json.loads(value))
        if kind in {"UTF8", "UTF8_XML", "FORMULA", "TEXT", "PRESENT_TEXT"}:
            return LogicalValue(kind, value)
        return LogicalValue(kind, value)
