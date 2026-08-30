"""Executable logical target resolver for bounded Artifact S v0.9 authority proof."""

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


def _pointer(root: Any, pointer: str) -> LogicalValue:
    if pointer == "":
        return LogicalValue(_json_kind(root), root)
    current = root
    segments = pointer.removeprefix("/").split("/")
    for index, raw in enumerate(segments):
        segment = raw.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(segment)]
        elif isinstance(current, dict):
            if segment not in current:
                if index == len(segments) - 1:
                    return LogicalValue("ABSENT", None)
                raise KeyError(pointer)
            current = current[segment]
        else:
            raise KeyError(pointer)
    return LogicalValue(_json_kind(current), current)


class LogicalFixtureResolver:
    def __init__(self) -> None:
        self.context = load_json("mutation-positive-context-v1.json")
        vectors = load_json("metadata-positive-logical-vectors-v2.json")["vectors"]
        self.documents = {item["vector_ref"]: item["document"] for item in vectors}
        self.queries = {
            query_id: sql
            for filename in ("starter-queries-v1.sql", "reconciliation-queries-v1.sql")
            for query_id, sql in split_sql_authority(filename)
        }

    def resolve_target(self, recipe_ref: str, target_ref: str) -> LogicalValue:
        override = self.context["recipe_target_overrides"].get(recipe_ref, {}).get(
            target_ref
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
        return _pointer(root, pointer)

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
            assert before_ref.removeprefix(prefix) == "schemas/p-evidence-v1/P-D06.schema.json"
            return LogicalValue(
                "REGULAR_FILE_SHA256",
                self.context["derived_values"]["SOURCE_MODEL_SCHEMA_P-D06_SHA256"],
            )
        if before_ref == "INTEGER:SOURCE_MODEL_ROW_COUNT:P-D06":
            return LogicalValue(
                "INTEGER", self.context["derived_values"]["SOURCE_MODEL_P-D06_ROW_COUNT"]
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
        if kind == "INTEGER":
            return LogicalValue(kind, int(value))
        if kind in {"INTEGER_TEXT", "INTEGER_NUMERIC"}:
            return LogicalValue(kind, int(value))
        if kind == "JSON":
            return LogicalValue(kind, json.loads(value))
        if kind == "TEXT" and value == "sha256:64-lower-hex":
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", str(target.value)):
                raise AssertionError(f"{recipe_ref} target is not a digest")
            return target
        return LogicalValue(kind, value)

    def apply_mutation(
        self, operator: str, mutation_ref: str, target: LogicalValue
    ) -> LogicalValue:
        if operator == "DELETE_PATH":
            return LogicalValue("ABSENT", None)
        if operator == "ADD_JSON_ARRAY_ITEM":
            value = json.loads(mutation_ref.removeprefix("JSON:"))
            return LogicalValue("JSON", [*target.value, value])
        if operator == "ADD_JSON_MEMBER":
            return self._literal(mutation_ref)
        if operator in {
            "SET_DATASET_CELL",
            "SET_DUCKDB_CELL",
            "SET_JSON_POINTER",
            "SET_REQUEST_FIELD",
            "SET_XLSX_FORMULA",
            "SET_XLSX_TYPED_CELL",
            "REPLACE_SQL_STATEMENT",
        }:
            return self._literal(mutation_ref)
        if operator in {"ADD_PATH", "ADD_ZIP_MEMBER"}:
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
