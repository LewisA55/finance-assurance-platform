from __future__ import annotations

import inspect

import pytest

from finance_assurance.digestion.keys import (
    assert_no_key_collisions,
    relationship_key,
)
from finance_assurance.digestion.writer import (
    PARQUET_WRITER_PROFILE,
    PYARROW_WRITE_OPTIONS,
    validate_writer_runtime,
    writer_options_hash,
)


def test_relationship_key_uses_exact_p_canonical_json_fixture() -> None:
    assert relationship_key(
        "P-RL02",
        ("text", "text"),
        ("DEMO-C001", "RV-JUNE@v1"),
    ) == "sha256:3b0e795cbd022b32df146b6e7fda55108c8074ac2ba1f6f8405c787998c15009"


@pytest.mark.parametrize(
    ("types", "values", "error"),
    [
        (("text", "text"), ("A", None), "cannot be null"),
        (("text",), ("A", "B"), "equal width"),
        (("integer", "text"), (True, "A"), "must be an int"),
        (("text", "text"), ("A", ""), "non-empty text"),
    ],
)
def test_relationship_key_rejects_incomplete_or_mistyped_tuples(
    types: tuple[str, ...], values: tuple[object, ...], error: str
) -> None:
    with pytest.raises((TypeError, ValueError), match=error):
        relationship_key("P-RL02", types, values)


def test_collision_guard_distinguishes_duplicate_from_collision() -> None:
    assert_no_key_collisions(
        (
            ("sha256:" + "a" * 64, ("A", "B")),
            ("sha256:" + "a" * 64, ("A", "B")),
        )
    )
    with pytest.raises(ValueError, match="collision"):
        assert_no_key_collisions(
            (
                ("sha256:" + "a" * 64, ("A", "B")),
                ("sha256:" + "a" * 64, ("A", "C")),
            )
        )


def test_writer_profile_and_all_byte_affecting_options_are_locked() -> None:
    import pyarrow.parquet as pq

    validate_writer_runtime()

    assert PARQUET_WRITER_PROFILE.implementation_version == "25.0.0"
    assert (
        PARQUET_WRITER_PROFILE.writer_version
        == "finance-assurance-pyarrow-writer@v1"
    )
    assert len(PYARROW_WRITE_OPTIONS) == 26
    assert writer_options_hash() == (
        "sha256:2642b3ea3f71badfff44760005b01ed1f80f9a571d823dc99fa6ef78f432b862"
    )
    assert PARQUET_WRITER_PROFILE.profile_hash == (
        "sha256:2702aa8812844e508d5b303c50b52e30ab9f20cf7b65c42c2d59f39171b85cb1"
    )
    accepted = set(inspect.signature(pq.write_table).parameters)
    assert set(PYARROW_WRITE_OPTIONS) <= accepted
