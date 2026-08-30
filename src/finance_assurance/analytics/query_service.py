"""Strict exact-original Artifact Q query assemblers."""

from __future__ import annotations

from typing import cast

from finance_assurance.analytics.contracts import AnalyticalQuery, AnalyticalView
from finance_assurance.exports.serialization import canonical_json_bytes
from finance_assurance.runtime.application.queries import RuntimeQueryService
from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.persistence.models import ExactStoredRecord
from finance_assurance.runtime.persistence.ports import QuerySession


class AnalyticalReadError(ValueError):
    """A strict Artifact Q exact read could not be satisfied."""


def _body(record: ExactStoredRecord) -> dict[str, object]:
    value = record.semantic_body()
    if not isinstance(value, dict):
        raise AnalyticalReadError("authoritative body is not an object")
    return value


def _record(record: ExactStoredRecord) -> dict[str, object]:
    return {
        "record_family": record.record_family,
        "record_identity": record.record_identity,
        "semantic_hash": record.semantic_hash,
        "body": _body(record),
    }


def _family_ref(record: ExactStoredRecord) -> str:
    return f"{record.record_family}:{record.record_identity}"


class AnalyticalQueryService:
    """Execute the finite Q-Q01..Q-Q06 registry in one pinned session."""

    def execute_in_session(
        self,
        request: AnalyticalQuery,
        session: QuerySession,
    ) -> AnalyticalView:
        runtime = RuntimeQueryService.from_session(session)
        dispatch = {
            "Q-Q01": self._catalogue,
            "Q-Q02": self._journal,
            "Q-Q03": self._business_event,
            "Q-Q04": self._referenced_journal,
            "Q-Q05": self._period,
            "Q-Q06": self._posting_rule,
        }
        data, sources = dispatch[request.query_id](request, session, runtime)
        view_contract = request.query_id.replace("Q-Q", "Q-V")
        return AnalyticalView(
            view_contract=cast(str, view_contract),
            view_contract_version=1,
            query_id=request.query_id,
            scenario_ref=request.scenario_ref,
            query_revision=session.revision,
            semantic_as_of_time=request.semantic_as_of_time,
            compatibility_mode="EXACT_ORIGINAL",
            source_refs=tuple(sources),
            data=data,
        )

    @staticmethod
    def _exact(session: QuerySession, family: str, identity: str) -> ExactStoredRecord:
        record = session.authoritative_record(family, identity)
        if record is None:
            raise AnalyticalReadError(f"exact {family}:{identity} is unavailable")
        return record

    def _evidence_sources(
        self,
        session: QuerySession,
        body: dict[str, object],
    ) -> tuple[ExactStoredRecord, ...]:
        values = body.get("evidence_refs", [])
        if not isinstance(values, list):
            raise AnalyticalReadError("evidence_refs is not a list")
        records: list[ExactStoredRecord] = []
        for value in values:
            if not isinstance(value, dict):
                raise AnalyticalReadError("evidence reference is invalid")
            identity = value.get("ref_id", value.get("record_identity"))
            if not isinstance(identity, str):
                raise AnalyticalReadError("evidence reference is invalid")
            exact = self._exact(session, "J-AR12", identity)
            expected_hash = value.get("semantic_hash")
            if expected_hash is not None and expected_hash != exact.semantic_hash:
                raise AnalyticalReadError("exact evidence authority hash differs")
            records.append(exact)
        return tuple({item.record_identity: item for item in records}.values())

    def _catalogue(self, request: AnalyticalQuery, session: QuerySession, runtime: RuntimeQueryService) -> tuple[dict[str, object], list[str]]:
        exact = runtime.get_exact("J-AR04", str(request.subject_ref))
        if exact is None:
            raise AnalyticalReadError("ledger catalogue is unavailable")
        body = _body(exact.record)
        if body.get("catalog_ref") != request.subject_ref or set(body) != {
            "contract_version", "catalog_id", "catalog_version", "catalog_ref",
            "effective_from", "effective_to", "status", "accounts",
            "statement_lines", "mappings", "evidence_refs",
        }:
            raise AnalyticalReadError("ledger catalogue contract is invalid")
        evidence = self._evidence_sources(session, body)
        return {"catalogue": _record(exact.record)}, [
            _family_ref(exact.record), *(_family_ref(item) for item in evidence)
        ]

    def _journal(self, request: AnalyticalQuery, session: QuerySession, runtime: RuntimeQueryService) -> tuple[dict[str, object], list[str]]:
        journal = runtime.get_journal(str(request.subject_ref))
        if journal is None:
            raise AnalyticalReadError("journal is unavailable")
        header = journal.header.record
        header_body = _body(header)
        proposal_ref = str(header_body["source_proposal_ref"])
        proposal = self._exact(session, "J-AR05", proposal_ref)
        proposal_body = _body(proposal)
        posting = self._exact(session, "J-AR06", str(header_body["posted_by_event_id"]))
        sources = [header, *(item.record for item in journal.ordered_lines), proposal, posting]
        predecessor: ExactStoredRecord | None = None
        origin = proposal_body.get("origin_basis")
        if not isinstance(origin, dict):
            raise AnalyticalReadError("proposal origin basis is invalid")
        if proposal_body.get("origin_type") == "RESTATEMENT_ADJUSTMENT":
            predecessor_ref = origin.get("predecessor_proposal_ref")
            if not isinstance(predecessor_ref, str):
                raise AnalyticalReadError("restatement predecessor is absent")
            predecessor = self._exact(session, "J-AR05", predecessor_ref)
            predecessor_body = _body(predecessor)
            if predecessor_body.get("origin_type") != "AUTOMATED_POSTING":
                raise AnalyticalReadError("predecessor origin is not automated")
            if isinstance(predecessor_body.get("origin_basis"), dict) and "predecessor_proposal_ref" in predecessor_body["origin_basis"]:
                raise AnalyticalReadError("a second predecessor hop is prohibited")
            sources.append(predecessor)
        elif proposal_body.get("origin_type") == "REVERSAL":
            source_id = origin.get("reverses_journal_id")
            if not isinstance(source_id, str):
                raise AnalyticalReadError("reversal source journal is absent")
            source = self._exact(session, "J-AR17", source_id)
            input_hashes = origin.get("input_hashes")
            if input_hashes != [source.semantic_hash]:
                raise AnalyticalReadError("reversal source hash is not bound")
            sources.append(source)
        evidence_records = (
            *self._evidence_sources(session, header_body),
            *self._evidence_sources(session, proposal_body),
            *self._evidence_sources(session, _body(posting)),
        )
        sources.extend(evidence_records)
        if proposal_body.get("origin_type") == "REVERSAL":
            # Artifact Q fixes one narrow source-closure collapse: the reversal
            # proposal and posting event share one exact evidence authority.
            sources = list(
                {
                    (item.record_family, item.record_identity): item
                    for item in sources
                }.values()
            )
        return {
            "journal": _record(header),
            "lines": [_record(item.record) for item in journal.ordered_lines],
            "proposal": _record(proposal),
            "posting_event": _record(posting),
            "predecessor_proposal": None if predecessor is None else _record(predecessor),
        }, [_family_ref(item) for item in sources]

    def _business_event(self, request: AnalyticalQuery, session: QuerySession, runtime: RuntimeQueryService) -> tuple[dict[str, object], list[str]]:
        exact = runtime.get_business_event(str(request.subject_ref))
        if exact is None:
            raise AnalyticalReadError("business event is unavailable")
        evidence = self._evidence_sources(session, _body(exact.record))
        return {"business_event": _record(exact.record)}, [
            _family_ref(exact.record), *(_family_ref(item) for item in evidence)
        ]

    def _referenced_journal(self, request: AnalyticalQuery, session: QuerySession, runtime: RuntimeQueryService) -> tuple[dict[str, object], list[str]]:
        source = self._exact(session, "J-AR17", str(request.subject_ref))
        source_body = _body(source)
        matches = []
        for record in session.authoritative_records("J-AR13"):
            body = _body(record)
            payload = body.get("canonical_payload")
            if body.get("contract_id") == "G-13" and isinstance(payload, dict) and payload.get("journal_id") == request.subject_ref:
                matches.append(record)
        if len(matches) != 1:
            raise AnalyticalReadError("G-13 referenced-journal publication is ambiguous")
        publication = matches[0]
        publication_body = _body(publication)
        payload = publication_body.get("canonical_payload")
        if not isinstance(payload, dict):
            raise AnalyticalReadError("G-13 payload is invalid")
        upstream = publication_body.get("upstream_authoritative_refs")
        if not isinstance(upstream, list) or len(upstream) != 1:
            raise AnalyticalReadError("G-13 upstream authority is not singular")
        authoritative = upstream[0].get("authoritative_ref") if isinstance(upstream[0], dict) else None
        expected = {
            "record_family": "J-AR17",
            "record_identity": source.record_identity,
            "semantic_hash": source.semantic_hash,
        }
        if authoritative != expected or payload.get("source_hash") != source.semantic_hash:
            raise AnalyticalReadError("G-13 source binding failed")
        shared = ("journal_id", "ledger_period_id", "currency", "line_tuples")
        if any(payload.get(field) != source_body.get(field) for field in shared):
            raise AnalyticalReadError("G-13 shared source fields differ")
        evidence = self._evidence_sources(session, publication_body)
        return {"source": _record(source), "publication": _record(publication)}, [
            _family_ref(source), _family_ref(publication), *(_family_ref(item) for item in evidence)
        ]

    def _period(self, request: AnalyticalQuery, session: QuerySession, runtime: RuntimeQueryService) -> tuple[dict[str, object], list[str]]:
        if request.state_basis_type == "BASE_FACT":
            exact = self._exact(session, "J-AR07", str(request.subject_ref))
            return {"state_basis_type": "BASE_FACT", "base_fact": _record(exact), "publication": None, "transition_event": None}, [_family_ref(exact)]
        assert request.state_token is not None
        read = runtime.get_accounting_period_exact(str(request.subject_ref), str(request.state_token))
        if read is None:
            raise AnalyticalReadError("period transition publication is unavailable")
        publication = read.state_publication.record
        transition = self._exact(session, "J-AR06", str(request.state_token))
        evidence = self._evidence_sources(session, _body(transition))
        return {"state_basis_type": "TRANSITION_PUBLICATION", "base_fact": None, "publication": _record(publication), "transition_event": _record(transition)}, [
            _family_ref(publication), _family_ref(transition), *(_family_ref(item) for item in evidence)
        ]

    def _posting_rule(self, request: AnalyticalQuery, session: QuerySession, runtime: RuntimeQueryService) -> tuple[dict[str, object], list[str]]:
        exact = runtime.get_posting_rule(str(request.subject_ref))
        if exact is None:
            raise AnalyticalReadError("posting rule is unavailable")
        evidence = self._evidence_sources(session, _body(exact.record))
        return {"posting_rule": _record(exact.record)}, [
            _family_ref(exact.record), *(_family_ref(item) for item in evidence)
        ]


def query_instance_ref(request: AnalyticalQuery) -> str:
    return f"QRY:{canonical_sha256(request.model_dump(mode='json'))[7:31]}"


def canonical_shared_payload(value: dict[str, object]) -> bytes:
    """Expose the registered canonical serializer for bound-field tests."""

    return canonical_json_bytes(value)
