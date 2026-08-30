"""Raw JSONL corpus loader tests."""

from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from finance_assurance.validation.corpus import (
    CANONICAL_FIXTURE_FILES,
    CorpusLoadError,
    default_fixture_root,
    load_jsonl_file,
    load_raw_corpus,
)


def test_canonical_corpus_loads_in_declared_order_without_rewriting() -> None:
    root = default_fixture_root()
    before = {
        file_name: (root / file_name).read_bytes()
        for file_name in CANONICAL_FIXTURE_FILES
    }

    index = load_raw_corpus()

    after = {
        file_name: (root / file_name).read_bytes()
        for file_name in CANONICAL_FIXTURE_FILES
    }
    assert tuple(fixture_file.name for fixture_file in index.files) == (
        CANONICAL_FIXTURE_FILES
    )
    assert index.record_count == 43
    assert before == after


def test_raw_records_and_nested_values_are_immutable() -> None:
    index = load_raw_corpus()
    record = index.records("canonical-object-payloads.jsonl")[0]

    with pytest.raises(FrozenInstanceError):
        record.line_number = 99  # type: ignore[misc]
    with pytest.raises(TypeError):
        record.value["fixture_id"] = "changed"  # type: ignore[index]
    with pytest.raises(TypeError):
        record.value["payload"]["contract_version"] = 2  # type: ignore[index]


def test_loader_ignores_empty_lines(tmp_path: Path) -> None:
    path = tmp_path / "sample.jsonl"
    path.write_text('\n{"fixture_id":"ONE"}\n  \n', encoding="utf-8")

    loaded = load_jsonl_file(path)

    assert len(loaded.records) == 1
    assert loaded.records[0].line_number == 2


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("not-json", "Expecting value"),
        ("[]", "must contain one JSON object"),
        ('{"id":1,"id":2}', "duplicate JSON object key"),
        ('{"amount":NaN}', "non-JSON numeric constant"),
    ],
)
def test_loader_rejects_invalid_jsonl_records(
    tmp_path: Path,
    content: str,
    message: str,
) -> None:
    path = tmp_path / "invalid.jsonl"
    path.write_text(content, encoding="utf-8")

    with pytest.raises(CorpusLoadError, match=message):
        load_jsonl_file(path)


def test_loader_rejects_a_missing_required_file(tmp_path: Path) -> None:
    with pytest.raises(CorpusLoadError, match="required fixture file is missing"):
        load_jsonl_file(tmp_path / "missing.jsonl")
