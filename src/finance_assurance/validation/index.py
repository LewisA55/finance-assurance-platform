"""Immutable validated corpus constructed from, never over, RawCorpusIndex."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import BaseModel

from finance_assurance.validation.contracts.registry import (
    canonical_model_bytes,
    validate_accounting_event,
    validate_object,
)
from finance_assurance.validation.corpus import RawCorpusIndex, RawRecord, thaw_json


@dataclass(frozen=True, slots=True)
class ValidatedRecord:
    raw: RawRecord
    contract_key: str
    value: BaseModel

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_model_bytes(self.value)


@dataclass(frozen=True, slots=True)
class ValidatedCorpusIndex:
    """Validated authored corpus plus untouched referenced-state boundaries."""

    raw: RawCorpusIndex
    canonical_objects: tuple[ValidatedRecord, ...]
    restatement_snapshots: tuple[ValidatedRecord, ...]
    c001_events: tuple[ValidatedRecord, ...]
    ct1_events: tuple[ValidatedRecord, ...]

    @property
    def objects(self) -> tuple[ValidatedRecord, ...]:
        return self.canonical_objects + self.restatement_snapshots

    @property
    def events(self) -> tuple[ValidatedRecord, ...]:
        return self.c001_events + self.ct1_events


def _object_record(record: RawRecord) -> ValidatedRecord:
    object_type = record.value.get("object_type")
    if not isinstance(object_type, str):
        raise ValueError("fixture object_type must be a string")
    payload = thaw_json(record.value.get("payload"))
    return ValidatedRecord(record, object_type, validate_object(object_type, payload))


def _event_record(record: RawRecord) -> ValidatedRecord:
    payload = thaw_json(record.value)
    model = validate_accounting_event(payload)
    return ValidatedRecord(record, str(model.event_type), model)


def build_validated_index(raw: RawCorpusIndex) -> ValidatedCorpusIndex:
    """Build a new all-or-nothing index after every domain record validates."""

    canonical_objects = tuple(
        _object_record(record)
        for record in raw.records("canonical-object-payloads.jsonl")
    )
    snapshots = tuple(
        _object_record(record)
        for record in raw.records("restatement-case-snapshots.jsonl")
    )
    c001_events = tuple(
        _event_record(record) for record in raw.records("c001-accounting-events.jsonl")
    )
    ct1_events = tuple(
        _event_record(record) for record in raw.records("ct1-accounting-events.jsonl")
    )
    return ValidatedCorpusIndex(
        raw=raw,
        canonical_objects=canonical_objects,
        restatement_snapshots=snapshots,
        c001_events=c001_events,
        ct1_events=ct1_events,
    )
