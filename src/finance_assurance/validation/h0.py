"""Artifact H H0 corpus-integrity assertions."""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from finance_assurance.validation.canonical import canonical_sha256
from finance_assurance.validation.corpus import (
    FrozenJson,
    RawCorpusIndex,
    RawRecord,
    load_raw_corpus,
)
from finance_assurance.validation.results import AssertionResult, AssertionStatus

_EXPECTED_OBJECT_TYPES = {
    "accounting_event",
    "accounting_period",
    "business_event",
    "journal_entry",
    "journal_line",
    "journal_proposal",
    "posting_rule",
    "reporting_version",
    "restatement_case",
}
_VERSIONED_REF_PATTERN = re.compile(r".+@v[1-9][0-9]*")
_IDENTITY_FIELDS = {
    "business_event": "business_event_id",
    "posting_rule": "posting_rule_ref",
    "journal_proposal": "proposal_ref",
    "journal_entry": "journal_id",
    "journal_line": "journal_line_id",
    "accounting_period": "period_id",
    "reporting_version": "reporting_version_ref",
    "restatement_case": "restatement_case_id",
}
_VERSIONED_OBJECT_TYPES = {
    "posting_rule",
    "journal_proposal",
    "reporting_version",
}
_OPAQUE_OBJECT_TYPES = {
    "checklist",
    "contract",
    "disclosure_basis",
    "issue",
    "materiality_assessment",
    "policy",
    "recognition_schedule",
    "reconciliation",
    "remediation_directive",
}


class H0AssertionError(ValueError):
    """A deterministic H0 assertion failure."""


@dataclass(frozen=True, slots=True)
class H0Run:
    """The immutable H0 results and their raw corpus, when loadable."""

    index: RawCorpusIndex | None
    results: tuple[AssertionResult, ...]

    @property
    def passed(self) -> bool:
        """Return true only when all seven required assertions pass."""

        return all(result.status is AssertionStatus.PASS for result in self.results)


def _mapping(value: FrozenJson, context: str) -> Mapping[str, FrozenJson]:
    if not isinstance(value, Mapping):
        raise H0AssertionError(f"{context} must be an object")
    return value


def _sequence(value: FrozenJson, context: str) -> Sequence[FrozenJson]:
    if not isinstance(value, tuple):
        raise H0AssertionError(f"{context} must be an array")
    return value


def _string(value: FrozenJson, context: str) -> str:
    if not isinstance(value, str) or not value:
        raise H0AssertionError(f"{context} must be a non-empty string")
    return value


def _canonical_wrappers(index: RawCorpusIndex) -> tuple[RawRecord, ...]:
    return index.records("canonical-object-payloads.jsonl")


def _event_records(index: RawCorpusIndex) -> tuple[RawRecord, ...]:
    return (
        *index.records("c001-accounting-events.jsonl"),
        *index.records("ct1-accounting-events.jsonl"),
    )


def _fixture_records(index: RawCorpusIndex) -> tuple[RawRecord, ...]:
    return tuple(
        record for record in index.all_records() if "fixture_id" in record.value
    )


def _payload(record: RawRecord) -> Mapping[str, FrozenJson]:
    return _mapping(record.value.get("payload"), f"{record.file_name}:{record.line_number}.payload")


def _pass(test_id: str, expected: str, actual: str) -> AssertionResult:
    return AssertionResult(
        test_id=test_id,
        layer="H0",
        source_obligation=f"Artifact H {test_id}",
        status=AssertionStatus.PASS,
        expected_outcome=expected,
        actual_outcome=actual,
    )


def _fail(test_id: str, expected: str, actual: str) -> AssertionResult:
    return AssertionResult(
        test_id=test_id,
        layer="H0",
        source_obligation=f"Artifact H {test_id}",
        status=AssertionStatus.FAIL,
        expected_outcome=expected,
        actual_outcome=actual,
    )


def _blocked(test_id: str, expected: str, reason: str) -> AssertionResult:
    return AssertionResult(
        test_id=test_id,
        layer="H0",
        source_obligation=f"Artifact H {test_id}",
        status=AssertionStatus.BLOCKED,
        expected_outcome=expected,
        actual_outcome=reason,
    )


