"""Transactional SQLite adapter for the Artifact K persistence boundary."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from threading import RLock

from pydantic import BaseModel

from finance_assurance.runtime.application.models import ProposalTreatmentVersion
from finance_assurance.runtime.canonical import canonical_bytes, canonical_sha256
from finance_assurance.runtime.contracts.events import (
    PeriodHardClosed,
    RestatementAdjustmentLinked,
    RestatementAdjustmentsReady,
    RestatementProposed,
)
from finance_assurance.runtime.contracts.evidence import ReportingContentRecord
from finance_assurance.runtime.contracts.module import (
    ContractPublication,
    ImportPublicationBasis,
    ReferencedJournalPublicationBasis,
    ValidatedModuleProduct,
)
from finance_assurance.runtime.contracts.objects import JournalEntryBase
from finance_assurance.runtime.digests import value_digest
from finance_assurance.runtime.persistence.codec import (
    decode_durable,
    durable_hash,
    encode_durable,
)
from finance_assurance.runtime.persistence.memory import (
    InMemoryPersistenceBoundary,
    InvariantFailure,
    _explicit_available_from,
    _state_exact_records,
    _visible_state,
    authoritative_family,
)
from finance_assurance.runtime.persistence.migrations import (
    LATEST_SCHEMA_VERSION,
    apply_migrations,
    schema_version,
)
from finance_assurance.runtime.persistence.models import (
    AdmissionBundle,
    AdmissionReceipt,
    BaselineContext,
    CommandContext,
    CommandResult,
    ExactStoredRecord,
    ImportContext,
    ModuleCommandOutcome,
    PreScopeReportingImportBundle,
    ProjectionGenerationRef,
    QueryContext,
    RebuildContext,
    RebuildReceipt,
    RebuiltProjectionSet,
    ReferencedJournalAdmissionBundle,
    ReferencedJournalContext,
    ValidatedProjectionGeneration,
)
from finance_assurance.runtime.persistence.projection import (
    ProjectionReplayError,
    replay_transition,
)
from finance_assurance.runtime.persistence.semantic_time import (
    BASELINE_AVAILABLE_FROM,
    instant,
    is_available,
    latest,
)
from finance_assurance.runtime.persistence.state import InMemoryState
from finance_assurance.runtime.planner import (
    ProposalState,
    RestatementState,
    StateSnapshot,
    TransitionPlan,
)

FaultInjector = Callable[[str], None]

_CODEC_VERSION = "CLOSED_RUNTIME_JSON_V1"
_CANONICALIZATION_VERSION = "SORTED_KEYS_COMPACT_UTF8_V1"


class DurableStateError(RuntimeError):
    """Raised when persisted runtime state is absent, corrupt, or inconsistent."""


class AdmissionConflict(RuntimeError):
    """Raised when a sealed admission identity conflicts with durable state."""


_ADMISSION_RULES = {
    "RUNTIME_BASELINE": (
        frozenset({"J-AR02", "J-AR04", "J-AR07", "J-AR12"}),
        frozenset({"J-P04", "J-P05", "J-P10", "J-P11"}),
    ),
    "PRE_SCOPE_REPORTING": (
        frozenset({"J-AR10", "J-AR11", "J-AR12", "J-AR13"}),
        frozenset({"J-P08", "J-P09", "J-P11"}),
    ),
    "REFERENCED_JOURNAL": (
        frozenset({"J-AR17", "J-AR13"}),
        frozenset({"J-P09", "J-P11", "J-P12"}),
    ),
}
def _decode_baseline_projection(payload: bytes) -> StateSnapshot:
    decoded = decode_durable(payload, StateSnapshot)
    assert isinstance(decoded, StateSnapshot)
    return decoded
_ADMISSION_OWNERS = {
    "RUNTIME_BASELINE": {
        "J-AR02": frozenset({"SourceDomain", "HERMES"}),
        "J-AR04": frozenset({"PLATFORM", "ATLAS", "AEGIS", "PYTHIA"}),
        "J-AR07": frozenset({"ATLAS"}),
        "J-AR12": frozenset({"PLATFORM"}),
    },
    "PRE_SCOPE_REPORTING": {
        "J-AR10": frozenset({"ATLAS"}),
        "J-AR11": frozenset({"PLATFORM"}),
        "J-AR12": frozenset({"PLATFORM"}),
        "J-AR13": frozenset({"ATLAS"}),
    },
    "REFERENCED_JOURNAL": {
        "J-AR17": frozenset({"ATLAS"}),
        "J-AR13": frozenset({"ATLAS"}),
    },
}


def _identity(value: BaseModel) -> str:
    if isinstance(value, ReportingContentRecord):
        return str(value.content_ref)
    for field in (
        "publication_ref",
        "product_ref",
        "business_event_id",
        "posting_rule_ref",
        "event_id",
        "journal_line_id",
        "journal_id",
        "reporting_version_ref",
        "proposal_ref",
        "case_id",
        "period_id",
    ):
        candidate = getattr(value, field, None)
        if candidate is not None:
            return str(candidate)
    return value_digest(value)


def _authoritative_only(state: InMemoryState) -> InMemoryState:
    return replace(state, snapshot=StateSnapshot())


def _combine(
    authoritative: InMemoryState,
    projection: StateSnapshot,
) -> InMemoryState:
    return replace(authoritative, snapshot=projection)


class SqliteQuerySession:
    """Read-only exact/current session over one immutable loaded revision."""

    def __init__(
        self,
        boundary: SqlitePersistenceBoundary,
        state: InMemoryState,
        revision: int,
        context: QueryContext,
    ) -> None:
        self._boundary = boundary
        self._state = state
        self._revision = revision
        self._records = tuple(
            item
            for item in self._read_exact_records()
            if is_available(item.available_from, context.semantic_as_of_time)
        )
        self._state = _visible_state(
            state,
            self._records,
            baseline_snapshot=(
                boundary._baseline_snapshot
                if is_available(
                    boundary._baseline_available_from,
                    context.semantic_as_of_time,
                )
                else StateSnapshot()
            ),
            baseline_command_ids=boundary._baseline_command_ids,
        )

    @property
    def revision(self) -> int:
        return self._revision

    def state(self) -> InMemoryState:
        return self._state

    def command_result(self, command_id: str) -> CommandResult | None:
        return self._state.command_result(command_id)

    def authoritative_record(
        self,
        record_family: str,
        record_identity: str,
    ) -> ExactStoredRecord | None:
        return next(
            (
                item
                for item in self.authoritative_records(record_family)
                if item.record_identity == record_identity
            ),
            None,
        )

    def authoritative_records(
        self, record_family: str | None = None
    ) -> tuple[ExactStoredRecord, ...]:
        if record_family is None:
            return self._records
        return tuple(
            item for item in self._records if item.record_family == record_family
        )

    def _read_exact_records(self) -> tuple[ExactStoredRecord, ...]:
        rows = self._boundary._connection.execute(
            """
            SELECT record_family, record_identity, semantic_hash, payload,
                   available_from
            FROM authoritative_records
            UNION ALL
            SELECT 'J-AR15', idempotency_key, semantic_hash, payload,
                   available_from
            FROM effect_claims
            ORDER BY 1, 2
            """
        ).fetchall()
        records = {
            (str(row[0]), str(row[1])): ExactStoredRecord(
                record_family=str(row[0]),
                record_identity=str(row[1]),
                semantic_hash=str(row[2]),
                canonical_payload=bytes(row[3]),
                available_from=str(row[4]),
            )
            for row in rows
        }
        for item in _state_exact_records(self._state, self._boundary._contexts):
            key = (item.record_family, item.record_identity)
            prior = records.get(key)
            if prior is not None and (
                prior.semantic_hash != item.semantic_hash
                or prior.available_from != item.available_from
            ):
                raise DurableStateError(
                    "exact record and authoritative state metadata disagree"
                )
            records.setdefault(key, item)
        ordered = tuple(records[key] for key in sorted(records))
        return ordered


class SqliteRebuildSession:
    """Projection-only rebuild mode over declared baseline and command results."""

    def __init__(
        self,
        boundary: SqlitePersistenceBoundary,
        context: RebuildContext,
    ) -> None:
        self._boundary = boundary
        self._context = context
        self._closed = False
        self._generation: ProjectionGenerationRef | None = None
        self._rebuilt: RebuiltProjectionSet | None = None

    def context(self) -> RebuildContext:
        return self._context

    def begin_generation(self) -> ProjectionGenerationRef:
        if self._closed or self._generation is not None:
            raise DurableStateError("rebuild generation is already open")
        self._generation = ProjectionGenerationRef(
            generation_id=(
                f"projection-generation:{self._boundary.revision}:"
                f"{self._boundary.state.full_digest}"
            ),
            source_revision=self._boundary.revision,
        )
        return self._generation

    def rebuild(self, generation: ProjectionGenerationRef) -> RebuiltProjectionSet:
        if self._closed or generation is not self._generation:
            raise DurableStateError("rebuild generation is not active")
        self._rebuilt = self._boundary._build_projection(generation)
        return self._rebuilt

    def validate(
        self,
        rebuilt: RebuiltProjectionSet,
    ) -> ValidatedProjectionGeneration:
        if self._closed or rebuilt is not self._rebuilt:
            raise DurableStateError("projection set was not rebuilt by this session")
        if rebuilt.generation_ref.source_revision != self._boundary.revision:
            raise DurableStateError("rebuild source revision is stale")
        if value_digest(rebuilt.projection) != value_digest(
            self._boundary.state.snapshot
        ):
            raise DurableStateError(
                "declared authoritative inputs do not reproduce the projection"
            )
        return ValidatedProjectionGeneration(rebuilt.generation_ref, rebuilt)

    def promote(
        self,
        validated: ValidatedProjectionGeneration,
    ) -> RebuildReceipt:
        if (
            self._closed
            or self._rebuilt is None
            or validated.projection_set is not self._rebuilt
        ):
            raise DurableStateError("projection generation was not validated")
        receipt = self._boundary._promote_projection(validated.projection_set)
        self._closed = True
        return receipt

    def abort(self, generation: ProjectionGenerationRef) -> None:
        if generation is not self._generation:
            raise DurableStateError("rebuild generation is not active")
        self._rebuilt = None
        self._closed = True

    def rollback(self) -> None:
        if self._generation is not None:
            self.abort(self._generation)
        else:
            self._closed = True


class SqliteAdmissionUnitOfWork:
    """One sealed, non-command administrative admission transaction."""

    def __init__(
        self,
        boundary: SqlitePersistenceBoundary,
        mode: str,
        admission_id: str,
        context: object,
    ) -> None:
        self._boundary = boundary
        self._mode = mode
        self._admission_id = admission_id
        self._context = context
        self._bundle: AdmissionBundle | None = None
        self._digest: str | None = None
        self._available_from: str | None = None
        self._closed = False

    def context(self) -> object:
        return self._context

    def prior_receipt(self) -> AdmissionReceipt | None:
        row = self._boundary._connection.execute(
            """
            SELECT input_digest, committed_revision FROM admission_registry
            WHERE admission_mode = ? AND admission_id = ?
            """,
            (self._mode, self._admission_id),
        ).fetchone()
        if row is None:
            return None
        return AdmissionReceipt(
            admission_mode=self._mode,  # type: ignore[arg-type]
            admission_id=self._admission_id,
            input_digest=str(row[0]),
            revision=int(row[1]),
            replayed=True,
        )

    def stage_bundle(self, bundle: AdmissionBundle) -> None:
        if self._closed or self._bundle is not None:
            raise AdmissionConflict("admission unit is closed or already staged")
        self._bundle = bundle

    def validate(self) -> str:
        if self._bundle is None:
            raise AdmissionConflict("admission bundle is not staged")
        allowed_records, allowed_projections = _ADMISSION_RULES[self._mode]
        owners = _ADMISSION_OWNERS[self._mode]
        identities: set[tuple[str, str]] = set()
        baseline_products: list[ValidatedModuleProduct] = []
        for record in self._bundle.declared_records:
            identity = (record.record_family, record.record_identity)
            if record.record_family not in allowed_records:
                raise AdmissionConflict(
                    f"{record.record_family} is not permitted in {self._mode}"
                )
            if identity in identities:
                raise AdmissionConflict("admission record identity is duplicated")
            identities.add(identity)
            if record.semantic_owner not in owners[record.record_family]:
                raise AdmissionConflict(
                    f"{record.semantic_owner} cannot own {record.record_family}"
                )
            try:
                parsed = json.loads(record.canonical_payload)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise AdmissionConflict("admission payload is not JSON") from error
            if canonical_bytes(parsed) != record.canonical_payload:
                raise AdmissionConflict("admission payload is not canonical")
            if record.record_family == "J-AR02":
                try:
                    product = ValidatedModuleProduct.model_validate(parsed)
                except ValueError as error:
                    raise AdmissionConflict(
                        "baseline module product is not registered"
                    ) from error
                if (
                    product.semantic_hash != record.semantic_hash
                    or product.creation_basis.basis_type != "BASELINE"
                    or product.creation_basis.baseline_manifest_ref
                    != self._admission_id
                ):
                    raise AdmissionConflict(
                        "baseline module-product binding is inconsistent"
                    )
                baseline_products.append(product)
            elif canonical_sha256(parsed) != record.semantic_hash:
                raise AdmissionConflict("admission payload hash does not match")
        for projection in self._bundle.projection_replacements:
            if projection.projection_family not in allowed_projections:
                raise AdmissionConflict(
                    f"{projection.projection_family} is not permitted in {self._mode}"
                )
            try:
                parsed_projection = json.loads(projection.canonical_payload)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise AdmissionConflict("projection payload is not JSON") from error
            if canonical_bytes(parsed_projection) != projection.canonical_payload:
                raise AdmissionConflict("projection payload is not canonical")
            if canonical_sha256(parsed_projection) != projection.source_hash:
                raise AdmissionConflict("projection source hash does not match")
        if self._mode == "RUNTIME_BASELINE":
            if not isinstance(self._context, BaselineContext):
                raise AdmissionConflict("baseline context type is invalid")
            manifest = next(
                (
                    item
                    for item in self._bundle.declared_records
                    if item.record_family == "J-AR04"
                    and item.record_identity == self._admission_id
                ),
                None,
            )
            if manifest is None:
                raise AdmissionConflict("baseline manifest record is absent")
            if manifest.semantic_hash != self._context.baseline_manifest_hash:
                raise AdmissionConflict("baseline context does not bind its manifest")
            declared = {
                (item.record_family, item.record_identity): item
                for item in self._bundle.declared_records
            }
            baseline_products_by_ref = {
                product.product_ref: product for product in baseline_products
            }
            for product in baseline_products:
                if product.upstream_publication_refs:
                    raise AdmissionConflict(
                        "baseline module product cannot consume a G publication"
                    )
                for evidence_ref in product.evidence_refs:
                    evidence = declared.get(
                        (
                            str(evidence_ref.record_family),
                            str(evidence_ref.record_identity),
                        )
                    )
                    if (
                        evidence is None
                        or evidence.semantic_hash != evidence_ref.semantic_hash
                    ):
                        raise AdmissionConflict(
                            "baseline module-product evidence is unavailable "
                            "or not exact"
                        )
                for semantic_ref in product.upstream_authoritative_refs:
                    if semantic_ref.ref_kind == "PUBLICATION":
                        raise AdmissionConflict(
                            "baseline module product cannot consume a G publication"
                        )
                    if semantic_ref.ref_kind == "MODULE_PRODUCT":
                        assert semantic_ref.module_product_ref is not None
                        ref = semantic_ref.module_product_ref.product_authoritative_ref
                        target_product = baseline_products_by_ref.get(
                            semantic_ref.module_product_ref.product_ref
                        )
                        if (
                            target_product is None
                            or target_product.exact_ref()
                            != semantic_ref.module_product_ref
                        ):
                            raise AdmissionConflict(
                                "baseline module-product reference is not exact"
                            )
                    else:
                        assert semantic_ref.authoritative_ref is not None
                        ref = semantic_ref.authoritative_ref
                    target = declared.get(
                        (str(ref.record_family), str(ref.record_identity))
                    )
                    if target is None or target.semantic_hash != ref.semantic_hash:
                        raise AdmissionConflict(
                            "baseline upstream reference is unavailable or not exact"
                        )
            self._available_from = self._context.semantic_as_of_time
        elif self._mode == "PRE_SCOPE_REPORTING":
            if not isinstance(self._context, ImportContext):
                raise AdmissionConflict("pre-scope import context type is invalid")
            if not isinstance(self._bundle, PreScopeReportingImportBundle):
                raise AdmissionConflict("pre-scope import bundle type is invalid")
            try:
                candidate = json.loads(self._bundle.sealed_candidate_body)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise AdmissionConflict("sealed candidate is not JSON") from error
            if (
                not isinstance(candidate, dict)
                or canonical_bytes(candidate) != self._bundle.sealed_candidate_body
                or canonical_sha256(candidate) != self._context.sealed_candidate_hash
                or candidate.get("candidate_ref")
                != self._context.imported_reporting_version_ref
                or self._context.sealed_candidate_contract_version != "1"
                or self._context.sealed_candidate_canonicalization_version
                != _CANONICALIZATION_VERSION
                or not self._bundle.prerequisite_period_ref
                or not self._bundle.prerequisite_close_event_ref
                or not self._bundle.prerequisite_close_view_hash
            ):
                raise AdmissionConflict("pre-scope import prerequisites are invalid")
            families = {item.record_family for item in self._bundle.declared_records}
            if families != {"J-AR10", "J-AR11", "J-AR12", "J-AR13"}:
                raise AdmissionConflict("pre-scope import set is incomplete")
            self._available_from = self._validate_pre_scope_import()
        elif self._mode == "REFERENCED_JOURNAL":
            if not isinstance(self._context, ReferencedJournalContext):
                raise AdmissionConflict("referenced-journal context type is invalid")
            if not isinstance(self._bundle, ReferencedJournalAdmissionBundle):
                raise AdmissionConflict("referenced-journal bundle type is invalid")
            by_family = {
                item.record_family: item
                for item in self._bundle.declared_records
            }
            if set(by_family) != {"J-AR17", "J-AR13"}:
                raise AdmissionConflict(
                    "referenced-journal admission set is incomplete"
                )
            source = by_family["J-AR17"]
            publication_body = json.loads(by_family["J-AR13"].canonical_payload)
            try:
                publication = ContractPublication.model_validate_json(
                    canonical_bytes(publication_body)
                )
            except ValueError as error:
                raise AdmissionConflict(
                    "referenced-journal G-13 contract is invalid"
                ) from error
            try:
                publication = ContractPublication.model_validate(publication_body)
            except ValueError as error:
                raise AdmissionConflict(
                    "referenced-journal G-13 contract is invalid"
                ) from error
            try:
                provenance = json.loads(self._bundle.provenance_body)
            except (UnicodeDecodeError, json.JSONDecodeError) as error:
                raise AdmissionConflict("referenced provenance is not JSON") from error
            if (
                source.record_identity != self._context.source_journal_ref
                or source.semantic_hash != self._context.source_hash
                or source.canonical_payload != self._bundle.canonical_source_body
                or canonical_bytes(provenance) != self._bundle.provenance_body
                or publication.contract_id != "G-13"
                or not isinstance(
                    publication.publication_basis,
                    ReferencedJournalPublicationBasis,
                )
                or publication.publication_basis.referenced_source_ref
                != source.record_identity
                or publication.canonical_payload.get("journal_id")
                != source.record_identity
                or publication.canonical_payload.get("source_hash")
                != source.semantic_hash
            ):
                raise AdmissionConflict(
                    "referenced source and G-13 publication are not hash-bound"
                )
            self._available_from = str(publication.available_from)
        self._digest = value_digest(
            (
                self._mode,
                self._admission_id,
                tuple(
                    (
                        item.record_family,
                        item.record_identity,
                        item.semantic_hash,
                    )
                    for item in self._bundle.declared_records
                ),
                tuple(
                    (
                        item.projection_family,
                        item.projection_token,
                        item.source_hash,
                    )
                    for item in self._bundle.projection_replacements
                ),
            )
        )
        return self._digest

    def _validate_pre_scope_import(self) -> str:
        assert isinstance(self._context, ImportContext)
        assert isinstance(self._bundle, PreScopeReportingImportBundle)
        by_family = {
            item.record_family: item for item in self._bundle.declared_records
        }
        core_record = by_family["J-AR10"]
        attestation_record = by_family["J-AR11"]
        content_record = by_family["J-AR12"]
        publication_record = by_family["J-AR13"]
        if (
            core_record.record_identity
            != self._context.imported_reporting_version_ref
            or attestation_record.record_identity != self._context.import_id
        ):
            raise AdmissionConflict("pre-scope import context binding is invalid")
        try:
            core = json.loads(core_record.canonical_payload)
            attestation = json.loads(attestation_record.canonical_payload)
            content = ReportingContentRecord.model_validate_json(
                content_record.canonical_payload
            )
            publication = ContractPublication.model_validate_json(
                publication_record.canonical_payload
            )
        except (ValueError, KeyError) as error:
            raise AdmissionConflict("pre-scope import bodies are invalid") from error

        required_attestation = {
            "import_id",
            "imported_object_type",
            "reporting_version_ref",
            "canonical_core_hash",
            "content_ref",
            "content_hash",
            "content_schema_version",
            "prerequisite_period_id",
            "prerequisite_close_event_id",
            "prerequisite_close_view_hash",
            "original_published_at",
            "available_from",
            "original_authority_ref",
            "source_ref",
            "imported_at",
            "imported_by",
            "import_command_or_manifest_ref",
            "evidence_refs",
        }
        if not required_attestation.issubset(attestation):
            raise AdmissionConflict("pre-scope import attestation is incomplete")
        if any(
            attestation.get(key) in (None, "", []) for key in required_attestation
        ):
            raise AdmissionConflict("pre-scope import attestation has empty fields")

        period = self._boundary.state.snapshot.period(
            self._bundle.prerequisite_period_ref
        )
        close_events = [
            item
            for item in self._boundary.state.event_log
            if isinstance(item, PeriodHardClosed)
            and str(item.event_id) == self._bundle.prerequisite_close_event_ref
            and str(item.payload.period_id) == self._bundle.prerequisite_period_ref
        ]
        if (
            period is None
            or period.status != "HARD_CLOSED"
            or len(close_events) != 1
            or value_digest(period) != self._bundle.prerequisite_close_view_hash
        ):
            raise AdmissionConflict(
                "pre-scope import hard-close authority does not resolve exactly"
            )
        close_event = close_events[0]

        original_published_at = str(attestation["original_published_at"])
        imported_at = str(attestation["imported_at"])
        available_from = str(attestation["available_from"])
        try:
            ordered_floor = latest(
                str(close_event.occurred_at),
                str(close_event.recorded_at),
                original_published_at,
                imported_at,
            )
            if instant(available_from) < instant(ordered_floor):
                raise AdmissionConflict(
                    "pre-scope import availability precedes its authority"
                )
            if instant(original_published_at) < instant(close_event.recorded_at):
                raise AdmissionConflict(
                    "original publication precedes the exact hard close"
                )
            if instant(imported_at) < instant(original_published_at):
                raise AdmissionConflict("import precedes original publication")
        except ValueError as error:
            raise AdmissionConflict(
                "pre-scope import timestamps are invalid"
            ) from error

        content_body = content.canonical_body.model_dump(mode="json")
        expected_attestation = {
            "import_id": self._context.import_id,
            "imported_object_type": "reporting_version",
            "reporting_version_ref": self._context.imported_reporting_version_ref,
            "canonical_core_hash": core_record.semantic_hash,
            "content_ref": str(content.content_ref),
            "content_hash": str(content.content_hash),
            "content_schema_version": content.content_schema_version,
            "prerequisite_period_id": self._bundle.prerequisite_period_ref,
            "prerequisite_close_event_id": (
                self._bundle.prerequisite_close_event_ref
            ),
            "prerequisite_close_view_hash": (
                self._bundle.prerequisite_close_view_hash
            ),
            "original_published_at": str(core.get("published_at")),
            "available_from": str(publication.available_from),
            "original_authority_ref": publication.canonical_payload.get(
                "original_authority_ref"
            ),
            "source_ref": publication.canonical_payload.get("source_ref"),
            "imported_at": self._context.semantic_as_of_time,
            "imported_by": self._context.importer_ref,
        }
        if any(
            attestation.get(key) != value
            for key, value in expected_attestation.items()
        ):
            raise AdmissionConflict("pre-scope import attestation binding is invalid")
        if (
            canonical_sha256(content_body) != str(content.content_hash)
            or content_record.record_identity != str(content.content_ref)
            or core.get("reporting_version_ref")
            != self._context.imported_reporting_version_ref
            or core.get("period_id") != self._bundle.prerequisite_period_ref
            or core.get("content_ref") != str(content.content_ref)
            or core.get("content_hash") != str(content.content_hash)
            or core.get("content_schema_version") != content.content_schema_version
            or core.get("publication_origin") != "PRE_SCOPE_IMPORT"
            or publication.contract_id != "G-06"
            or publication_record.record_identity != str(publication.publication_ref)
            or publication.product_ref
            != self._context.imported_reporting_version_ref
            or publication.payload_hash
            != canonical_sha256(publication.canonical_payload)
            or any(
                publication.canonical_payload.get(key) != core.get(key)
                for key in (
                    "reporting_version_ref",
                    "period_id",
                    "content_ref",
                    "content_hash",
                    "content_schema_version",
                    "publication_origin",
                    "published_at",
                )
            )
            or not isinstance(publication.publication_basis, ImportPublicationBasis)
            or publication.publication_basis.import_attestation_ref
            != f"J-AR11:{self._context.import_id}"
        ):
            raise AdmissionConflict(
                "pre-scope reporting core, content, and G-06 are not bound"
            )
        return available_from

    def commit(self, validated_digest: str) -> AdmissionReceipt:
        if (
            self._closed
            or self._bundle is None
            or self._digest is None
            or self._available_from is None
            or validated_digest != self._digest
        ):
            raise AdmissionConflict("admission bundle was not validated by this unit")
        boundary = self._boundary
        with boundary._lock:
            prior = self.prior_receipt()
            if prior is not None:
                self._closed = True
                if prior.input_digest != self._digest:
                    raise AdmissionConflict(
                        "admission identity is bound to different content"
                    )
                return prior
            if self._mode != "RUNTIME_BASELINE" and not boundary._has_persisted_state():
                raise AdmissionConflict("runtime baseline must be admitted first")
            if self._mode == "RUNTIME_BASELINE" and boundary._has_persisted_state():
                raise AdmissionConflict("runtime baseline is already present")
            next_revision = (
                0 if self._mode == "RUNTIME_BASELINE" else boundary._revision + 1
            )
            admitted_state = boundary._state
            boundary._connection.execute("BEGIN IMMEDIATE")
            try:
                persisted_revision = boundary._connection.execute(
                    "SELECT revision FROM runtime_metadata WHERE singleton_id = 1"
                ).fetchone()
                if (
                    self._mode != "RUNTIME_BASELINE"
                    and (
                        persisted_revision is None
                        or int(persisted_revision[0]) != boundary._revision
                    )
                ):
                    raise AdmissionConflict(
                        "durable revision changed before admission commit"
                    )
                if not boundary._has_persisted_state():
                    baseline_projections = [
                        item
                        for item in self._bundle.projection_replacements
                        if item.projection_family == "J-P04"
                    ]
                    if len(baseline_projections) != 1:
                        raise AdmissionConflict(
                            "baseline requires one J-P04 state projection"
                        )
                    baseline_projection = baseline_projections[0]
                    baseline_snapshot = _decode_baseline_projection(
                        baseline_projection.canonical_payload
                    )
                    admitted_state = InMemoryState.from_snapshot(
                        baseline_snapshot,
                        known_predecessor_event_ids=(
                            baseline_snapshot.accounting_event_ids
                            | {
                                item.record_identity
                                for item in self._bundle.declared_records
                                if item.record_family == "J-AR12"
                            }
                        ),
                    )
                    boundary._write_complete_state(
                        admitted_state,
                        revision=next_revision,
                    )
                    baseline_payload = encode_durable(baseline_snapshot)
                    boundary._connection.execute(
                        """
                        INSERT INTO baseline_projection(
                            singleton_id, manifest_id, payload, payload_hash,
                            source_record_family, source_record_identity
                        ) VALUES (1, ?, ?, ?, ?, ?)
                        """,
                        (
                            self._admission_id,
                            baseline_payload,
                            durable_hash(baseline_payload),
                            "J-AR04",
                            self._admission_id,
                        ),
                    )
                else:
                    boundary._write_complete_state(
                        boundary._state, revision=next_revision
                    )
                for ordinal, record in enumerate(self._bundle.declared_records):
                    boundary._connection.execute(
                        """
                        INSERT INTO authoritative_records(
                            record_family, record_identity, semantic_hash, payload,
                            command_id, record_ordinal, available_from
                        ) VALUES (?, ?, ?, ?, NULL, ?, ?)
                        """,
                        (
                            record.record_family,
                            record.record_identity,
                            record.semantic_hash,
                            record.canonical_payload,
                            ordinal,
                            self._available_from,
                        ),
                    )
                for projection in self._bundle.projection_replacements:
                    boundary._connection.execute(
                        """
                        INSERT INTO admission_projections(
                            admission_mode, admission_id, projection_family,
                            projection_token, source_hash, payload
                        ) VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (
                            self._mode,
                            self._admission_id,
                            projection.projection_family,
                            projection.projection_token,
                            projection.source_hash,
                            projection.canonical_payload,
                        ),
                    )
                boundary._connection.execute(
                    """
                    INSERT INTO admission_registry(
                        admission_mode, admission_id, input_digest,
                        committed_revision
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (self._mode, self._admission_id, self._digest, next_revision),
                )
                boundary._inject("admission_before_commit")
                boundary._connection.commit()
            except BaseException:
                boundary._connection.rollback()
                raise
            boundary._state = admitted_state
            if self._mode == "RUNTIME_BASELINE":
                boundary._baseline_snapshot = admitted_state.snapshot
                boundary._baseline_available_from = self._available_from
            boundary._revision = next_revision
            self._closed = True
            return AdmissionReceipt(
                admission_mode=self._mode,  # type: ignore[arg-type]
                admission_id=self._admission_id,
                input_digest=self._digest,
                revision=next_revision,
            )

    def rollback(self) -> None:
        self._bundle = None
        self._closed = True


class SqlitePersistenceBoundary(InMemoryPersistenceBoundary):
    """One durable, serializable, single-process persistence boundary."""

    def __init__(
        self,
        database: str | Path,
        *,
        fault_injector: FaultInjector | None = None,
    ) -> None:
        self._database = Path(database)
        self._connection = sqlite3.connect(
            self._database,
            isolation_level=None,
            check_same_thread=False,
        )
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._connection.execute("PRAGMA synchronous = FULL")
        apply_migrations(self._connection)
        self._backfill_record_availability()
        self._fault_injector = fault_injector
        loaded = self._load()
        super().__init__(loaded[0])
        self._contexts = loaded[1]
        self._revision = loaded[2]
        self._baseline_snapshot = self._load_baseline_snapshot()
        self._baseline_available_from = self._load_baseline_available_from()
        self._baseline_command_ids = frozenset()
        self._lock = RLock()

    @property
    def schema_version(self) -> int:
        return schema_version(self._connection)

    def close(self) -> None:
        self._connection.close()

    def __enter__(self) -> SqlitePersistenceBoundary:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def open_query(self, context: QueryContext) -> SqliteQuerySession:
        if not context.semantic_as_of_time:
            raise ValueError("query context requires semantic_as_of_time")
        with self._lock:
            return SqliteQuerySession(self, self._state, self._revision, context)

    def begin_runtime_baseline_admission(
        self,
        context: BaselineContext,
    ) -> SqliteAdmissionUnitOfWork:
        return SqliteAdmissionUnitOfWork(
            self,
            "RUNTIME_BASELINE",
            context.baseline_manifest_ref,
            context,
        )

    def begin_pre_scope_reporting_import(
        self,
        context: ImportContext,
    ) -> SqliteAdmissionUnitOfWork:
        return SqliteAdmissionUnitOfWork(
            self,
            "PRE_SCOPE_REPORTING",
            context.import_id,
            context,
        )

    def begin_referenced_journal_admission(
        self,
        context: ReferencedJournalContext,
    ) -> SqliteAdmissionUnitOfWork:
        return SqliteAdmissionUnitOfWork(
            self,
            "REFERENCED_JOURNAL",
            context.source_journal_ref,
            context,
        )

    def open_rebuild(self, context: RebuildContext) -> SqliteRebuildSession:
        if not context.semantic_as_of_time or not context.requested_projection_families:
            raise ValueError("rebuild context requires time and projection families")
        return SqliteRebuildSession(self, context)

    def delete_projection_checkpoint(self) -> None:
        """Delete only the disposable current projection checkpoint."""

        with self._lock:
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._connection.execute("DELETE FROM projection_checkpoint")
                self._connection.commit()
            except BaseException:
                self._connection.rollback()
                raise

    def _inject(self, stage: str) -> None:
        if self._fault_injector is not None:
            self._fault_injector(stage)

    def _has_persisted_state(self) -> bool:
        row = self._connection.execute(
            "SELECT 1 FROM current_authoritative_state WHERE singleton_id = 1"
        ).fetchone()
        return row is not None

    def _backfill_record_availability(self) -> None:
        """Upgrade pre-v4 rows without inventing later semantic availability."""

        null_records = self._connection.execute(
            """
            SELECT record_family, record_identity, payload, command_id
            FROM authoritative_records WHERE available_from IS NULL
            """
        ).fetchall()
        null_effects = self._connection.execute(
            """
            SELECT idempotency_key, command_id
            FROM effect_claims WHERE available_from IS NULL
            """
        ).fetchall()
        if not null_records and not null_effects:
            return
        context_times: dict[str, str] = {}
        for command_id, payload in self._connection.execute(
            "SELECT command_id, payload FROM command_contexts"
        ):
            decoded = decode_durable(bytes(payload), CommandContext)
            assert isinstance(decoded, CommandContext)
            context_times[str(command_id)] = decoded.semantic_as_of_time

        explicit_by_ref: dict[str, str] = {}
        parsed_rows: list[tuple[str, str, object, str | None]] = []
        for family, identity, payload, command_id in null_records:
            parsed = json.loads(bytes(payload))
            if isinstance(parsed, dict) and "$runtime_type" in parsed:
                parsed = parsed.get("value")
            parsed_rows.append(
                (
                    str(family),
                    str(identity),
                    parsed,
                    str(command_id) if command_id else None,
                )
            )
            if isinstance(parsed, dict) and isinstance(
                parsed.get("available_from"), str
            ):
                available = str(parsed["available_from"])
                explicit_by_ref[str(identity)] = available
                product_ref = parsed.get("product_ref")
                if isinstance(product_ref, str):
                    explicit_by_ref[product_ref] = available
                canonical_payload = parsed.get("canonical_payload")
                if isinstance(canonical_payload, dict):
                    for key in ("content_ref", "reporting_version_ref"):
                        value = canonical_payload.get(key)
                        if isinstance(value, str):
                            explicit_by_ref[value] = available

        self._connection.execute("BEGIN IMMEDIATE")
        try:
            for family, identity, parsed, command_id in parsed_rows:
                available = context_times.get(command_id or "")
                if available is None:
                    available = explicit_by_ref.get(identity)
                if available is None and isinstance(parsed, dict):
                    for key in (
                        "available_from",
                        "imported_at",
                        "attested_at",
                        "published_at",
                        "recorded_at",
                    ):
                        candidate = parsed.get(key)
                        if isinstance(candidate, str):
                            available = candidate
                            break
                    for key in ("content_ref", "reporting_version_ref"):
                        candidate = parsed.get(key)
                        if available is None and isinstance(candidate, str):
                            available = explicit_by_ref.get(candidate)
                if available is None:
                    available = BASELINE_AVAILABLE_FROM
                self._connection.execute(
                    """
                    UPDATE authoritative_records SET available_from = ?
                    WHERE record_family = ? AND record_identity = ?
                    """,
                    (available, family, identity),
                )
            for idempotency_key, command_id in null_effects:
                available = context_times.get(str(command_id), BASELINE_AVAILABLE_FROM)
                self._connection.execute(
                    """
                    UPDATE effect_claims SET available_from = ?
                    WHERE idempotency_key = ?
                    """,
                    (available, str(idempotency_key)),
                )
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise

    def _load_baseline_snapshot(self) -> StateSnapshot:
        row = self._connection.execute(
            """
            SELECT b.payload, b.payload_hash
            FROM baseline_projection AS b
            """
        ).fetchone()
        if row is None:
            return StateSnapshot()
        payload = bytes(row[0])
        if durable_hash(payload) != row[1]:
            raise DurableStateError("baseline-authority hash mismatch")
        return _decode_baseline_projection(payload)

    def _load_baseline_available_from(self) -> str:
        row = self._connection.execute(
            """
            SELECT a.available_from
            FROM baseline_projection AS b
            JOIN authoritative_records AS a
              ON a.record_family = b.source_record_family
             AND a.record_identity = b.source_record_identity
            """
        ).fetchone()
        return BASELINE_AVAILABLE_FROM if row is None else str(row[0])

    def _load(self) -> tuple[InMemoryState, dict[str, CommandContext], int]:
        metadata = self._connection.execute(
            """
            SELECT revision, codec_version, canonicalization_version
            FROM runtime_metadata WHERE singleton_id = 1
            """
        ).fetchone()
        if metadata is None:
            return InMemoryState(), {}, 0
        if metadata[1:] != (_CODEC_VERSION, _CANONICALIZATION_VERSION):
            raise DurableStateError("persisted runtime codec is not supported")
        authoritative_row = self._connection.execute(
            """
            SELECT payload, payload_hash FROM current_authoritative_state
            WHERE singleton_id = 1
            """
        ).fetchone()
        projection_row = self._connection.execute(
            """
            SELECT revision, authoritative_state_hash, payload, payload_hash
            FROM projection_checkpoint WHERE singleton_id = 1
            """
        ).fetchone()
        if authoritative_row is None or projection_row is None:
            raise DurableStateError(
                "authoritative state and projection checkpoint must both exist"
            )
        authoritative_payload = bytes(authoritative_row[0])
        projection_payload = bytes(projection_row[2])
        if durable_hash(authoritative_payload) != authoritative_row[1]:
            raise DurableStateError("authoritative-state hash mismatch")
        if durable_hash(projection_payload) != projection_row[3]:
            raise DurableStateError("projection-checkpoint hash mismatch")
        if projection_row[1] != authoritative_row[1]:
            raise DurableStateError("projection is not bound to authoritative state")
        if int(projection_row[0]) != int(metadata[0]):
            raise DurableStateError("projection revision is not current")
        authoritative = decode_durable(authoritative_payload, InMemoryState)
        projection = decode_durable(projection_payload, StateSnapshot)
        contexts: dict[str, CommandContext] = {}
        for command_id, payload, payload_hash in self._connection.execute(
            "SELECT command_id, payload, payload_hash FROM command_contexts"
        ):
            raw = bytes(payload)
            if durable_hash(raw) != payload_hash:
                raise DurableStateError(f"command-context hash mismatch: {command_id}")
            decoded = decode_durable(raw, CommandContext)
            assert isinstance(decoded, CommandContext)
            contexts[str(command_id)] = decoded
        assert isinstance(authoritative, InMemoryState)
        assert isinstance(projection, StateSnapshot)
        return _combine(authoritative, projection), contexts, int(metadata[0])

    def _write_complete_state(self, state: InMemoryState, *, revision: int) -> None:
        authoritative_payload = encode_durable(_authoritative_only(state))
        authoritative_hash = durable_hash(authoritative_payload)
        projection_payload = encode_durable(state.snapshot)
        projection_hash = durable_hash(projection_payload)
        self._connection.execute(
            """
            INSERT INTO runtime_metadata(
                singleton_id, revision, codec_version, canonicalization_version
            ) VALUES (1, ?, ?, ?)
            ON CONFLICT(singleton_id) DO UPDATE SET
                revision = excluded.revision,
                codec_version = excluded.codec_version,
                canonicalization_version = excluded.canonicalization_version
            """,
            (revision, _CODEC_VERSION, _CANONICALIZATION_VERSION),
        )
        self._connection.execute(
            """
            INSERT INTO current_authoritative_state(
                singleton_id, payload, payload_hash
            ) VALUES (1, ?, ?)
            ON CONFLICT(singleton_id) DO UPDATE SET
                payload = excluded.payload,
                payload_hash = excluded.payload_hash
            """,
            (authoritative_payload, authoritative_hash),
        )
        self._connection.execute(
            """
            INSERT INTO projection_checkpoint(
                singleton_id, revision, authoritative_state_hash, payload, payload_hash
            ) VALUES (1, ?, ?, ?, ?)
            ON CONFLICT(singleton_id) DO UPDATE SET
                revision = excluded.revision,
                authoritative_state_hash = excluded.authoritative_state_hash,
                payload = excluded.payload,
                payload_hash = excluded.payload_hash
            """,
            (
                revision,
                authoritative_hash,
                projection_payload,
                projection_hash,
            ),
        )

    def _append_record(
        self,
        family: str,
        identity: str,
        value: object,
        command_id: str,
        ordinal: int,
        available_from: str,
    ) -> None:
        payload = encode_durable(value)
        self._connection.execute(
            """
            INSERT INTO authoritative_records(
                record_family, record_identity, semantic_hash, payload,
                command_id, record_ordinal, available_from
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                family,
                identity,
                value_digest(value),
                payload,
                command_id,
                ordinal,
                _explicit_available_from(value, available_from),
            ),
        )

    def _append_deltas(
        self,
        previous: InMemoryState,
        prepared: InMemoryState,
        context: CommandContext,
    ) -> None:
        output_groups = (
            (previous.object_versions, prepared.object_versions),
            (previous.event_log, prepared.event_log),
            (previous.journal_store, prepared.journal_store),
            (previous.reporting_version_store, prepared.reporting_version_store),
        )
        ordinal = 0
        for before, after in output_groups:
            for value in after[len(before) :]:
                assert isinstance(value, BaseModel)
                self._append_record(
                    authoritative_family(value),
                    _identity(value),
                    value,
                    context.command_id,
                    ordinal,
                    context.semantic_as_of_time,
                )
                ordinal += 1
        for family, before, after in (
            ("J-AR14", previous.command_results, prepared.command_results),
            ("J-AR16", previous.dispositions, prepared.dispositions),
        ):
            for value in after[len(before) :]:
                identity = value.command_id
                self._append_record(
                    family,
                    str(identity),
                    value,
                    context.command_id,
                    ordinal,
                    context.semantic_as_of_time,
                )
                ordinal += 1
        for effect in prepared.effect_registry[len(previous.effect_registry) :]:
            payload = encode_durable(effect)
            semantic_hash = value_digest(effect)
            self._connection.execute(
                """
                INSERT INTO effect_claims(
                    idempotency_key, command_id, event_id, semantic_hash, payload,
                    available_from
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    effect.idempotency_key,
                    effect.command_id,
                    effect.event_id,
                    semantic_hash,
                    payload,
                    context.semantic_as_of_time,
                ),
            )
            self._append_record(
                "J-AR15",
                effect.idempotency_key,
                effect,
                context.command_id,
                ordinal,
                context.semantic_as_of_time,
            )
            ordinal += 1

    def _commit_prepared(
        self,
        *,
        previous: InMemoryState,
        prepared: InMemoryState,
        context: CommandContext,
    ) -> None:
        if previous is not self._state:
            raise InvariantFailure("prepared state no longer has its exact base")
        rebuilt = self._rebuild_from_authority(prepared.command_results)
        if value_digest(rebuilt) != value_digest(prepared.snapshot):
            raise InvariantFailure(
                "command projection is not rebuildable from declared authority"
            )
        next_revision = self._revision + 1
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            persisted_revision = self._connection.execute(
                "SELECT revision FROM runtime_metadata WHERE singleton_id = 1"
            ).fetchone()
            if (
                persisted_revision is None
                or int(persisted_revision[0]) != self._revision
            ):
                raise InvariantFailure(
                    "durable revision changed before final arbitration"
                )
            self._append_deltas(previous, prepared, context)
            context_payload = encode_durable(context)
            self._connection.execute(
                """
                INSERT INTO command_contexts(
                    command_owner, command_id, input_digest, payload, payload_hash
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    context.command_owner,
                    context.command_id,
                    context.input_digest,
                    context_payload,
                    durable_hash(context_payload),
                ),
            )
            self._write_complete_state(prepared, revision=next_revision)
            self._inject("command_before_commit")
            self._connection.commit()
        except BaseException:
            self._connection.rollback()
            raise
        super()._commit_prepared(
            previous=previous,
            prepared=prepared,
            context=context,
        )

    def _build_projection(
        self,
        generation: ProjectionGenerationRef,
    ) -> RebuiltProjectionSet:
        with self._lock:
            from finance_assurance.runtime.application.contracts import (
                ModuleContractService,
            )

            contracts = ModuleContractService(self)
            for result in self._state.command_results:
                if (
                    result.status == "ACCEPTED"
                    and isinstance(result.outcome, ModuleCommandOutcome)
                ):
                    context = self._contexts.get(result.command_id)
                    if context is None:
                        raise DurableStateError(
                            "module rebuild lacks its exact command context"
                        )
                    try:
                        contracts.validate_rebuild_outcome(context, result.outcome)
                    except ValueError as error:
                        raise DurableStateError(
                            "module contract binding failed during rebuild"
                        ) from error
            accepted = [
                item
                for item in self._state.command_results
                if item.status == "ACCEPTED"
            ]
            rebuilt = self._rebuild_from_authority(self._state.command_results)
            prior_hash = value_digest(self._state.snapshot)
            authoritative_payload = encode_durable(_authoritative_only(self._state))
            return RebuiltProjectionSet(
                generation_ref=generation,
                projection=rebuilt,
                prior_projection_hash=prior_hash,
                authoritative_state_hash=durable_hash(authoritative_payload),
                command_count=len(accepted),
            )

    def _rebuild_from_authority(
        self,
        command_results: tuple[CommandResult, ...],
    ) -> StateSnapshot:
        baseline = self._load_baseline_snapshot()
        if baseline == StateSnapshot() and not self._has_persisted_state():
            raise DurableStateError("projection rebuild requires an admitted baseline")
        rebuilt = baseline
        for result in command_results:
            if result.status != "ACCEPTED":
                continue
            if isinstance(result.outcome, TransitionPlan):
                try:
                    rebuilt = replay_transition(rebuilt, result.outcome)
                except ProjectionReplayError as error:
                    raise DurableStateError(str(error)) from error
            elif not isinstance(result.outcome, ModuleCommandOutcome):
                raise DurableStateError(
                    "accepted closure lacks transition or module outcome"
                )
        return rebuilt

    def _promote_projection(
        self,
        rebuilt: RebuiltProjectionSet,
    ) -> RebuildReceipt:
        with self._lock:
            if rebuilt.generation_ref.source_revision != self._revision:
                raise DurableStateError("rebuild generation is stale")
            self._connection.execute("BEGIN IMMEDIATE")
            try:
                self._write_complete_state(
                    replace(self._state, snapshot=rebuilt.projection),
                    revision=self._revision,
                )
                self._inject("rebuild_before_commit")
                self._connection.commit()
            except BaseException:
                self._connection.rollback()
                raise
            return RebuildReceipt(
                prior_projection_hash=rebuilt.prior_projection_hash,
                rebuilt_projection_hash=value_digest(rebuilt.projection),
                authoritative_state_hash=rebuilt.authoritative_state_hash,
                command_count=rebuilt.command_count,
            )


