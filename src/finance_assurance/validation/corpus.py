"""Read-only loading and immutable indexing of the ratified fixture corpus."""

from __future__ import annotations

import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

type JsonScalar = bool | int | float | str | None
type FrozenJson = JsonScalar | Mapping[str, FrozenJson] | tuple[FrozenJson, ...]

CANONICAL_FIXTURE_FILES = (
    "canonical-object-payloads.jsonl",
    "c001-accounting-events.jsonl",
    "ct1-accounting-events.jsonl",
    "restatement-case-snapshots.jsonl",
    "referenced-state-projections.jsonl",
    "reporting-content-proof-bodies.jsonl",
)


class CorpusLoadError(ValueError):
    """A deterministic failure to load one corpus record."""

    def __init__(
        self,
        message: str,
        *,
        file_name: str,
        line_number: int | None = None,
    ) -> None:
        self.file_name = file_name
        self.line_number = line_number
        location = file_name
        if line_number is not None:
            location = f"{location}:{line_number}"
        super().__init__(f"{location}: {message}")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_non_json_constant(value: str) -> object:
    raise ValueError(f"non-JSON numeric constant: {value}")


def freeze_json(value: object) -> FrozenJson:
    """Recursively freeze parsed JSON without changing scalar values."""

    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, dict):
        frozen = {key: freeze_json(item) for key, item in value.items()}
        return MappingProxyType(frozen)
    if isinstance(value, list):
        return tuple(freeze_json(item) for item in value)
    raise TypeError(f"unsupported parsed JSON value: {type(value).__name__}")


def thaw_json(value: FrozenJson) -> object:
    """Return a fresh mutable JSON tree for strict boundary validation."""

    if isinstance(value, Mapping):
        return {key: thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [thaw_json(item) for item in value]
    return value


@dataclass(frozen=True, slots=True)
class RawRecord:
    """One immutable parsed JSONL record with its source location."""

    file_name: str
    line_number: int
    raw_text: str
    value: Mapping[str, FrozenJson]


@dataclass(frozen=True, slots=True)
class RawFixtureFile:
    """One required fixture file in canonical corpus order."""

    name: str
    records: tuple[RawRecord, ...]


@dataclass(frozen=True, slots=True)
class RawCorpusIndex:
    """Immutable raw corpus produced before Artifact F validation."""

    root: Path
    files: tuple[RawFixtureFile, ...]

    def file(self, name: str) -> RawFixtureFile:
        """Return a required fixture file by its canonical name."""

        for fixture_file in self.files:
            if fixture_file.name == name:
                return fixture_file
        raise KeyError(name)

    def records(self, name: str) -> tuple[RawRecord, ...]:
        """Return immutable records for one canonical file."""

        return self.file(name).records

    def all_records(self) -> Iterator[RawRecord]:
        """Iterate records in canonical file and line order."""

        for fixture_file in self.files:
            yield from fixture_file.records

    @property
    def record_count(self) -> int:
        """Return the total number of non-empty JSONL records."""

        return sum(len(fixture_file.records) for fixture_file in self.files)


def project_root() -> Path:
    """Return the repository root for the editable validation harness."""

    return Path(__file__).resolve().parents[3]


def default_fixture_root() -> Path:
    """Return the ratified corpus directory in this checkout."""

    return project_root() / "docs" / "architecture" / "fixtures"


def load_jsonl_file(path: Path) -> RawFixtureFile:
    """Parse one JSONL file as immutable top-level JSON objects."""

    if not path.is_file():
        raise CorpusLoadError("required fixture file is missing", file_name=path.name)

    records: list[RawRecord] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError as error:
        raise CorpusLoadError(
            "fixture is not valid UTF-8",
            file_name=path.name,
        ) from error

    for line_number, raw_text in enumerate(lines, start=1):
        if not raw_text.strip():
            continue
        try:
            parsed = json.loads(
                raw_text,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_non_json_constant,
            )
        except (json.JSONDecodeError, ValueError) as error:
            raise CorpusLoadError(
                str(error),
                file_name=path.name,
                line_number=line_number,
            ) from error
        if not isinstance(parsed, dict):
            raise CorpusLoadError(
                "non-empty line must contain one JSON object",
                file_name=path.name,
                line_number=line_number,
            )
        frozen = freeze_json(parsed)
        if not isinstance(frozen, Mapping):
            raise AssertionError("frozen JSON object lost its mapping type")
        records.append(
            RawRecord(
                file_name=path.name,
                line_number=line_number,
                raw_text=raw_text,
                value=frozen,
            ),
        )

    return RawFixtureFile(name=path.name, records=tuple(records))


def load_raw_corpus(root: Path | None = None) -> RawCorpusIndex:
    """Load all six canonical files without modifying their bytes."""

    fixture_root = (root or default_fixture_root()).resolve()
    files = tuple(
        load_jsonl_file(fixture_root / file_name)
        for file_name in CANONICAL_FIXTURE_FILES
    )
    return RawCorpusIndex(root=fixture_root, files=files)
