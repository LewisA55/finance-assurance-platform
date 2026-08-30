"""Executed Artifact G module contracts over the shared unit of work."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from pydantic import BaseModel

from finance_assurance.runtime.application.models import CandidateReceipt
from finance_assurance.runtime.contracts.module import (
    G_REGISTRY,
    BoundaryObservation,
    CommandPublicationBasis,
    ContractPublication,
    ModuleCreationBasis,
    ValidatedModuleProduct,
)
from finance_assurance.runtime.contracts.objects import BusinessEvent
from finance_assurance.runtime.contracts.primitives import ExactSemanticRef
from finance_assurance.runtime.digests import value_digest
from finance_assurance.runtime.persistence.memory import authoritative_family
from finance_assurance.runtime.persistence.models import (
    AdmissionReceipt,
    CommandContext,
    CommandDisposition,
    CommandIdentityConflict,
    CommandResult,
    CommitReceipt,
    ExactCommandResult,
    ExactConflictSnapshot,
    ExactStoredRecord,
    ModuleCommandOutcome,
    QueryContext,
    StagedRejectionSet,
    StagedWriteSet,
)
from finance_assurance.runtime.persistence.ports import PersistenceBoundary
from finance_assurance.runtime.rejections import Rejection


class ModuleBoundaryError(ValueError):
    """Raised before persistence when an Artifact G boundary is violated."""


class ObservationSink(Protocol):
    """Removable J-P13 observation sink; never an authoritative dependency."""

    def record(self, observation: BoundaryObservation) -> None: ...


class InMemoryObservationSink:
    """Deterministic, de-duplicated observation recorder for tests and demos."""

    def __init__(self) -> None:
        self._observations: dict[str, BoundaryObservation] = {}

    def record(self, observation: BoundaryObservation) -> None:
        self._observations.setdefault(str(observation.observation_id), observation)

    @property
    def observations(self) -> tuple[BoundaryObservation, ...]:
        return tuple(self._observations.values())


@dataclass(frozen=True, slots=True)
class ModuleCommand:
    """One finite module-owned command and its complete authoritative closure."""

    command_id: str
    command_owner: str
    command_type: str
    actor_ref: str
    correlation_id: str
    semantic_as_of_time: str
    products: tuple[ValidatedModuleProduct, ...] = ()
    authoritative_creations: tuple[BaseModel, ...] = ()
    publications: tuple[ContractPublication, ...] = ()
    consumed_publication_refs: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ModuleExecution:
    outcome: ModuleCommandOutcome | Rejection
    receipt: CommitReceipt
    replayed: bool = False


def _creation_refs(value: BaseModel) -> frozenset[str]:
    refs: set[str] = set()
    for field in (
        "product_ref",
        "candidate_receipt_ref",
        "business_event_id",
        "event_id",
        "proposal_ref",
        "period_id",
        "case_id",
        "journal_id",
        "reporting_version_ref",
    ):
        candidate = getattr(value, field, None)
        if candidate is not None:
            refs.add(str(candidate))
    return frozenset(refs)


def _consumer_name(owner: str, publication: ContractPublication) -> str:
    if owner == "SourceDomain" and publication.contract_id == "G-12":
        return "ApprovedDecision"
    return owner


class ModuleContractService:
    """Validate, commit, and observe the bounded G-01 through G-14 handoffs."""

    def __init__(
        self,
        boundary: PersistenceBoundary,
        *,
        observations: ObservationSink | None = None,
    ) -> None:
        self._boundary = boundary
        self._observations = observations

    def execute(self, command: ModuleCommand) -> ModuleExecution:
        self._validate_command(command)
        outcome = ModuleCommandOutcome(
            command_id=command.command_id,
            command_owner=command.command_owner,
            consumed_publication_refs=command.consumed_publication_refs,
            immutable_creations=(
                *command.products,
                *command.authoritative_creations,
                *command.publications,
            ),
        )
        context = self._context(command)
        result = CommandResult(
            command_id=command.command_id,
            command_fingerprint=context.input_digest,
            status="ACCEPTED",
            outcome=outcome,
        )
        unit = self._boundary.begin_command(context)
        prior = unit.prior_result()
        if prior is not None:
            unit.rollback()
            self._validate_prior(prior, context)
            return self._prior(prior)
        unit.stage_accepted(
            StagedWriteSet(
                projection_replacement=unit.records().snapshot(),
                object_appends=outcome.immutable_creations,
                accounting_event_appends=(),
                journal_appends=(),
                reporting_version_appends=(),
                effect_claims=(),
                expected_state_tokens=(),
                resulting_state_tokens=(),
                command_result=result,
            )
        )
        validated = unit.validate()
        arbitrated = unit.arbitrate(validated)
        if isinstance(arbitrated, ExactCommandResult):
            unit.rollback()
            return self._prior(arbitrated)
        if isinstance(arbitrated, (ExactConflictSnapshot, CommandIdentityConflict)):
            unit.rollback()
            raise ModuleBoundaryError("module command lost deterministic arbitration")
        receipt = unit.commit(arbitrated)
        self._observe_committed(command)
        return ModuleExecution(outcome=outcome, receipt=receipt)

    def validate_transition(
        self,
        *,
        command_id: str,
        actor_ref: str,
        correlation_id: str,
        semantic_as_of_time: str,
        publications: tuple[ContractPublication, ...],
        consumed_publication_refs: tuple[str, ...],
    ) -> None:
        """Validate Atlas publications before the owning transition commits."""

        self._validate_command(
            ModuleCommand(
                command_id=command_id,
                command_owner="Atlas",
                command_type="AccountingTransition",
                actor_ref=actor_ref,
                correlation_id=correlation_id,
                semantic_as_of_time=semantic_as_of_time,
                publications=publications,
                consumed_publication_refs=consumed_publication_refs,
            )
        )

    def validate_rebuild_outcome(
        self,
        context: CommandContext,
        outcome: ModuleCommandOutcome,
    ) -> None:
        """Re-run ordinary module closure checks over immutable authority."""

        products = tuple(
            item
            for item in outcome.immutable_creations
            if isinstance(item, ValidatedModuleProduct)
        )
        publications = tuple(
            item
            for item in outcome.immutable_creations
            if isinstance(item, ContractPublication)
        )
        authoritative = tuple(
            item
            for item in outcome.immutable_creations
            if not isinstance(item, (ValidatedModuleProduct, ContractPublication))
        )
        self._validate_command(
            ModuleCommand(
                command_id=context.command_id,
                command_owner=context.command_owner,
                command_type=context.command_type,
                actor_ref=context.actor_ref,
                correlation_id=context.correlation_id,
                semantic_as_of_time=context.semantic_as_of_time,
                products=products,
                authoritative_creations=authoritative,
                publications=publications,
                consumed_publication_refs=outcome.consumed_publication_refs,
            )
        )

    def observe_transition(
        self,
        *,
        command_id: str,
        actor_ref: str,
        correlation_id: str,
        semantic_as_of_time: str,
        publications: tuple[ContractPublication, ...],
        consumed_publication_refs: tuple[str, ...],
    ) -> None:
        """Emit removable observations only after an accounting commit succeeds."""

        self._observe_committed(
            ModuleCommand(
                command_id=command_id,
                command_owner="Atlas",
                command_type="AccountingTransition",
                actor_ref=actor_ref,
                correlation_id=correlation_id,
                semantic_as_of_time=semantic_as_of_time,
                publications=publications,
                consumed_publication_refs=consumed_publication_refs,
            )
        )

    def reject(
        self,
        command: ModuleCommand,
        *,
        rejection: Rejection,
        disposition: CommandDisposition,
    ) -> ModuleExecution:
        if (
            command.products
            or command.authoritative_creations
            or len(command.publications) != 1
        ):
            raise ModuleBoundaryError("rejection closure permits only one G-14 publication")
        publication = command.publications[0]
        if publication.contract_id != "G-14":
            raise ModuleBoundaryError("rejection closure requires G-14")
        self._validate_publication(command, publication, set())
        context = self._context(command)
        result = CommandResult(
            command_id=command.command_id,
            command_fingerprint=context.input_digest,
            status="REJECTED",
            outcome=rejection,
        )
        unit = self._boundary.begin_command(context)
        prior = unit.prior_result()
        if prior is not None:
            unit.rollback()
            self._validate_prior(prior, context)
            return self._prior(prior)
        unit.stage_rejection(
            StagedRejectionSet(
                command_result=result,
                dispositions=(disposition,),
                object_appends=(publication,),
            )
        )
        validated = unit.validate()
        receipt = unit.commit(validated)
        self._observe_committed(command)
        return ModuleExecution(outcome=rejection, receipt=receipt)

    def _validate_command(self, command: ModuleCommand) -> None:
        if not command.command_id or not command.command_owner:
            raise ModuleBoundaryError("module command identity and owner are required")
        creations: set[str] = set()
        if command.authoritative_creations:
            permitted_business_events = (
                command.command_owner == "SharedSubstrate"
                and command.command_type == "PublishAdmittedBusinessEvent"
                and all(
                    isinstance(item, BusinessEvent)
                    for item in command.authoritative_creations
                )
            )
            permitted_candidate_custody = (
                command.command_owner == "Hermes"
                and command.command_type == "AssessBusinessEventCandidate"
                and all(
                    isinstance(item, CandidateReceipt)
                    for item in command.authoritative_creations
                )
            )
            if not (permitted_business_events or permitted_candidate_custody):
                raise ModuleBoundaryError(
                    "authoritative creation is outside the finite command boundary"
                )
            creations.update(
                ref
                for item in command.authoritative_creations
                for ref in _creation_refs(item)
            )
        for product in command.products:
            if product.semantic_owner != command.command_owner:
                raise ModuleBoundaryError("command cannot write another module's product")
            basis = product.creation_basis
            if (
                not isinstance(basis, ModuleCreationBasis)
                or
                basis.command_owner != command.command_owner
                or basis.command_id != command.command_id
            ):
                raise ModuleBoundaryError("module-product creation basis is inconsistent")
            creations.update(_creation_refs(product))
            if not all(ref.record_family == "J-AR12" for ref in product.evidence_refs):
                raise ModuleBoundaryError("module-product evidence must reference J-AR12")
        for publication in command.publications:
            self._validate_publication(command, publication, creations)
            creations.update(_creation_refs(publication))
        self._validate_output_bindings(command)
        self._validate_candidate_assessment(command)
        self._validate_admitted_event_publication(command)
        if len(command.consumed_publication_refs) != len(
            set(command.consumed_publication_refs)
        ):
            raise ModuleBoundaryError("consumed publication refs must be unique")
        persisted = self._publications(command.semantic_as_of_time)
        self._validate_exact_references(command, persisted)
        for ref in command.consumed_publication_refs:
            publication = persisted.get(ref)
            if publication is None:
                raise ModuleBoundaryError(f"consumed publication is unavailable: {ref}")
            consumer = _consumer_name(command.command_owner, publication)
            if (
                consumer not in G_REGISTRY[publication.contract_id][2]
                and command.command_owner != publication.publisher
            ):
                raise ModuleBoundaryError("consumer is not permitted by the G registry")
            if str(publication.available_from) > command.semantic_as_of_time:
                raise ModuleBoundaryError("publication is not semantically available")
        declared_upstream = {
            str(ref)
            for publication in command.publications
            for ref in publication.upstream_publication_refs
        }
        if not declared_upstream.issubset(set(command.consumed_publication_refs)):
            raise ModuleBoundaryError("publication lineage lacks a committed consumption")
        for publication in command.publications:
            self._validate_reliance(publication, persisted)

    def _validate_publication(
        self,
        command: ModuleCommand,
        publication: ContractPublication,
        creation_refs: set[str],
    ) -> None:
        basis = publication.publication_basis
        if not isinstance(basis, CommandPublicationBasis):
            raise ModuleBoundaryError("ordinary commands require COMMAND publication basis")
        if (
            basis.command_owner != command.command_owner
            or basis.command_id != command.command_id
            or basis.command_result_ref != command.command_id
        ):
            raise ModuleBoundaryError("publication basis does not bind its owner command")
        expected_owner = G_REGISTRY[publication.contract_id][0]
        if publication.publisher != expected_owner:
            raise ModuleBoundaryError("publication publisher is not authoritative")
        if command.command_owner != publication.publisher:
            raise ModuleBoundaryError("command cannot publish for another owner")
        if not all(
            ref.record_family == "J-AR12" for ref in publication.evidence_refs
        ):
            raise ModuleBoundaryError("publication evidence must reference J-AR12")
        if publication.product_ref not in creation_refs:
            payload_refs = {
                str(value)
                for key, value in publication.canonical_payload.items()
                if key
                in {
                    "product_ref",
                    "business_event_id",
                    "event_id",
                    "proposal_ref",
                    "period_id",
                    "case_id",
                    "restatement_case_id",
                    "journal_id",
                    "reporting_version_ref",
                    "disposition_ref",
                }
            }
            if publication.product_ref not in payload_refs:
                raise ModuleBoundaryError("publication does not bind a command output")

    def _publications(
        self, semantic_as_of_time: str
    ) -> dict[str, ContractPublication]:
        publications = {
            str(item.publication_ref): item
            for item in self._boundary.state.object_versions
            if isinstance(item, ContractPublication)
        }
        session = self._boundary.open_query(
            QueryContext(semantic_as_of_time=semantic_as_of_time)
        )
        for record in session.authoritative_records("J-AR13"):
            try:
                publication = ContractPublication.model_validate(
                    record.semantic_body()
                )
            except ValueError as error:
                raise ModuleBoundaryError(
                    "persisted J-AR13 publication is invalid"
                ) from error
            publication_ref = str(publication.publication_ref)
            projected = publications.get(publication_ref)
            if projected is not None and projected != publication:
                raise ModuleBoundaryError(
                    "persisted J-AR13 publication conflicts with lifecycle projection"
                )
            publications.setdefault(publication_ref, publication)
        return publications

    def _validate_exact_references(
        self,
        command: ModuleCommand,
        persisted_publications: dict[str, ContractPublication],
    ) -> None:
        publications = {
            **persisted_publications,
            **{str(item.publication_ref): item for item in command.publications},
        }
        session = self._boundary.open_query(
            QueryContext(semantic_as_of_time=command.semantic_as_of_time)
        )
        exact_records = {
            (item.record_family, item.record_identity): item
            for item in session.authoritative_records()
        }
        products = {
            item.product_ref: item
            for item in (*self._boundary.state.object_versions, *command.products)
            if isinstance(item, ValidatedModuleProduct)
            and (
                item in command.products
                or ("J-AR02", item.product_ref) in exact_records
            )
        }
        authoritative: dict[tuple[str, str], ExactStoredRecord] = dict(exact_records)
        for item in command.authoritative_creations:
            if not isinstance(item, BaseModel):
                continue
            family = authoritative_family(item)
            for identity in _creation_refs(item):
                authoritative[(family, identity)] = ExactStoredRecord(
                    record_family=family,
                    record_identity=identity,
                    semantic_hash=value_digest(item),
                    canonical_payload=b"",
                    available_from=command.semantic_as_of_time,
                )

        values = (*command.products, *command.publications)
        for value in values:
            for reference in value.evidence_refs:
                target = authoritative.get(
                    (str(reference.record_family), str(reference.record_identity))
                )
                if target is None or target.semantic_hash != reference.semantic_hash:
                    raise ModuleBoundaryError(
                        "evidence reference is unavailable or not exact"
                    )
            for reference in value.upstream_publication_refs:
                target = publications.get(str(reference))
                if target is None or target.exact_ref() != reference:
                    raise ModuleBoundaryError(
                        "upstream publication reference is not exact"
                    )
            for reference in value.upstream_authoritative_refs:
                self._validate_exact_semantic_ref(
                    reference,
                    authoritative=authoritative,
                    publications=publications,
                    products=products,
                )

    @staticmethod
    def _validate_exact_semantic_ref(
        reference: ExactSemanticRef,
        *,
        authoritative: dict[tuple[str, str], ExactStoredRecord],
        publications: dict[str, ContractPublication],
        products: dict[str, ValidatedModuleProduct],
    ) -> None:
        if reference.ref_kind == "PUBLICATION":
            assert reference.publication_ref is not None
            target = publications.get(str(reference.publication_ref))
            if target is None or target.exact_ref() != reference.publication_ref:
                raise ModuleBoundaryError("publication semantic reference is not exact")
        elif reference.ref_kind == "MODULE_PRODUCT":
            assert reference.module_product_ref is not None
            target = products.get(str(reference.module_product_ref))
            if target is None or target.exact_ref() != reference.module_product_ref:
                raise ModuleBoundaryError("module-product semantic reference is not exact")
        else:
            assert reference.authoritative_ref is not None
            key = (
                str(reference.authoritative_ref.record_family),
                str(reference.authoritative_ref.record_identity),
            )
            target = authoritative.get(key)
            if target is None or target.semantic_hash != (
                reference.authoritative_ref.semantic_hash
            ):
                raise ModuleBoundaryError("authoritative semantic reference is not exact")

    @staticmethod
    def _context(command: ModuleCommand) -> CommandContext:
        digest = value_digest(command)
        return CommandContext(
            command_owner=command.command_owner,
            command_id=command.command_id,
            command_type=command.command_type,
            input_contract_version="ARTIFACT-L-MODULE-COMMAND-V1",
            input_canonicalization_version="SORTED_KEYS_COMPACT_UTF8_V1",
            input_digest=digest,
            actor_ref=command.actor_ref,
            authority_refs=(),
            semantic_as_of_time=command.semantic_as_of_time,
            correlation_id=command.correlation_id,
        )

    @staticmethod
    def _validate_prior(prior: ExactCommandResult, context: CommandContext) -> None:
        if prior.context.retry_identity != context.retry_identity:
            raise ModuleBoundaryError("command identity is bound to different input")

    @staticmethod
    def _prior(prior: ExactCommandResult) -> ModuleExecution:
        outcome = prior.result.outcome
        if not isinstance(outcome, (ModuleCommandOutcome, Rejection)):
            raise ModuleBoundaryError("command identity belongs to another command family")
        return ModuleExecution(
            outcome=outcome,
            receipt=CommitReceipt(
                outcome=prior.result.status,
                command_result_ref=prior.result.command_id,
                command_result_hash=value_digest(prior.result),
                committed_authoritative_refs=(),
                committed_publication_refs=(),
                claimed_effect_refs=(),
                resulting_state_tokens=(),
            ),
            replayed=True,
        )

    def _observe_committed(self, command: ModuleCommand) -> None:
        if self._observations is None:
            return
        for publication in command.publications:
            self._safe_record(
                BoundaryObservation(
                    observation_id=f"PUBLISH:{publication.publication_ref}",
                    operation="PUBLISH",
                    publication_ref=publication.publication_ref,
                    contract_id=publication.contract_id,
                    publisher=publication.publisher,
                    consumer=None,
                    command_id=command.command_id,
                    observed_at=command.semantic_as_of_time,
                )
            )
        publications = self._publications(command.semantic_as_of_time)
        for ref in command.consumed_publication_refs:
            publication = publications[ref]
            self._safe_record(
                BoundaryObservation(
                    observation_id=f"CONSUME:{ref}:{command.command_id}",
                    operation="CONSUME",
                    publication_ref=publication.publication_ref,
                    contract_id=publication.contract_id,
                    publisher=publication.publisher,
                    consumer=_consumer_name(command.command_owner, publication),
                    command_id=command.command_id,
                    observed_at=command.semantic_as_of_time,
                )
            )
    def observe_admission(
        self,
        publication: ContractPublication,
        receipt: AdmissionReceipt,
        *,
        observed_at: str,
    ) -> None:
        """Observe a committed administrative publication without owning it."""

        expected_mode = {
            "G-06": "PRE_SCOPE_REPORTING",
            "G-13": "REFERENCED_JOURNAL",
        }.get(publication.contract_id)
        if expected_mode is None or receipt.admission_mode != expected_mode:
            raise ModuleBoundaryError("admission receipt does not match publication")
        self._safe_record(
            BoundaryObservation(
                observation_id=f"PUBLISH:{publication.publication_ref}",
                operation="PUBLISH",
                publication_ref=publication.publication_ref,
                contract_id=publication.contract_id,
                publisher=publication.publisher,
                consumer=None,
                command_id=receipt.admission_id,
                observed_at=observed_at,
            )
        )

    @staticmethod
    def _validate_output_bindings(command: ModuleCommand) -> None:
        products = {item.product_ref: item for item in command.products}
        publications = {item.contract_id: item for item in command.publications}

        for contract_id in {"G-02", "G-03", "G-09", "G-10", "G-11", "G-12"}:
            publication = publications.get(contract_id)
            if publication is None:
                continue
            product = products.get(publication.product_ref)
            if product is None or product.canonical_body != publication.canonical_payload:
                raise ModuleBoundaryError(
                    f"{contract_id} payload does not equal its exact J-AR02 body"
                )

        assurance = publications.get("G-07")
        if assurance is not None:
            payload = assurance.canonical_payload
            if payload["result_type"] == "ASSURANCE_EXCEPTION":
                test_run = products.get(str(payload["test_run_ref"]))
                exception = products.get(str(payload["exception_ref"]))
                if (
                    test_run is None
                    or exception is None
                    or exception.canonical_body.get("test_run_ref")
                    != test_run.product_ref
                    or exception.canonical_body.get("status") != "OPEN"
                ):
                    raise ModuleBoundaryError(
                        "G-07 exception does not bind its command-owned test run"
                    )
            else:
                verification = products.get(str(payload["verification_ref"]))
                if (
                    verification is None
                    or verification.canonical_body.get("outcome")
                    != payload["verification_outcome"]
                ):
                    raise ModuleBoundaryError(
                        "G-07 verification does not reproduce its outcome"
                    )

        governance = publications.get("G-08")
        if governance is not None:
            payload = governance.canonical_payload
            issue = products.get(str(payload["issue_ref"]))
            if issue is None:
                raise ModuleBoundaryError("G-08 does not bind its issue version")
            if payload["governance_result_type"] == "EXCEPTION_GOVERNED":
                review = products.get(str(payload["review_ref"]))
                finding = products.get(str(payload["finding_ref"]))
                if (
                    review is None
                    or finding is None
                    or finding.canonical_body.get("review_ref") != review.product_ref
                    or finding.product_ref
                    not in issue.canonical_body.get("finding_refs", [])
                    or review.canonical_body.get("exception_ref")
                    != payload["source_exception_ref"]
                ):
                    raise ModuleBoundaryError(
                        "G-08 governed exception chain is inconsistent"
                    )
            else:
                verification_ref = str(payload["verification_ref"])
                if (
                    issue.canonical_body.get("prior_issue_ref")
                    != payload["prior_issue_ref"]
                    or verification_ref
                    not in issue.canonical_body.get("verification_refs", [])
                ):
                    raise ModuleBoundaryError(
                        "G-08 issue update does not bind prior issue and verification"
                    )

        approvals = tuple(
            item
            for item in command.products
            if item.product_discriminator == "source.operational_decision_approval"
        )
        candidates = tuple(
            item
            for item in command.products
            if item.product_discriminator == "source.business_event_candidate"
        )
        for approval in approvals:
            body = approval.canonical_body
            approved = body["outcome"] == "APPROVED"
            matching = tuple(
                item
                for item in candidates
                if item.product_ref == body.get("candidate_ref")
                and item.canonical_body.get("approval_ref") == approval.product_ref
                and item.canonical_body.get("decision_ref") == body["decision_ref"]
            )
            if approved != (len(matching) == 1):
                raise ModuleBoundaryError(
                    "approved decision return does not bind one exact candidate"
                )

    @staticmethod
    def _validate_candidate_assessment(command: ModuleCommand) -> None:
        receipts = tuple(
            item
            for item in command.authoritative_creations
            if isinstance(item, CandidateReceipt)
        )
        if command.command_type != "AssessBusinessEventCandidate":
            if receipts:
                raise ModuleBoundaryError(
                    "candidate custody is permitted only in I-C01"
                )
            return
        if command.command_owner != "Hermes":
            raise ModuleBoundaryError("I-C01 must be owned by Hermes")
        products = tuple(
            item
            for item in command.products
            if item.product_discriminator
            == "hermes.business_event_admission_result"
        )
        publications = tuple(
            item for item in command.publications if item.contract_id == "G-02"
        )
        if (
            len(receipts) != 1
            or len(command.authoritative_creations) != 1
            or len(products) != 1
            or len(command.products) != 1
            or len(publications) != 1
            or len(command.publications) != 1
            or command.consumed_publication_refs
        ):
            raise ModuleBoundaryError(
                "I-C01 requires exactly J-AR01, Hermes admission, and G-02"
            )
        receipt = receipts[0]
        product = products[0]
        publication = publications[0]
        body = product.canonical_body
        expected = {
            "candidate_receipt_ref": str(receipt.candidate_receipt_ref),
            "candidate_type": str(receipt.candidate_type),
            "candidate_payload_hash": str(receipt.candidate_payload_hash),
            "source_domain_ref": str(receipt.source_domain_ref),
            "source_record_ref": str(receipt.source_record_ref),
        }
        if any(body.get(key) != value for key, value in expected.items()):
            raise ModuleBoundaryError("G-02 admission does not bind exact J-AR01")
        if (
            publication.product_ref != product.product_ref
            or publication.canonical_payload != body
            or str(receipt.candidate_receipt_ref)
            not in {str(ref) for ref in product.upstream_authoritative_refs}
            or str(receipt.candidate_receipt_ref)
            not in {str(ref) for ref in publication.upstream_authoritative_refs}
        ):
            raise ModuleBoundaryError("I-C01 authoritative closure is inconsistent")

    def _validate_admitted_event_publication(self, command: ModuleCommand) -> None:
        if command.command_type != "PublishAdmittedBusinessEvent":
            return
        events = tuple(
            item
            for item in command.authoritative_creations
            if isinstance(item, BusinessEvent)
        )
        publications = tuple(
            item for item in command.publications if item.contract_id == "G-01"
        )
        if (
            command.command_owner != "SharedSubstrate"
            or len(events) != 1
            or len(command.authoritative_creations) != 1
            or len(publications) != 1
            or len(command.publications) != 1
            or len(command.consumed_publication_refs) != 1
        ):
            raise ModuleBoundaryError("I-C02 requires exact accepted G-02 and G-01")
        admission_ref = command.consumed_publication_refs[0]
        admission = self._publications(command.semantic_as_of_time).get(admission_ref)
        if (
            admission is None
            or admission.contract_id != "G-02"
            or admission.canonical_payload.get("outcome") != "ACCEPTED"
            or admission.canonical_payload.get("eligible_for_g01") is not True
        ):
            raise ModuleBoundaryError("G-01 requires exact accepted G-02")
        receipt_ref = str(admission.canonical_payload["candidate_receipt_ref"])
        receipt = next(
            (
                item
                for item in self._boundary.state.object_versions
                if isinstance(item, CandidateReceipt)
                and str(item.candidate_receipt_ref) == receipt_ref
            ),
            None,
        )
        event = events[0]
        publication = publications[0]
        event_hash = value_digest(event.model_dump(mode="json"))
        if receipt is None or receipt.candidate_payload_hash != event_hash:
            raise ModuleBoundaryError("G-01 event bytes do not match J-AR01")
        if (
            publication.canonical_payload != event.model_dump(mode="json")
            or publication.product_ref != str(event.business_event_id)
            or admission_ref
            not in {str(ref) for ref in publication.upstream_publication_refs}
            or receipt_ref
            not in {str(ref) for ref in publication.upstream_authoritative_refs}
            or str(event.business_event_id)
            not in {str(ref) for ref in publication.upstream_authoritative_refs}
        ):
            raise ModuleBoundaryError("G-01 closure does not bind admission custody")

    @staticmethod
    def _validate_reliance(
        publication: ContractPublication,
        persisted: dict[str, ContractPublication],
    ) -> None:
        payload = publication.canonical_payload
        if publication.contract_id == "G-10":
            report = persisted.get(str(payload["reporting_publication_ref"]))
            if (
                report is None
                or report.contract_id != "G-06"
                or report.product_ref != payload["reporting_version_ref"]
                or report.canonical_payload["period_id"] != payload["period_id"]
            ):
                raise ModuleBoundaryError("G-10 does not bind its exact G-06")
        elif publication.contract_id == "G-11":
            report = persisted.get(str(payload["reporting_publication_ref"]))
            readiness = persisted.get(str(payload["readiness_publication_ref"]))
            if (
                report is None
                or report.contract_id != "G-06"
                or readiness is None
                or readiness.contract_id != "G-10"
                or readiness.canonical_payload["status"] != "APPROVED"
                or report.product_ref != payload["reporting_version_ref"]
                or readiness.product_ref != payload["readiness_ref"]
                or readiness.canonical_payload["purpose_ref"]
                != payload["purpose_ref"]
                or readiness.canonical_payload["period_id"] != payload["period_id"]
                or readiness.canonical_payload["scope_ref"] != payload["scope_ref"]
            ):
                raise ModuleBoundaryError(
                    "G-11 requires matching G-06 and approved G-10"
                )
        elif publication.contract_id == "G-12":
            planning = persisted.get(str(payload["planning_publication_ref"]))
            if (
                planning is None
                or planning.contract_id != "G-11"
                or planning.product_ref != payload["planning_snapshot_ref"]
            ):
                raise ModuleBoundaryError("G-12 does not bind its frozen G-11")

    def _safe_record(self, observation: BoundaryObservation) -> None:
        try:
            assert self._observations is not None
            self._observations.record(observation)
        except Exception:
            # J-P13 is removable and can never change authoritative commit outcome.
            return
