"""Canonical runtime construction and restart/rebuild acceptance proof."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory

from finance_assurance.runtime.application.models import (
    AccountingWorkflow,
    EventCreations,
    ProposalTreatmentVersion,
    ScriptedIdentityGenerator,
)
from finance_assurance.runtime.application.service import AccountingApplicationService
from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256
from finance_assurance.runtime.contracts.module import ContractPublication
from finance_assurance.runtime.contracts.objects import (
    AccountingPeriodBase,
    BusinessEvent,
    JournalEntryBase,
    JournalLine,
    JournalProposalBase,
    ReportingVersion,
    RestatementCaseBase,
)
from finance_assurance.runtime.persistence.codec import durable_hash, encode_durable
from finance_assurance.runtime.persistence.models import (
    AdmissionBundle,
    BaselineContext,
    ProjectionReplacement,
    RebuildContext,
    SealedAdmissionRecord,
)
from finance_assurance.runtime.persistence.sqlite import SqlitePersistenceBoundary
from finance_assurance.runtime.persistence.state import InMemoryState
from finance_assurance.validation.h2 import run_h2
from finance_assurance.validation.scenarios import replay_c001, replay_ct1


@dataclass(frozen=True, slots=True)
class RuntimeEquivalenceProof:
    family: str
    clean_start_digest: str
    restart_digest: str
    rebuilt_digest: str
    event_count: int
    publication_count: int

    @property
    def passed(self) -> bool:
        return (
            self.clean_start_digest == self.restart_digest == self.rebuilt_digest
        )


def sealed_record(
    family: str,
    identity: str,
    body: dict[str, object],
    *,
    owner: str = "PLATFORM",
) -> SealedAdmissionRecord:
    payload = canonical_bytes(body)
    return SealedAdmissionRecord(
        record_family=family,
        record_identity=identity,
        semantic_owner=owner,
        contract_version="1",
        canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        semantic_hash=canonical_sha256(body),
        canonical_payload=payload,
    )


def admit_runtime(
    path: Path,
    state: InMemoryState,
    *,
    additional_records: tuple[SealedAdmissionRecord, ...] = (),
) -> SqlitePersistenceBoundary:
    boundary = SqlitePersistenceBoundary(path)
    index = run_h2().index
    evidence = {
        str(ref.ref_id): ref
        for validated in (*index.canonical_objects, *index.events)
        for ref in getattr(validated.value, "evidence_refs", ())
    }
    encoded_snapshot = encode_durable(state.snapshot)
    projection_ref = "BASELINE-PHASE6:J-P04"
    projection_hash = durable_hash(encoded_snapshot)
    manifest = {
        "contract_version": 1,
        "manifest_ref": "BASELINE-PHASE6",
        "projection_ref": projection_ref,
        "projection_hash": projection_hash,
        "predecessor_event_refs": sorted(state.known_predecessor_event_ids),
    }
    context = BaselineContext(
        baseline_manifest_ref="BASELINE-PHASE6",
        baseline_manifest_contract_version="1",
        baseline_manifest_canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
        baseline_manifest_hash=canonical_sha256(manifest),
        semantic_as_of_time="2026-06-01T00:00:00Z",
        admitting_actor_ref="PHASE6-TEST",
    )
    unit = boundary.begin_runtime_baseline_admission(context)
    unit.stage_bundle(
        AdmissionBundle(
            declared_records=(
                sealed_record("J-AR04", "BASELINE-PHASE6", manifest),
                *tuple(
                    sealed_record(
                        "J-AR12",
                        str(item.ref_id),
                        item.model_dump(mode="json"),
                    )
                    for item in evidence.values()
                ),
                *additional_records,
            ),
            projection_replacements=(
                ProjectionReplacement(
                    projection_family="J-P04",
                    projection_token=projection_ref,
                    source_hash=projection_hash,
                    canonical_payload=encoded_snapshot,
                ),
            ),
        )
    )
    unit.commit(unit.validate())
    return boundary


def accounting_workflow(
    name: str,
) -> tuple[AccountingWorkflow, InMemoryState, InMemoryState]:
    index = run_h2().index
    replay = replay_c001(index) if name == "C001" else replay_ct1(index)
    commands = replay.commands
    events = tuple(
        command.accounting_event
        for command in commands
        if command.accounting_event is not None
    )
    proposal_objects = {
        item.proposal_ref: item
        for command in commands
        for item in command.immutable_creations
        if isinstance(item, JournalProposalBase)
    }
    refs = (
        ("P-551@v1", "P-551@v2")
        if name == "C001"
        else ("P-REV-010@v1", "P-REP-010@v1")
    )
    treatments = tuple(
        ProposalTreatmentVersion.from_proposal(proposal_objects[ref]) for ref in refs
    )
    creation_bundles = []
    for command in commands:
        event = command.accounting_event
        values = tuple(
            item
            for item in command.immutable_creations
            if isinstance(
                item,
                (
                    AccountingPeriodBase,
                    JournalEntryBase,
                    JournalLine,
                    ReportingVersion,
                    RestatementCaseBase,
                ),
            )
        )
        if event is not None and values:
            creation_bundles.append(EventCreations(str(event.event_id), values))
    business_event = next(
        (
            item
            for item in replay.initial_state.object_versions
            if isinstance(item, BusinessEvent)
        ),
        None,
    )
    workflow = AccountingWorkflow(
        family=name,  # type: ignore[arg-type]
        correlation_id=name.replace("001", "-001").replace("CT1", "CT-1"),
        treatments=treatments,
        event_templates=events,
        creations=tuple(creation_bundles),
        business_event=business_event,
    )
    return workflow, replay.initial_state, replay.state


def run_runtime_equivalence() -> tuple[RuntimeEquivalenceProof, ...]:
    """Execute both reference families and compare durable semantic states."""

    proofs: list[RuntimeEquivalenceProof] = []
    with TemporaryDirectory(prefix="finance-assurance-m2-") as directory:
        root = Path(directory)
        for family in ("C001", "CT1"):
            workflow, initial, _ = accounting_workflow(family)
            database = root / f"{family.lower()}.sqlite3"
            boundary = admit_runtime(database, initial)
            AccountingApplicationService(
                boundary,
                ScriptedIdentityGenerator(
                    {
                        "constructor_command": (
                            f"CMD-{family}-M2-CONSTRUCT-1",
                            f"CMD-{family}-M2-CONSTRUCT-2",
                        )
                    }
                ),
            ).execute_workflow(workflow)
            clean_digest = boundary.state.full_digest
            publication_count = sum(
                isinstance(item, ContractPublication)
                for item in boundary.state.object_versions
            )
            event_count = len(boundary.state.event_log)
            boundary.close()

            restarted = SqlitePersistenceBoundary(database)
            restart_digest = restarted.state.full_digest
            restarted.delete_projection_checkpoint()
            session = restarted.open_rebuild(
                RebuildContext(
                    semantic_as_of_time="2026-07-14T12:00:00Z",
                    requested_projection_families=("J-P02", "J-P04", "J-P06"),
                )
            )
            generation = session.begin_generation()
            session.promote(session.validate(session.rebuild(generation)))
            rebuilt_digest = restarted.state.full_digest
            restarted.close()
            proofs.append(
                RuntimeEquivalenceProof(
                    family=family,
                    clean_start_digest=clean_digest,
                    restart_digest=restart_digest,
                    rebuilt_digest=rebuilt_digest,
                    event_count=event_count,
                    publication_count=publication_count,
                )
            )
    return tuple(proofs)
