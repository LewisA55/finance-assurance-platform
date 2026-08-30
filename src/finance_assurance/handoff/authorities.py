"""Exact checked-in authorities for Artifact S Phase S1."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from finance_assurance.exports.serialization import sha256_bytes
from finance_assurance.runtime.canonical import canonical_sha256

AUTHORITY_DIRECTORY = (
    Path(__file__).resolve().parents[3]
    / "tests"
    / "fixtures"
    / "local-analytical-handoff"
)


@dataclass(frozen=True, slots=True)
class AuthoritySpec:
    filename: str
    file_sha256: str
    canonical_sha256: str | None = None


AUTHORITY_SPECS = (
    AuthoritySpec(
        "readme-v1.md",
        "sha256:6b30bddd0db4f608844191722df2285595e9bfe955fe5edbacf3a4e5b8a3c8a0",
    ),
    AuthoritySpec(
        "limitations-v1.json",
        "sha256:683490346f9cc3c82ef02fbce4a3d2bf5cde119edd724f159c68167c39417772",
        "sha256:a353c13d8ba10ffb0bfa08e68fdbff85d5a3fad3c8dcda8b94b168cf859f8914",
    ),
    AuthoritySpec(
        "starter-queries-v1.sql",
        "sha256:d27ddd406a6ad77209f292140bae0c4fe724ee71dddd18c56cc1f844c47d044e",
    ),
    AuthoritySpec(
        "reconciliation-queries-v1.sql",
        "sha256:4b22a4edbafe4542797f5cb36ba945651c3637ecc6ee56bbf427bac920801557",
    ),
    AuthoritySpec(
        "validation-registry-v1.json",
        "sha256:60ca04f300039da6c575fe77c25f69a440bb7c413e53674911b4db740f38b633",
        "sha256:36255992b12b0176f290ec2fa033e5655d8ca4b3a2e4cbd3a522a1de295f7cb8",
    ),
    AuthoritySpec(
        "xlsx-logical-vectors-v1.json",
        "sha256:3b2f0dee58092b211f8169296fa32ad927fadefaf34ed7f045df26910f7d1bae",
        "sha256:4ebd181b9bbef9e7a2e038e764f74fc7bec57e41305a494372637afd611c8c94",
    ),
    AuthoritySpec(
        "operation-failure-state-registry-v1.json",
        "sha256:19ebfd9dbf0face3ac39abc3c5acab27916f459bc264c6121d40bdd07c9c77bb",
        "sha256:0f1f0d7af6678e32670d93623a73f8d8d4203e7c607974c667aa7c6ef56e5cbe",
    ),
    AuthoritySpec(
        "negative-fixture-registry-v2.json",
        "sha256:ef203ecd239e674135c94147c9d52b52c8c6b02ada7a41c6067a2c638cc3389c",
        "sha256:9045d0a33d4131df49a976befd04c490c06ee8446c525ff3de68ad21b67e1537",
    ),
    AuthoritySpec(
        "negative-mutation-recipes-v1.json",
        "sha256:4110112fb87a31728ed7e3c908dbd6719e691063b5bb0dc7a81b59790415d1e4",
        "sha256:eac2ee3e444a520cb68383ee78381dd2f6a73701e2dbf9c748469e96e48b9c22",
    ),
)

AUTHORITY_BY_FILENAME = {item.filename: item for item in AUTHORITY_SPECS}

_QUERY_HEADER = re.compile(r"^-- (S-Q(?:S|V)[0-9]{2})\n", re.MULTILINE)
_FORBIDDEN_SQL = re.compile(
    r"\b(?:CREATE|INSERT|UPDATE|DELETE|MERGE|COPY|ATTACH|DETACH|INSTALL|LOAD|"
    r"EXPORT|IMPORT|PRAGMA|MACRO|CALL)\b|\b(?:READ_CSV|READ_PARQUET|SCAN)\s*\(",
    re.IGNORECASE,
)


def _authority_path(filename: str, directory: Path) -> Path:
    if filename not in AUTHORITY_BY_FILENAME:
        raise ValueError(f"unregistered Artifact S authority: {filename}")
    return directory / filename


def read_authority_bytes(
    filename: str,
    *,
    directory: Path = AUTHORITY_DIRECTORY,
) -> bytes:
    spec = AUTHORITY_BY_FILENAME[filename]
    payload = _authority_path(filename, directory).read_bytes()
    if not payload.endswith(b"\n") or b"\r" in payload:
        raise ValueError(f"{filename} must be exactly LF-terminated")
    try:
        payload.decode("ascii")
    except UnicodeDecodeError as error:
        raise ValueError(f"{filename} must contain ASCII only") from error
    if sha256_bytes(payload) != spec.file_sha256:
        raise ValueError(f"{filename} does not match its exact authority hash")
    return payload


def load_json_authority(
    filename: str,
    *,
    directory: Path = AUTHORITY_DIRECTORY,
) -> dict[str, Any]:
    spec = AUTHORITY_BY_FILENAME[filename]
    if spec.canonical_sha256 is None:
        raise ValueError(f"{filename} is not a registered JSON authority")
    value = json.loads(read_authority_bytes(filename, directory=directory))
    if not isinstance(value, dict):
        raise ValueError(f"{filename} must contain one JSON object")
    if canonical_sha256(value) != spec.canonical_sha256:
        raise ValueError(f"{filename} parsed object does not match its authority hash")
    return value


def split_sql_authority(
    filename: str,
    *,
    directory: Path = AUTHORITY_DIRECTORY,
) -> tuple[tuple[str, str], ...]:
    text = read_authority_bytes(filename, directory=directory).decode("ascii")
    matches = tuple(_QUERY_HEADER.finditer(text))
    expected_prefix = "S-QS" if filename == "starter-queries-v1.sql" else "S-QV"
    expected_count = 5 if expected_prefix == "S-QS" else 12
    expected_ids = tuple(
        f"{expected_prefix}{number:02d}" for number in range(1, expected_count + 1)
    )
    query_ids = tuple(match.group(1) for match in matches)
    if query_ids != expected_ids:
        raise ValueError(f"{filename} query inventory is not exact")
    statements: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        stop = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        sql = text[match.end() : stop].strip()
        if not sql.endswith(";") or _FORBIDDEN_SQL.search(sql):
            raise ValueError(f"{match.group(1)} is not closed read-only SQL")
        if not sql.lstrip().upper().startswith(("SELECT", "WITH")):
            raise ValueError(f"{match.group(1)} must start with SELECT or WITH")
        statements.append((match.group(1), sql))
    return tuple(statements)


def validate_authorities(
    *,
    directory: Path = AUTHORITY_DIRECTORY,
) -> None:
    for spec in AUTHORITY_SPECS:
        if spec.canonical_sha256 is None:
            read_authority_bytes(spec.filename, directory=directory)
        else:
            load_json_authority(spec.filename, directory=directory)
    split_sql_authority("starter-queries-v1.sql", directory=directory)
    split_sql_authority("reconciliation-queries-v1.sql", directory=directory)
