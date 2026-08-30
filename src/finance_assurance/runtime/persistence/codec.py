"""Closed, deterministic codec for the Phase 3 SQLite adapter.

This is an adapter codec, not a new wire contract.  Type tags are accepted only
for the finite runtime classes registered below; decoding never imports a type
named by persisted data.
"""

from __future__ import annotations

import inspect
import json
from dataclasses import fields, is_dataclass
from enum import Enum
from types import ModuleType
from typing import Any

from pydantic import BaseModel

from finance_assurance.runtime import planner, referenced, rejections
from finance_assurance.runtime.application import models as application_models
from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256
from finance_assurance.runtime.contracts import events, evidence, objects, primitives
from finance_assurance.runtime.contracts import module as module_contracts
from finance_assurance.runtime.persistence import models, state

_TAG = "$runtime_type"
_VALUE = "value"


class DurableCodecError(ValueError):
    """Raised when durable bytes contain a type outside the closed registry."""


def _qualified(value: type[object]) -> str:
    return f"{value.__module__}.{value.__qualname__}"


def _classes(module: ModuleType) -> tuple[type[object], ...]:
    return tuple(
        value
        for _, value in inspect.getmembers(module, inspect.isclass)
        if value.__module__.startswith("finance_assurance.runtime")
    )


_MODULES = (
    planner,
    referenced,
    rejections,
    events,
    evidence,
    objects,
    primitives,
    module_contracts,
    models,
    state,
    application_models,
)
_REGISTRY = {
    _qualified(value): value for module in _MODULES for value in _classes(module)
}


def _encode(value: object) -> Any:
    if isinstance(value, BaseModel):
        return {
            _TAG: _qualified(type(value)),
            _VALUE: value.model_dump(mode="json"),
        }
    if isinstance(value, Enum):
        return {_TAG: _qualified(type(value)), _VALUE: value.value}
    if is_dataclass(value) and not isinstance(value, type):
        return {
            _TAG: _qualified(type(value)),
            _VALUE: {
                item.name: _encode(getattr(value, item.name)) for item in fields(value)
            },
        }
    if isinstance(value, frozenset):
        encoded = [_encode(item) for item in value]
        return {
            _TAG: "builtins.frozenset",
            _VALUE: sorted(encoded, key=canonical_bytes),
        }
    if isinstance(value, set):
        encoded = [_encode(item) for item in value]
        return {
            _TAG: "builtins.set",
            _VALUE: sorted(encoded, key=canonical_bytes),
        }
    if isinstance(value, tuple):
        return {_TAG: "builtins.tuple", _VALUE: [_encode(item) for item in value]}
    if isinstance(value, list):
        return [_encode(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _encode(item) for key, item in value.items()}
    if value is None or isinstance(value, (str, int, bool)):
        return value
    raise DurableCodecError(f"unsupported durable value: {type(value)!r}")


def _decode(value: Any) -> object:
    if isinstance(value, list):
        return [_decode(item) for item in value]
    if not isinstance(value, dict):
        return value
    type_name = value.get(_TAG)
    if type_name is None:
        return {key: _decode(item) for key, item in value.items()}
    body = value.get(_VALUE)
    if type_name == "builtins.tuple":
        return tuple(_decode(item) for item in body)
    if type_name == "builtins.frozenset":
        return frozenset(_decode(item) for item in body)
    if type_name == "builtins.set":
        return set(_decode(item) for item in body)
    runtime_type = _REGISTRY.get(type_name)
    if runtime_type is None:
        raise DurableCodecError(f"unregistered durable type: {type_name}")
    if issubclass(runtime_type, BaseModel):
        if (
            runtime_type.__name__ == "ContractPublication"
            and isinstance(body, dict)
            and "product_state_token" not in body
        ):
            body = {**body, "product_state_token": None}
        return runtime_type.model_validate_json(
            json.dumps(body, ensure_ascii=True, separators=(",", ":"))
        )
    if issubclass(runtime_type, Enum):
        return runtime_type(body)
    if is_dataclass(runtime_type):
        if not isinstance(body, dict):
            raise DurableCodecError(f"invalid dataclass body for {type_name}")
        return runtime_type(**{key: _decode(item) for key, item in body.items()})
    raise DurableCodecError(f"unsupported registered type: {type_name}")


def encode_durable(value: object) -> bytes:
    """Return canonical UTF-8 bytes for one closed runtime value."""

    return canonical_bytes(_encode(value))


def decode_durable(payload: bytes, expected_type: type[object]) -> object:
    """Decode bytes and require the caller's exact top-level semantic type."""

    try:
        parsed = json.loads(payload)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise DurableCodecError("durable payload is not canonical JSON") from error
    decoded = _decode(parsed)
    if not isinstance(decoded, expected_type):
        raise DurableCodecError(
            f"expected {expected_type.__name__}, received {type(decoded).__name__}"
        )
    if encode_durable(decoded) != payload:
        raise DurableCodecError("durable payload is not in canonical form")
    return decoded


def durable_hash(payload: bytes) -> str:
    """Hash the exact persisted bytes."""

    return canonical_sha256(json.loads(payload))