def _h0_02(index: RawCorpusIndex) -> str:
    object_types = {
        _string(record.value.get("object_type"), "object_type")
        for record in _canonical_wrappers(index)
    }
    if _event_records(index):
        object_types.add("accounting_event")

    c001_events = index.records("c001-accounting-events.jsonl")
    ct1_events = index.records("ct1-accounting-events.jsonl")
    event_types = {
        _string(record.value.get("event_type"), "event_type")
        for record in (*c001_events, *ct1_events)
    }

    problems: list[str] = []
    if object_types != _EXPECTED_OBJECT_TYPES:
        problems.append(
            f"object types were {','.join(sorted(object_types))}",
        )
    if len(event_types) != 10:
        problems.append(f"distinct event type count was {len(event_types)}")
    if len(c001_events) != 11:
        problems.append(f"C-001 event count was {len(c001_events)}")
    if len(ct1_events) != 6:
        problems.append(f"CT-1 event count was {len(ct1_events)}")
    if len(c001_events) + len(ct1_events) != 17:
        problems.append(
            f"total event instance count was {len(c001_events) + len(ct1_events)}",
        )
    if problems:
        raise H0AssertionError("; ".join(problems))
    return "9 object types; 10 event types; 11 C-001 + 6 CT-1 = 17 events"


def _duplicates(values: Sequence[str]) -> tuple[str, ...]:
    counts = Counter(values)
    return tuple(sorted(value for value, count in counts.items() if count > 1))


def _h0_03(index: RawCorpusIndex) -> str:
    events = _event_records(index)
    event_ids = [_string(record.value.get("event_id"), "event_id") for record in events]
    command_ids = [
        _string(record.value.get("command_id"), "command_id") for record in events
    ]
    fixture_ids = [
        _string(record.value.get("fixture_id"), "fixture_id")
        for record in _fixture_records(index)
    ]

    object_identities: list[tuple[str, str]] = []
    for record in _canonical_wrappers(index):
        object_type = _string(record.value.get("object_type"), "object_type")
        payload = _payload(record)
        identity_field = _IDENTITY_FIELDS.get(object_type)
        if identity_field is None:
            raise H0AssertionError(f"no H0 identity field for {object_type}")
        identity = _string(payload.get(identity_field), identity_field)
        if (
            object_type in _VERSIONED_OBJECT_TYPES
            and _VERSIONED_REF_PATTERN.fullmatch(identity) is None
        ):
            raise H0AssertionError(f"unversioned {object_type} identity: {identity}")
        object_identities.append((object_type, identity))

    problems: list[str] = []
    for label, values in (
        ("event IDs", event_ids),
        ("command IDs", command_ids),
        ("fixture IDs", fixture_ids),
    ):
        repeated = _duplicates(values)
        if repeated:
            problems.append(f"duplicate {label}: {','.join(repeated)}")
    repeated_objects = tuple(
        sorted(
            f"{object_type}:{identity}"
            for object_type, identity in _duplicates(object_identities)
        ),
    )
    if repeated_objects:
        problems.append(f"duplicate object identities: {','.join(repeated_objects)}")
    if problems:
        raise H0AssertionError("; ".join(problems))
    return (
        f"{len(event_ids)} event IDs; {len(command_ids)} command IDs; "
        f"{len(fixture_ids)} fixture IDs; {len(object_identities)} object identities"
    )


