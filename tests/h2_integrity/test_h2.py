"""Executable acceptance tests for Artifact H H2."""

from finance_assurance.validation.canonical import canonical_sha256
from finance_assurance.validation.h1 import run_h1
from finance_assurance.validation.h2 import run_h2
from finance_assurance.validation.integrity import (
    IntegrityViolation,
    assert_reversal_integrity,
)
from finance_assurance.validation.proofs import (
    resolve_referenced_journal,
    resolve_reporting_content,
)
from finance_assurance.validation.results import AssertionStatus


def _index_digest(index: object) -> str:
    return canonical_sha256(
        {
            "raw": [record.value for record in index.raw.all_records()],
            "objects": [
                record.value.model_dump(mode="json", round_trip=True)
                for record in index.objects
            ],
            "events": [
                record.value.model_dump(mode="json", round_trip=True)
                for record in index.events
            ],
        }
    )


def test_canonical_corpus_passes_all_eleven_h2_assertions() -> None:
    run = run_h2()

    assert run.index is not None
    assert run.passed
    assert [result.test_id for result in run.results] == [
        f"H2-{number:02d}" for number in range(1, 12)
    ]
    assert {result.status for result in run.results} == {AssertionStatus.PASS}


def test_h2_is_pure_over_the_validated_index() -> None:
    h1 = run_h1()
    assert h1.index is not None
    before = _index_digest(h1.index)

    first = run_h2(h1_run=h1)
    middle = _index_digest(h1.index)
    second = run_h2(h1_run=h1)
    after = _index_digest(h1.index)

    assert first.results == second.results
    assert before == middle == after


def test_reversal_hash_binding_precedes_line_comparison() -> None:
    h1 = run_h1()
    assert h1.index is not None
    projection = resolve_referenced_journal(h1.index)
    changed_line = projection.line_tuples[0].model_copy(
        update={"account_id": "ACC-OTHER"},
    )
    unbound_and_changed = projection.model_copy(
        update={
            "source_hash": "sha256:" + "0" * 64,
            "line_tuples": (changed_line, *projection.line_tuples[1:]),
        },
    )

    try:
        assert_reversal_integrity(h1.index, unbound_and_changed)
    except IntegrityViolation as error:
        assert error.code == "REVERSAL_BINDING"
    else:
        raise AssertionError("unbound reversal projection was accepted")


def test_proof_boundaries_remain_non_authored_and_hash_verified() -> None:
    h1 = run_h1()
    assert h1.index is not None
    projection = resolve_referenced_journal(h1.index)
    v1, v2 = resolve_reporting_content(h1.index)

    assert projection.authored_by_f is False
    assert projection.journal_id == "J-010"
    assert all(record.value is not projection for record in h1.index.objects)
    assert v1.content_hash != v2.content_hash
    assert v1.canonical_body.reporting_version_ref == "RV-2026-06@v1"
    assert v2.canonical_body.reporting_version_ref == "RV-2026-06@v2"