def _replay_transition(
    snapshot: StateSnapshot,
    outcome: TransitionPlan,
) -> StateSnapshot:
    """Rebuild projection state from a committed transition closure."""

    transition = outcome.transition
    proposals = snapshot.proposals
    periods = snapshot.periods
    restatements = snapshot.restatements
    if transition.subject_type == "journal_proposal":
        existing = snapshot.proposal(transition.subject_ref)
        if transition.from_state is None:
            treatments = [
                item
                for item in outcome.immutable_creations
                if isinstance(item, ProposalTreatmentVersion)
                and item.proposal_ref == transition.subject_ref
            ]
            if len(treatments) != 1 or existing is not None:
                raise DurableStateError(
                    "proposal constructor requires one exact J-AR05 treatment"
                )
            treatment = treatments[0]
            proposals = (
                *proposals,
                ProposalState(
                    proposal_ref=treatment.proposal_ref,
                    status="DRAFT",
                    target_period_id=treatment.target_period_id,
                    origin_type=treatment.origin_type,
                    account_ids=treatment.account_ids,
                    input_hashes=treatment.input_hashes,
                ),
            )
        else:
            if existing is None:
                raise DurableStateError("proposal transition has no J-AR05 treatment")
            proposals = tuple(
                replace(item, status=transition.to_state)
                if item.proposal_ref == transition.subject_ref
                else item
                for item in proposals
            )
    elif transition.subject_type == "accounting_period":
        if snapshot.period(transition.subject_ref) is None:
            raise DurableStateError("period transition has no baseline object")
        periods = tuple(
            replace(item, status=transition.to_state)
            if item.period_id == transition.subject_ref
            else item
            for item in periods
        )
    elif transition.subject_type == "restatement_case":
        existing = snapshot.restatement(transition.subject_ref)
        event = outcome.accounting_event
        if transition.from_state is None:
            if not isinstance(event, RestatementProposed) or existing is not None:
                raise DurableStateError(
                    "restatement constructor requires its proposed event"
                )
            restatements = (
                *restatements,
                RestatementState(
                    case_id=transition.subject_ref,
                    status="PROPOSED",
                    scope_period_ids=frozenset(event.basis.scope_period_ids),
                ),
            )
        else:
            if existing is None:
                raise DurableStateError("restatement transition has no proposed case")
            linked = existing.linked_journal_ids
            manifest_hash = existing.manifest_hash
            if isinstance(event, RestatementAdjustmentLinked):
                linked = linked | {str(event.payload.journal_id)}
            if isinstance(event, RestatementAdjustmentsReady):
                linked = frozenset(str(item) for item in event.basis.linked_journal_ids)
                manifest_hash = str(event.basis.manifest_hash)
            replacement = replace(
                existing,
                status=transition.to_state,
                linked_journal_ids=linked,
                manifest_hash=manifest_hash,
            )
            restatements = tuple(
                replacement if item.case_id == transition.subject_ref else item
                for item in restatements
            )
    event_ids = snapshot.accounting_event_ids
    if outcome.accounting_event is not None:
        event_ids = event_ids | {str(outcome.accounting_event.event_id)}
    journal_ids = {
        item.journal_id
        for item in outcome.immutable_creations
        if isinstance(item, JournalEntryBase)
    }
    frozen_cases = snapshot.frozen_manifest_case_ids
    if isinstance(outcome.accounting_event, RestatementAdjustmentsReady):
        frozen_cases = frozen_cases | {transition.subject_ref}
    reporting_refs = {
        str(item.reporting_version_ref)
        for item in outcome.immutable_creations
        if hasattr(item, "reporting_version_ref")
    }
    return replace(
        snapshot,
        proposals=proposals,
        periods=periods,
        restatements=restatements,
        posted_journal_ids=snapshot.posted_journal_ids | journal_ids,
        immutable_journal_ids=snapshot.immutable_journal_ids | journal_ids,
        frozen_manifest_case_ids=frozen_cases,
        published_reporting_refs=snapshot.published_reporting_refs | reporting_refs,
        accounting_event_ids=event_ids,
        consumed_effect_keys=(
            snapshot.consumed_effect_keys
            | ({outcome.effect_key} if outcome.effect_key else set())
        ),
    )


assert LATEST_SCHEMA_VERSION == 4