def _h0_04(index: RawCorpusIndex) -> str:
    snapshots = list(index.records("restatement-case-snapshots.jsonl"))
    terminal = [
        record
        for record in _canonical_wrappers(index)
        if record.value.get("object_type") == "restatement_case"
    ]
    records = (*snapshots, *terminal)
    forms: list[str] = []
    for record in records:
        payload = _payload(record)
        status = _string(payload.get("status"), "restatement status")
        linked = _sequence(payload.get("linked_journal_ids"), "linked_journal_ids")
        if status == "PROPOSED":
            forms.append("PROPOSED_EMPTY" if not linked else "PROPOSED_LINKED")
        else:
            forms.append(status)

    expected = {
        "PROPOSED_EMPTY",
        "PROPOSED_LINKED",
        "ADJUSTMENTS_READY",
        "APPROVED",
        "PUBLISHED",
    }
    if len(records) != 5 or set(forms) != expected:
        raise H0AssertionError(
            f"snapshot forms were {','.join(sorted(forms))}",
        )
    return "empty PROPOSED; linked PROPOSED; ADJUSTMENTS_READY; APPROVED; PUBLISHED"


def _h0_05(index: RawCorpusIndex) -> str:
    projections = index.records("referenced-state-projections.jsonl")
    if len(projections) != 1:
        raise H0AssertionError(f"referenced projection count was {len(projections)}")
    projection = projections[0].value
    if projection.get("projection_type") != "referenced_journal_projection":
        raise H0AssertionError("J-010 projection type is invalid")
    if projection.get("authored_by_f") is not False:
        raise H0AssertionError("J-010 projection is not marked authored_by_f=false")
    if projection.get("journal_id") != "J-010":
        raise H0AssertionError("referenced projection is not J-010")
    canonical_types = {
        record.value.get("object_type") for record in _canonical_wrappers(index)
    }
    if "referenced_journal_projection" in canonical_types:
        raise H0AssertionError("J-010 projection entered the authored object inventory")
    return "J-010 is one G-13 projection with authored_by_f=false"


def _authored_identities(index: RawCorpusIndex) -> dict[str, set[str]]:
    identities = {object_type: set() for object_type in _IDENTITY_FIELDS}
    for record in _canonical_wrappers(index):
        object_type = _string(record.value.get("object_type"), "object_type")
        payload = _payload(record)
        identity_field = _IDENTITY_FIELDS[object_type]
        identities[object_type].add(_string(payload.get(identity_field), identity_field))
    identities["accounting_event"] = {
        _string(record.value.get("event_id"), "event_id")
        for record in _event_records(index)
    }
    return identities


def _reporting_boundaries(index: RawCorpusIndex) -> tuple[set[str], set[str]]:
    version_refs: set[str] = set()
    content_refs: set[str] = set()
    for record in index.records("reporting-content-proof-bodies.jsonl"):
        value = record.value
        if value.get("canonicalization") != "SORTED_KEYS_COMPACT_UTF8_V1":
            raise H0AssertionError("reporting proof uses an unknown canonicalization")
        body = _mapping(value.get("canonical_body"), "canonical_body")
        content_hash = _string(value.get("content_hash"), "content_hash")
        actual_hash = canonical_sha256(body)
        if actual_hash != content_hash:
            raise H0AssertionError(
                f"reporting content hash mismatch for {value.get('fixture_id')}",
            )
        version_refs.add(
            _string(body.get("reporting_version_ref"), "reporting_version_ref"),
        )
        content_refs.add(_string(value.get("content_ref"), "content_ref"))
    if len(version_refs) != 2 or len(content_refs) != 2:
        raise H0AssertionError("reporting proof boundary must contain two versions")
    return version_refs, content_refs


def _check_reference(
    value: FrozenJson,
    allowed: set[str],
    context: str,
    problems: list[str],
) -> None:
    if value is None:
        return
    if not isinstance(value, str) or value not in allowed:
        problems.append(f"{context} unresolved: {value}")


