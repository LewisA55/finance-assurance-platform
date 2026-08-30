"""Executable acceptance tests for Artifact H H1."""

from dataclasses import FrozenInstanceError

import pytest
from pydantic import BaseModel

from finance_assurance.validation.canonical import canonical_sha256
from finance_assurance.validation.contracts import objects as contract_objects
from finance_assurance.validation.contracts.registry import ContractViolation
from finance_assurance.validation.corpus import load_raw_corpus
from finance_assurance.validation.h1 import run_h1
from finance_assurance.validation.index import build_validated_index
from finance_assurance.validation.results import AssertionStatus


def test_canonical_corpus_passes_all_fourteen_h1_assertions() -> None:
    run = run_h1()

    assert run.index is not None
    assert run.passed
    assert [result.test_id for result in run.results] == [
        f"H1-{number:02d}" for number in range(1, 15)
    ]
    assert {result.status for result in run.results} == {AssertionStatus.PASS}


def test_validated_index_is_distinct_and_deeply_immutable() -> None:
    raw = load_raw_corpus()
    before = canonical_sha256(tuple(record.value for record in raw.all_records()))
    validated = build_validated_index(raw)

    assert validated.raw is raw
    assert canonical_sha256(tuple(record.value for record in raw.all_records())) == before
    with pytest.raises((FrozenInstanceError, TypeError, ValueError)):
        validated.c001_events[0].value.event_id = "changed"


def test_each_negative_mutation_has_a_stable_rejection_code() -> None:
    run = run_h1()
    negative_results = run.results[3:]

    assert len(negative_results) == 11
    assert all("rejected with " in result.actual_outcome for result in negative_results)
    assert len({result.actual_outcome for result in negative_results}) >= 8


def test_contract_violation_string_does_not_expose_pydantic_wording() -> None:
    from finance_assurance.validation.contracts.registry import validate_object

    with pytest.raises(ContractViolation) as caught:
        validate_object("not-an-object", {})

    assert str(caught.value) == "UNKNOWN_DISCRIMINATOR: unknown object type"


def test_contract_models_do_not_supply_wire_defaults() -> None:
    assert contract_objects.OBJECT_ADAPTERS

    def descendants(model: type[BaseModel]) -> set[type[BaseModel]]:
        direct = set(model.__subclasses__())
        return direct | {child for item in direct for child in descendants(item)}

    contract_models = {
        model
        for model in descendants(BaseModel)
        if model.__module__.startswith("finance_assurance.runtime.contracts")
    }
    assert contract_models
    assert all(
        field.is_required()
        for model in contract_models
        for field in model.model_fields.values()
    )
