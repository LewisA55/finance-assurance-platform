"""Dependency-locked Parquet writer profile for Artifact R Phase R1."""

from __future__ import annotations

from finance_assurance.digestion.contracts import (
    PINNED_PARQUET_PROFILE_HASH,
    PINNED_PYARROW_OPTIONS_HASH,
    ParquetWriterProfile,
)
from finance_assurance.runtime.canonical import canonical_sha256

WRITER_PROFILE_REF = "PYARROW-25@v1"

# This is the complete option set consumed by the future R2 writer wrapper.
# R1 fixes it now but deliberately writes no Parquet bytes.
PYARROW_WRITE_OPTIONS: dict[str, object] = {
    "allow_truncated_timestamps": False,
    "bloom_filter_options": None,
    "coerce_timestamps": "us",
    "column_encoding": None,
    "compression": "zstd",
    "compression_level": 3,
    "data_page_size": 1048576,
    "data_page_version": "1.0",
    "dictionary_pagesize_limit": 1048576,
    "encryption_properties": None,
    "flavor": None,
    "max_rows_per_page": 65536,
    "row_group_size": 65536,
    "sorting_columns": None,
    "store_decimal_as_integer": False,
    "store_schema": True,
    "use_byte_stream_split": False,
    "use_compliant_nested_type": True,
    "use_deprecated_int96_timestamps": False,
    "use_dictionary": True,
    "version": "2.6",
    "write_batch_size": 1024,
    "write_page_checksum": False,
    "write_page_index": False,
    "write_statistics": True,
    "write_time_adjusted_to_utc": True,
}


def _profile_body() -> dict[str, object]:
    return {
        "compression_codec": "ZSTD",
        "compression_level": 3,
        "data_page_version": "1.0",
        "dictionary_encoding": True,
        "implementation": "PYARROW",
        "implementation_version": "25.0.0",
        "profile_id": WRITER_PROFILE_REF,
        "profile_version": 1,
        "row_group_size": 65536,
        "schema_metadata_policy": "R_CONTRACT_AND_SOURCE_COORDINATE_ONLY",
        "statistics_mode": "ALL",
        "timestamp_timezone": "UTC",
        "timestamp_unit": "MICROSECOND",
        "writer_version": "finance-assurance-pyarrow-writer@v1",
    }


PARQUET_WRITER_PROFILE = ParquetWriterProfile(
    **_profile_body(),
    profile_hash=canonical_sha256(
        {
            "profile": _profile_body(),
            "writer_options_hash": PINNED_PYARROW_OPTIONS_HASH,
        }
    ),
)

if PARQUET_WRITER_PROFILE.profile_hash != PINNED_PARQUET_PROFILE_HASH:
    raise RuntimeError("declared Parquet profile hash does not match its binding")


def writer_options_hash() -> str:
    """Bind every option consumed by the future R2 writer wrapper."""

    return canonical_sha256(PYARROW_WRITE_OPTIONS)


def validate_writer_runtime() -> None:
    """Reject a runtime that cannot honor the dependency-locked profile."""

    import pyarrow

    if pyarrow.__version__ != PARQUET_WRITER_PROFILE.implementation_version:
        raise RuntimeError("installed PyArrow does not match the R writer profile")
    if writer_options_hash() != PINNED_PYARROW_OPTIONS_HASH:
        raise RuntimeError("R writer options do not match the pinned profile")