def _walk_references(
    value: FrozenJson,
    *,
    path: str,
    routes: Mapping[str, set[str]],
    sequence_routes: Mapping[str, set[str]],
    subject_routes: Mapping[str, set[str]],
    reporting_content_refs: set[str],
    problems: list[str],
) -> None:
    if isinstance(value, Mapping):
        opaque_type = value.get("object_type")
        opaque_id = value.get("object_id")
        if opaque_id is not None:
            if opaque_type not in _OPAQUE_OBJECT_TYPES:
                problems.append(f"{path} has unpermitted opaque object type")
            if not isinstance(opaque_id, str) or not opaque_id:
                problems.append(f"{path}.object_id is not a non-empty string")

        subject = value.get("subject_ref")
        if isinstance(subject, Mapping):
            object_type = subject.get("object_type")
            object_ref = subject.get("object_ref")
            if not isinstance(object_type, str) or object_type not in subject_routes:
                problems.append(f"{path}.subject_ref has unknown object type")
            else:
                _check_reference(
                    object_ref,
                    subject_routes[object_type],
                    f"{path}.subject_ref.object_ref",
                    problems,
                )

        authority = value.get("derivation_authority")
        if isinstance(authority, Mapping):
            kind = authority.get("authority_kind")
            authority_ref = authority.get("authority_ref")
            if kind == "POSTING_RULE":
                _check_reference(
                    authority_ref,
                    routes["posting_rule_ref"],
                    f"{path}.derivation_authority.authority_ref",
                    problems,
                )
            elif kind != "POLICY":
                problems.append(f"{path}.derivation_authority has unknown kind")

        for key, item in value.items():
            item_path = f"{path}.{key}"
            if key in routes:
                _check_reference(item, routes[key], item_path, problems)
            elif key in sequence_routes:
                if not isinstance(item, tuple):
                    problems.append(f"{item_path} is not an array")
                else:
                    for index, member in enumerate(item):
                        _check_reference(
                            member,
                            sequence_routes[key],
                            f"{item_path}[{index}]",
                            problems,
                        )
            elif key == "content_ref" and isinstance(item, str):
                if item.startswith("reporting://"):
                    if item not in reporting_content_refs:
                        problems.append(f"{item_path} unresolved: {item}")
                elif not item.startswith("rules://"):
                    problems.append(f"{item_path} has unpermitted content boundary")
            _walk_references(
                item,
                path=item_path,
                routes=routes,
                sequence_routes=sequence_routes,
                subject_routes=subject_routes,
                reporting_content_refs=reporting_content_refs,
                problems=problems,
            )
    elif isinstance(value, tuple):
        for index, item in enumerate(value):
            _walk_references(
                item,
                path=f"{path}[{index}]",
                routes=routes,
                sequence_routes=sequence_routes,
                subject_routes=subject_routes,
                reporting_content_refs=reporting_content_refs,
                problems=problems,
            )


def _h0_06(index: RawCorpusIndex) -> str:
    authored = _authored_identities(index)
    reporting_versions, reporting_content_refs = _reporting_boundaries(index)
    g13_journals = {
        _string(record.value.get("journal_id"), "G-13 journal_id")
        for record in index.records("referenced-state-projections.jsonl")
    }
    all_journals = authored["journal_entry"] | g13_journals
    all_reporting_versions = authored["reporting_version"] | reporting_versions

    routes = {
        "business_event_ref": authored["business_event"],
        "posting_rule_ref": authored["posting_rule"],
        "proposal_ref": authored["journal_proposal"],
        "source_proposal_ref": authored["journal_proposal"],
        "predecessor_proposal_ref": authored["journal_proposal"],
        "posted_by_event_id": authored["accounting_event"],
        "hard_close_event_id": authored["accounting_event"],
        "published_by_event_id": authored["accounting_event"],
        "causation_event_id": authored["accounting_event"],
        "journal_id": all_journals,
        "reverses_journal_id": all_journals,
        "corrects_journal_id": all_journals,
        "journal_line_ref": authored["journal_line"],
        "period_id": authored["accounting_period"],
        "target_period_id": authored["accounting_period"],
        "ledger_period_id": authored["accounting_period"],
        "presented_period_id": authored["accounting_period"],
        "restatement_case_id": authored["restatement_case"],
        "reporting_version_ref": all_reporting_versions,
        "predecessor_version_ref": all_reporting_versions,
    }
    sequence_routes = {
        "deferred_proposal_refs": authored["journal_proposal"],
        "line_refs": authored["journal_line"],
        "linked_journal_ids": all_journals,
        "published_version_refs": all_reporting_versions,
        "scope_period_ids": authored["accounting_period"],
    }
    subject_routes = {
        "journal_proposal": authored["journal_proposal"],
        "accounting_period": authored["accounting_period"],
        "restatement_case": authored["restatement_case"],
    }
    problems: list[str] = []
    for record in index.all_records():
        _walk_references(
            record.value,
            path=f"{record.file_name}:{record.line_number}",
            routes=routes,
            sequence_routes=sequence_routes,
            subject_routes=subject_routes,
            reporting_content_refs=reporting_content_refs,
            problems=problems,
        )
    if problems:
        raise H0AssertionError("; ".join(problems))
    return (
        f"{sum(len(values) for values in authored.values())} authored identities; "
        f"{len(g13_journals)} G-13 journal; "
        f"{len(reporting_content_refs)} hash-verified reporting bodies; "
        "opaque-owner types bounded"
    )


