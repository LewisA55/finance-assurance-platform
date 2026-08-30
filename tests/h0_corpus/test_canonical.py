"""Canonical JSON serialization tests."""

import math

import pytest

from finance_assurance.validation.canonical import canonical_bytes, canonical_sha256
from finance_assurance.validation.corpus import freeze_json


def test_canonical_bytes_sort_keys_recursively_and_preserve_array_order() -> None:
    value = freeze_json(
        {
            "z": [{"b": 2, "a": 1}, "second"],
            "a": "sterling-GBP",
        },
    )

    result = canonical_bytes(value)

    assert result == b'{"a":"sterling-GBP","z":[{"a":1,"b":2},"second"]}'
    assert not result.startswith(b"\xef\xbb\xbf")
    assert not result.endswith(b"\n")


def test_canonical_bytes_encode_unicode_as_utf8() -> None:
    assert canonical_bytes({"currency": "\u00a3"}) == '{"currency":"\u00a3"}'.encode()


@pytest.mark.parametrize("value", [math.nan, math.inf, -math.inf])
def test_canonical_bytes_reject_non_finite_numbers(value: float) -> None:
    with pytest.raises(ValueError, match="non-finite"):
        canonical_bytes({"value": value})


def test_canonical_bytes_reject_non_string_object_keys() -> None:
    with pytest.raises(TypeError, match="keys must be strings"):
        canonical_bytes({1: "invalid"})  # type: ignore[dict-item]


def test_canonical_sha256_uses_contract_prefix() -> None:
    assert canonical_sha256({"a": 1}) == (
        "sha256:015abd7f5cc57a2dd94b7590f04ad8084273905ee33ec5cebeae62276a97f862"
    )
