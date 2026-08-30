"""Artifact S canonical JSON and typed-workbook digest functions."""

from __future__ import annotations

import copy
from collections.abc import Mapping, Sequence

from finance_assurance.handoff.authorities import load_json_authority
from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256


def _reject_float_and_non_ascii(value: object) -> None:
    if isinstance(value, float):
        raise TypeError("Artifact S canonical JSON prohibits floating-point values")
    if isinstance(value, str):
        if not value.isascii():
            raise ValueError("Artifact S canonical JSON requires ASCII content")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str) or not key.isascii():
                raise ValueError("Artifact S canonical JSON keys require ASCII text")
            _reject_float_and_non_ascii(item)
        return
    if isinstance(value, Sequence) and not isinstance(
        value, (str, bytes, bytearray)
    ):
        for item in value:
            _reject_float_and_non_ascii(item)


def canonical_json_file_bytes(value: object) -> bytes:
    _reject_float_and_non_ascii(value)
    return canonical_bytes(value) + b"\n"  # type: ignore[arg-type]


def typed_rows_digest(preimage: Mapping[str, object]) -> str:
    if preimage.get("contract_version") != "xlsx-typed-rows@v1":
        raise ValueError("typed-row preimage contract is not supported")
    _reject_float_and_non_ascii(preimage)
    return canonical_sha256(preimage)


def logical_workbook_digest(preimage: Mapping[str, object]) -> str:
    if preimage.get("contract_version") != "logical-workbook-digest@v1":
        raise ValueError("logical-workbook preimage contract is not supported")
    _reject_float_and_non_ascii(preimage)
    return canonical_sha256(preimage)


def _set_json_pointer(value: object, pointer: str, replacement: object) -> None:
    current = value
    parts = pointer.strip("/").split("/")
    for part in parts[:-1]:
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            raise ValueError("mutation JSON pointer does not resolve")
    terminal = parts[-1]
    if isinstance(current, list):
        current[int(terminal)] = replacement
    elif isinstance(current, dict):
        current[terminal] = replacement
    else:
        raise ValueError("mutation JSON pointer does not resolve")


def validate_workbook_vectors() -> None:
    payload = load_json_authority("xlsx-logical-vectors-v1.json")
    typed = payload["typed_rows_vector"]
    logical = payload["logical_workbook_vector"]
    if typed_rows_digest(typed["preimage"]) != typed["expected_digest"]:
        raise ValueError("positive typed-row vector digest differs")
    if logical_workbook_digest(logical["preimage"]) != logical["expected_digest"]:
        raise ValueError("positive logical-workbook vector digest differs")
    bases = {
        typed["vector_id"]: typed["preimage"],
        logical["vector_id"]: logical["preimage"],
    }
    rejected_contracts = 0
    for mutation in payload["mutation_vectors"]:
        changed = copy.deepcopy(bases[mutation["base_vector_id"]])
        for operation in mutation["operations"]:
            if operation.get("operation") == "SWAP_ROW_CELL_ARRAYS":
                left, right = operation["row_ordinals"]
                changed["rows"][left - 1]["cells"], changed["rows"][right - 1][
                    "cells"
                ] = changed["rows"][right - 1]["cells"], changed["rows"][left - 1][
                    "cells"
                ]
            else:
                _set_json_pointer(
                    changed,
                    operation["target_json_pointer"],
                    operation["replacement"],
                )
        actual = canonical_sha256(changed)
        if actual != mutation["expected_digest"]:
            raise ValueError(f"{mutation['mutation_id']} digest differs")
        if actual == canonical_sha256(bases[mutation["base_vector_id"]]):
            raise ValueError(f"{mutation['mutation_id']} did not change its digest")
        if mutation["expected_outcome"].endswith("CONTRACT_REJECTED"):
            rejected_contracts += 1
    if rejected_contracts != 2:
        raise ValueError("workbook vectors must contain two contract rejections")