def _walk_evidence(
    value: FrozenJson,
    relationships: dict[str, str],
    conflicts: list[str],
) -> None:
    if isinstance(value, Mapping):
        if "ref_id" in value and "content_hash" in value:
            ref_id = value.get("ref_id")
            content_hash = value.get("content_hash")
            if not isinstance(ref_id, str) or not isinstance(content_hash, str):
                conflicts.append("evidence ref_id and content_hash must be strings")
            else:
                prior = relationships.setdefault(ref_id, content_hash)
                if prior != content_hash:
                    conflicts.append(f"{ref_id} maps to multiple declared hashes")
        for item in value.values():
            _walk_evidence(item, relationships, conflicts)
    elif isinstance(value, tuple):
        for item in value:
            _walk_evidence(item, relationships, conflicts)


def _h0_07(index: RawCorpusIndex) -> str:
    relationships: dict[str, str] = {}
    conflicts: list[str] = []
    for record in index.all_records():
        _walk_evidence(record.value, relationships, conflicts)
    if conflicts:
        raise H0AssertionError("; ".join(conflicts))
    if not relationships:
        raise H0AssertionError("no declared-only evidence references found")
    return (
        f"{len(relationships)} stable ref_id-to-hash relationships; "
        "0 evidence bodies claimed as byte-verified"
    )


_CHECKS: tuple[tuple[str, str, Callable[[RawCorpusIndex], str]], ...] = (
    (
        "H0-02",
        "Nine object types, ten event types, and 11 + 6 = 17 event instances",
        _h0_02,
    ),
    (
        "H0-03",
        "Required event, command, fixture, and object identities are unique",
        _h0_03,
    ),
    (
        "H0-04",
        "Five RC-001 forms cover both PROPOSED forms through PUBLISHED",
        _h0_04,
    ),
    (
        "H0-05",
        "J-010 is one non-authored G-13 projection outside the object inventory",
        _h0_05,
    ),
    (
        "H0-06",
        "Required references resolve through their permitted boundaries",
        _h0_06,
    ),
    (
        "H0-07",
        "Each declared evidence ref_id has one hash without a byte claim",
        _h0_07,
    ),
)


def run_h0(root: Path | None = None) -> H0Run:
    """Load the corpus and execute H0-01 through H0-07 in order."""

    h0_01_expected = "Every non-empty line parses as one JSON object"
    try:
        index = load_raw_corpus(root)
    except (OSError, ValueError, TypeError) as error:
        results = [_fail("H0-01", h0_01_expected, str(error))]
        results.extend(
            _blocked(test_id, expected, "Blocked because H0-01 failed")
            for test_id, expected, _ in _CHECKS
        )
        return H0Run(index=None, results=tuple(results))

    results = [
        _pass(
            "H0-01",
            h0_01_expected,
            f"{index.record_count} non-empty lines parsed across 6 files",
        ),
    ]
    for test_id, expected, check in _CHECKS:
        try:
            actual = check(index)
        except (H0AssertionError, KeyError, TypeError, ValueError) as error:
            results.append(_fail(test_id, expected, str(error)))
        else:
            results.append(_pass(test_id, expected, actual))
    return H0Run(index=index, results=tuple(results))
