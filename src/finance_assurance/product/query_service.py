"""Revision-pinned O-Q01/O-Q11 in-process public query assemblers."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Literal, cast

from finance_assurance.product.contracts import (
    AssuranceExceptionEnvelope,
    CashApplicationIdentityExceptionView,
    CashApplicationIdentityReconciliationView,
    CorrectionIntegrityEnvelope,
    CorrectionIntegrityView,
    DemoManifestEnvelope,
    DemoManifestView,
    GovernanceCaseEnvelope,
    GovernanceCaseView,
    GovernanceIssueState,
    GovernedDecisionEnvelope,
    GovernedDecisionView,
    HeadlineValue,
    JournalBalanceResult,
    JourneyLink,
    ModuleSummary,
    PlatformOverviewEnvelope,
    PlatformOverviewView,
    PreScopeReportingVersionView,
    PublicFailureEnvelope,
    PublicSuccessEnvelope,
    ReadinessMatrixEnvelope,
    ReadinessMatrixView,
    ReadinessRow,
    ReadinessSummary,
    RecognitionCompletenessExceptionView,
    RecognitionPopulationReconciliationView,
    ReportingHistoryEnvelope,
    ReportingHistoryView,
    ReportingValueTraceEnvelope,
    ReportingValueTraceView,
    ReportingVersionEnvelope,
    ReportingVersionSummary,
    RestatedReportingVersionView,
    RestatementBridgeItem,
    RuntimeFailureEnvelope,
    ScenarioEntryPoint,
    ScenarioSummary,
    SourceReconciliationEnvelope,
    StartupFailureEnvelope,
    TraceEdgeView,
    TraceNodeView,
)
from finance_assurance.product.demo_scenarios import DemoScenarioSet
from finance_assurance.product.query_models import (
    GetAssuranceException,
    GetCorrectionIntegrity,
    GetDemoManifest,
    GetGovernanceCase,
    GetGovernedDecision,
    GetPlatformOverview,
    GetReadinessMatrix,
    GetReportingHistory,
    GetReportingVersion,
    GetSourceReconciliation,
    PublicQuery,
    TraceReportingValue,
)
from finance_assurance.product.registry import resolve_public_query
from finance_assurance.runtime.application.queries import (
    ReadModelError,
    ResolvedReportingContent,
    RuntimeQueryService,
)
from finance_assurance.runtime.canonical import canonical_sha256
from finance_assurance.runtime.persistence.models import (
    ExactStoredRecord,
    QueryContext,
)
from finance_assurance.runtime.persistence.ports import (
    PersistenceBoundary,
    QuerySession,
)

ErrorCode = Literal[
    "NOT_FOUND",
    "UNAVAILABLE",
    "UNVERIFIED_CONTENT",
    "REVISION_CONFLICT",
    "TRACE_INTEGRITY_FAILURE",
    "INTERNAL_FAILURE",
]


class PublicQueryAssemblyError(RuntimeError):
    """One safe, typed failure raised by a bounded public assembler."""

    def __init__(self, code: ErrorCode, subject_ref: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.subject_ref = subject_ref
        self.safe_message = message


def _body(record: ExactStoredRecord) -> dict[str, object]:
    value = record.semantic_body()
    if not isinstance(value, dict):
        raise PublicQueryAssemblyError(
            "INTERNAL_FAILURE",
            f"{record.record_family}:{record.record_identity}",
            "An authoritative public source has an invalid object body.",
        )
    return value


def _product_body(record: ExactStoredRecord) -> dict[str, object]:
    outer = _body(record)
    nested = outer.get("canonical_body")
    if not isinstance(nested, dict):
        raise PublicQueryAssemblyError(
            "INTERNAL_FAILURE",
            record.record_identity,
            "A module product has no canonical body.",
        )
    return nested


def _reference(value: object) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        authority = value.get("authoritative_ref")
        if isinstance(authority, dict):
            family = authority.get("record_family")
            identity = authority.get("record_identity")
            if isinstance(family, str) and isinstance(identity, str):
                return f"{family}:{identity}"
        publication = value.get("publication_ref")
        if isinstance(publication, dict):
            nested = publication.get("publication_authoritative_ref")
            if isinstance(nested, dict) and isinstance(
                nested.get("record_identity"), str
            ):
                return str(nested["record_identity"])
        if isinstance(value.get("object_id"), str):
            return str(value["object_id"])
    raise PublicQueryAssemblyError(
        "INTERNAL_FAILURE",
        "REFERENCE",
        "An authoritative reference cannot be represented safely.",
    )


def _string_tuple(value: object) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(_reference(item) for item in value)


def _contains_identity(value: object, identity: str) -> bool:
    return any(
        reference == identity or reference.endswith(f":{identity}")
        for reference in _string_tuple(value)
    )


@dataclass(frozen=True, slots=True)
class _ScenarioIndex:
    entries: tuple[ScenarioEntryPoint, ...]
    c001_reporting_ref: str
    c001_reconciliation_ref: str
    c001_exception_ref: str
    c001_issue_ref: str
    c001_readiness_ref: str
    c001_decision_ref: str
    ct1_reconciliation_ref: str
    ct1_exception_ref: str
    ct1_issue_ref: str
    ct1_verification_ref: str


class _PinnedReader:
    """Bounded product reads over exactly one runtime query session."""

    def __init__(self, session: QuerySession) -> None:
        self.session = session
        self.runtime = RuntimeQueryService.from_session(session)
        self.records = session.authoritative_records()
        self._by_key = {
            (item.record_family, item.record_identity): item for item in self.records
        }
        self.sources: set[str] = set()

    @property
    def revision(self) -> int:
        return self.session.revision

    def use(self, record: ExactStoredRecord) -> ExactStoredRecord:
        self.sources.add(f"{record.record_family}:{record.record_identity}")
        return record

    def exact(
        self,
        family: str,
        identity: str,
        *,
        required: bool = True,
    ) -> ExactStoredRecord | None:
        record = self._by_key.get((family, identity))
        if record is None:
            if required:
                raise PublicQueryAssemblyError(
                    "NOT_FOUND",
                    identity,
                    "The requested public subject was not found.",
                )
            return None
        return self.use(record)

    def product(
        self,
        product_ref: str,
        discriminator: str | None = None,
    ) -> ExactStoredRecord:
        record = self.exact("J-AR02", product_ref)
        assert record is not None
        if discriminator is not None and _body(record).get(
            "product_discriminator"
        ) != discriminator:
            raise PublicQueryAssemblyError(
                "NOT_FOUND",
                product_ref,
                "The requested public subject was not found.",
            )
        return record

    def find_products(
        self,
        discriminator: str,
        *,
        predicate: Callable[[dict[str, object]], bool] | None = None,
    ) -> tuple[ExactStoredRecord, ...]:
        values = tuple(
            item
            for item in self.records
            if item.record_family == "J-AR02"
            and _body(item).get("product_discriminator") == discriminator
            and (
                predicate is None
                or predicate(_product_body(item))
            )
        )
        return values

    def one_product(
        self,
        discriminator: str,
        *,
        predicate: Callable[[dict[str, object]], bool] | None = None,
        subject_ref: str = "MODULE-PRODUCT",
    ) -> ExactStoredRecord:
        values = self.find_products(discriminator, predicate=predicate)
        if len(values) != 1:
            raise PublicQueryAssemblyError(
                "UNAVAILABLE",
                subject_ref,
                "The exact public source is unavailable or ambiguous.",
            )
        return self.use(values[0])

    def publication(self, contract_id: str, product_ref: str) -> ExactStoredRecord:
        values = tuple(
            item
            for item in self.records
            if item.record_family == "J-AR13"
            and _body(item).get("contract_id") == contract_id
            and _body(item).get("product_ref") == product_ref
        )
        if len(values) != 1:
            raise PublicQueryAssemblyError(
                "UNAVAILABLE",
                product_ref,
                "The exact contract publication is unavailable or ambiguous.",
            )
        return self.use(values[0])

    def evidence(self, record: ExactStoredRecord) -> tuple[str, ...]:
        values = _body(record).get("evidence_refs")
        if not isinstance(values, (list, tuple)):
            return ()
        refs: list[str] = []
        for value in values:
            if not isinstance(value, dict):
                continue
            identity = value.get("record_identity") or value.get("ref_id")
            if not isinstance(identity, str):
                continue
            evidence = self.exact("J-AR12", identity, required=False)
            if evidence is not None:
                refs.append(f"J-AR12:{identity}")
        return tuple(sorted(set(refs)))

    def inventory_digest(self) -> str:
        for record in self.records:
            self.use(record)
        inventory = tuple(
            sorted(
                (item.record_family, item.record_identity, item.semantic_hash)
                for item in self.records
            )
        )
        return canonical_sha256(inventory)

    def scenario_index(self) -> _ScenarioIndex:
        reporting = self.one_product(
            "aegis.readiness_assessment",
            subject_ref="C-001 readiness",
        )
        readiness_body = _product_body(reporting)
        reporting_ref = str(readiness_body["reporting_version_ref"])
        reconciliation = self.one_product(
            "hermes.recognition_population_reconciliation",
            subject_ref="C-001 reconciliation",
        )
        c001_exception = self.one_product(
            "argus.recognition_completeness_exception",
            subject_ref="C-001 exception",
        )
        c001_verification = self.one_product(
            "argus.restatement_verification",
            subject_ref="C-001 verification",
        )
        c001_issue = self.one_product(
            "aegis.issue",
            predicate=lambda body: _product_body(c001_verification).get(
                "product_ref"
            )
            in body.get("verification_refs", []),
            subject_ref="C-001 issue",
        )
        decision = self.one_product(
            "pythia.governed_decision",
            subject_ref="C-001 decision",
        )
        ct1_reconciliation = self.one_product(
            "hermes.cash_application_identity_reconciliation",
            subject_ref="CT-1 reconciliation",
        )
        ct1_exception = self.one_product(
            "argus.cash_application_identity_exception",
            subject_ref="CT-1 exception",
        )
        ct1_verification = self.one_product(
            "argus.cash_application_correction_verification",
            subject_ref="CT-1 verification",
        )
        ct1_issue = self.one_product(
            "aegis.issue",
            predicate=lambda body: _product_body(ct1_verification).get(
                "product_ref"
            )
            in body.get("verification_refs", []),
            subject_ref="CT-1 issue",
        )
        entries = (
            ScenarioEntryPoint(
                journey_id="O-J01",
                semantic_role="reporting_value_trace",
                exact_ref=reporting_ref,
                source_kind="AUTHORITATIVE_RECORD",
                availability="AVAILABLE",
            ),
            ScenarioEntryPoint(
                journey_id="O-J02",
                semantic_role="recognition_reconciliation",
                exact_ref=str(_product_body(reconciliation)["product_ref"]),
                source_kind="AUTHORITATIVE_RECORD",
                availability="AVAILABLE",
            ),
            ScenarioEntryPoint(
                journey_id="O-J03",
                semantic_role="governed_decision",
                exact_ref=str(_product_body(decision)["product_ref"]),
                source_kind="AUTHORITATIVE_RECORD",
                availability="AVAILABLE",
            ),
            ScenarioEntryPoint(
                journey_id="O-SJ01",
                semantic_role="correction_verification",
                exact_ref=str(_product_body(ct1_verification)["product_ref"]),
                source_kind="AUTHORITATIVE_RECORD",
                availability="AVAILABLE",
            ),
        )
        return _ScenarioIndex(
            entries=entries,
            c001_reporting_ref=reporting_ref,
            c001_reconciliation_ref=str(_product_body(reconciliation)["product_ref"]),
            c001_exception_ref=str(_product_body(c001_exception)["product_ref"]),
            c001_issue_ref=str(_product_body(c001_issue)["product_ref"]),
            c001_readiness_ref=str(readiness_body["product_ref"]),
            c001_decision_ref=str(_product_body(decision)["product_ref"]),
            ct1_reconciliation_ref=str(
                _product_body(ct1_reconciliation)["product_ref"]
            ),
            ct1_exception_ref=str(_product_body(ct1_exception)["product_ref"]),
            ct1_issue_ref=str(_product_body(ct1_issue)["product_ref"]),
            ct1_verification_ref=str(
                _product_body(ct1_verification)["product_ref"]
            ),
        )


def _statement_label(field: str) -> str:
    return {
        "subscription_revenue_minor": "Subscription revenue",
        "deferred_revenue_minor": "Deferred revenue",
    }.get(field, field.replace("_minor", "").replace("_", " ").title())


def _reporting_values(
    reader: _PinnedReader,
    reporting_version_ref: str,
) -> tuple[tuple[HeadlineValue, ...], ResolvedReportingContent]:
    content = reader.runtime.resolve_reporting_content(reporting_version_ref)
    if content.proof is not None:
        reader.use(content.proof.record)
    if not isinstance(content.canonical_body, dict):
        return (), content
    currency = str(content.canonical_body.get("currency", ""))
    values: list[HeadlineValue] = []
    for field, amount in sorted(content.canonical_body.items()):
        if not field.endswith("_minor") or isinstance(amount, bool) or not isinstance(
            amount, int
        ):
            continue
        trace_available = False
        try:
            trace = reader.runtime.trace_reporting_value(reporting_version_ref, field)
            trace_available = True
            for node in trace.nodes:
                if node.record_family != "EXTERNAL":
                    record = reader.exact(
                        node.record_family,
                        node.record_identity,
                        required=False,
                    )
                    if record is not None:
                        reader.use(record)
        except ReadModelError:
            trace_available = False
        values.append(
            HeadlineValue(
                field=field,
                label=_statement_label(field),
                amount_minor=amount,
                currency=currency,
                reporting_version_ref=reporting_version_ref,
                content_verification_status=content.verification_status,
                trace_available=trace_available,
            )
        )
    return tuple(values), content


def _reporting_summary(
    reader: _PinnedReader,
    record: ExactStoredRecord,
) -> ReportingVersionSummary:
    reader.use(record)
    body = _body(record)
    ref = str(body["reporting_version_ref"])
    publication = reader.publication("G-06", ref)
    payload = _body(publication).get("canonical_payload")
    if not isinstance(payload, dict):
        raise PublicQueryAssemblyError(
            "INTERNAL_FAILURE",
            ref,
            "The reporting publication has an invalid canonical payload.",
        )
    values, content = _reporting_values(reader, ref)
    origin = str(payload["publication_origin"])
    if origin not in {"PRE_SCOPE_IMPORT", "RESTATEMENT_PUBLICATION"}:
        raise PublicQueryAssemblyError(
            "INTERNAL_FAILURE", ref, "The reporting origin is unsupported."
        )
    return ReportingVersionSummary(
        reporting_version_ref=ref,
        version=int(body["version"]),
        publication_origin=cast(
            Literal["PRE_SCOPE_IMPORT", "RESTATEMENT_PUBLICATION"], origin
        ),
        published_at=str(body["published_at"]),
        content_verification_status=content.verification_status,
        statement_values=values,
    )


def _readiness_summary(record: ExactStoredRecord) -> ReadinessSummary:
    body = _product_body(record)
    assessed_by = body.get("assessed_by")
    if not isinstance(assessed_by, dict):
        raise PublicQueryAssemblyError(
            "INTERNAL_FAILURE",
            record.record_identity,
            "The readiness assessor is unavailable.",
        )
    return ReadinessSummary(
        readiness_ref=str(body["product_ref"]),
        reporting_version_ref=str(body["reporting_version_ref"]),
        period_id=str(body["period_id"]),
        purpose_ref=str(body["purpose_ref"]),
        scope_ref=str(body["scope_ref"]),
        status=cast(
            Literal["BLOCKED", "USABLE_WITH_REVIEW", "APPROVED"], body["status"]
        ),
        basis_refs=tuple(sorted(_string_tuple(body.get("basis_refs")))),
        limitation_codes=tuple(sorted(_string_tuple(body.get("limitation_codes")))),
        assessed_by_ref=str(assessed_by["actor_id"]),
    )


class PublicQueryService:
    """Execute the closed Artifact O query set without transport or UI concerns."""

    def __init__(
        self,
        boundary: PersistenceBoundary,
        *,
        scenarios: DemoScenarioSet,
        workspace_ref: str,
    ) -> None:
        self._boundary = boundary
        self._scenarios = scenarios
        self._workspace_ref = workspace_ref

    def execute(self, query: PublicQuery) -> PublicSuccessEnvelope | PublicFailureEnvelope:
        if query.semantic_as_of_time != self._scenarios.semantic_as_of_time:
            return StartupFailureEnvelope(
                error_code="UNSUPPORTED_CONTRACT",
                message="The requested semantic time is not supported by this demo.",
                scenario_ref=query.scenario_ref,
                subject_ref=str(query.semantic_as_of_time),
            )
        session = self._boundary.open_query(
            QueryContext(semantic_as_of_time=str(query.semantic_as_of_time))
        )
        return self.execute_in_session(query, session)

    def execute_in_session(
        self,
        query: PublicQuery,
        session: QuerySession,
    ) -> PublicSuccessEnvelope | PublicFailureEnvelope:
        """Execute one public query using a caller-owned immutable session.

        A fresh reader is constructed for every invocation so source references
        remain local to one O-Q response even when Artifact P deliberately shares
        the underlying query session across a complete export package.
        """

        descriptor = resolve_public_query(query.query_id)
        if query.semantic_as_of_time != self._scenarios.semantic_as_of_time:
            return StartupFailureEnvelope(
                error_code="UNSUPPORTED_CONTRACT",
                message="The requested semantic time is not supported by this demo.",
                scenario_ref=query.scenario_ref,
                subject_ref=str(query.semantic_as_of_time),
            )
        reader = _PinnedReader(session)
        try:
            self._validate_scenario_scope(reader, query)
            data = {
                "O-Q01": self._manifest,
                "O-Q02": self._overview,
                "O-Q03": self._reconciliation,
                "O-Q04": self._reporting_history,
                "O-Q05": self._reporting_version,
                "O-Q06": self._assurance_exception,
                "O-Q07": self._governance_case,
                "O-Q08": self._readiness_matrix,
                "O-Q09": self._governed_decision,
                "O-Q10": self._trace_reporting_value,
                "O-Q11": self._correction_integrity,
            }[query.query_id](reader, query)
            return self._success(
                reader,
                query,
                descriptor.view_id,
                data,
            )
        except PublicQueryAssemblyError as error:
            return RuntimeFailureEnvelope(
                error_code=error.code,
                message=error.safe_message,
                scenario_ref=query.scenario_ref,
                subject_ref=error.subject_ref,
                query_revision=reader.revision,
            )
        except Exception:
            return RuntimeFailureEnvelope(
                error_code="INTERNAL_FAILURE",
                message="An authoritative source could not satisfy the public view.",
                scenario_ref=query.scenario_ref,
                subject_ref=query.query_id,
                query_revision=reader.revision,
            )

    def _validate_scenario_scope(
        self,
        reader: _PinnedReader,
        query: PublicQuery,
    ) -> None:
        if isinstance(query, GetDemoManifest):
            if query.workspace_ref != self._workspace_ref:
                raise PublicQueryAssemblyError(
                    "NOT_FOUND",
                    query.workspace_ref,
                    "The requested demo workspace was not found.",
                )
            return
        c001_ref = self._scenarios.c001.scenario_ref
        ct1_ref = self._scenarios.ct1.scenario_ref
        c001_only = (
            GetPlatformOverview,
            GetReportingHistory,
            GetReportingVersion,
            GetReadinessMatrix,
            GetGovernedDecision,
            TraceReportingValue,
        )
        if isinstance(query, c001_only) and query.scenario_ref != c001_ref:
            raise PublicQueryAssemblyError(
                "NOT_FOUND",
                query.scenario_ref,
                "The requested subject does not belong to this scenario.",
            )
        if isinstance(query, GetCorrectionIntegrity) and query.scenario_ref != ct1_ref:
            raise PublicQueryAssemblyError(
                "NOT_FOUND",
                query.scenario_ref,
                "The requested subject does not belong to this scenario.",
            )
        expected: str | None = None
        if isinstance(query, GetSourceReconciliation):
            product = reader.one_product(
                (
                    "hermes.recognition_population_reconciliation"
                    if query.scenario_ref == c001_ref
                    else "hermes.cash_application_identity_reconciliation"
                ),
                subject_ref=query.scenario_ref,
            )
            expected = str(_product_body(product)["product_ref"])
            actual = query.reconciliation_ref
        elif isinstance(query, GetAssuranceException):
            product = reader.one_product(
                (
                    "argus.recognition_completeness_exception"
                    if query.scenario_ref == c001_ref
                    else "argus.cash_application_identity_exception"
                ),
                subject_ref=query.scenario_ref,
            )
            expected = str(_product_body(product)["product_ref"])
            actual = query.exception_ref
        elif isinstance(query, GetGovernanceCase):
            verification = reader.one_product(
                (
                    "argus.restatement_verification"
                    if query.scenario_ref == c001_ref
                    else "argus.cash_application_correction_verification"
                ),
                subject_ref=query.scenario_ref,
            )
            verification_ref = str(_product_body(verification)["product_ref"])
            final_issue = reader.one_product(
                "aegis.issue",
                predicate=lambda body: verification_ref
                in body.get("verification_refs", []),
                subject_ref=query.scenario_ref,
            )
            actual = query.issue_ref
            allowed = {
                final_issue.record_identity,
                str(_product_body(final_issue).get("prior_issue_ref", "")),
            }
            if actual not in allowed:
                raise PublicQueryAssemblyError(
                    "NOT_FOUND",
                    actual,
                    "The requested subject does not belong to this scenario.",
                )
            return
        else:
            return
        if actual != expected:
            raise PublicQueryAssemblyError(
                "NOT_FOUND",
                actual,
                "The requested subject does not belong to this scenario.",
            )
    def _success(
        self,
        reader: _PinnedReader,
        query: PublicQuery,
        view_id: str,
        data: object,
    ) -> PublicSuccessEnvelope:
        common = {
            "view_contract_version": 1,
            "scenario_ref": query.scenario_ref,
            "semantic_as_of_time": query.semantic_as_of_time,
            "query_revision": reader.revision,
            "compatibility_read_mode": "EXACT_ORIGINAL",
            "source_refs": tuple(sorted(reader.sources)),
        }
        envelope_types = {
            "O-V01": DemoManifestEnvelope,
            "O-V02": PlatformOverviewEnvelope,
            "O-V03": SourceReconciliationEnvelope,
            "O-V04": ReportingHistoryEnvelope,
            "O-V05": ReportingVersionEnvelope,
            "O-V06": AssuranceExceptionEnvelope,
            "O-V07": GovernanceCaseEnvelope,
            "O-V08": ReadinessMatrixEnvelope,
            "O-V09": GovernedDecisionEnvelope,
            "O-V10": ReportingValueTraceEnvelope,
            "O-V11": CorrectionIntegrityEnvelope,
        }
        envelope_type = envelope_types[view_id]
        return cast(
            PublicSuccessEnvelope,
            envelope_type(view_contract=view_id, data=data, **common),
        )

    def _manifest(
        self, reader: _PinnedReader, query: PublicQuery
    ) -> DemoManifestView:
        assert isinstance(query, GetDemoManifest)
        index = reader.scenario_index()
        inventory_digest = reader.inventory_digest()
        return DemoManifestView(
            workspace_ref=query.workspace_ref,
            runtime_release=self._scenarios.runtime_release,
            synthetic_data_notice=self._scenarios.synthetic_data_notice,
            scenario_summaries=(
                ScenarioSummary(
                    scenario_ref=self._scenarios.c001.scenario_ref,
                    canonical_family="C-001",
                    status="AVAILABLE",
                    public_role="FLAGSHIP",
                    entry_point_count=3,
                ),
                ScenarioSummary(
                    scenario_ref=self._scenarios.ct1.scenario_ref,
                    canonical_family="CT-1",
                    status="AVAILABLE",
                    public_role="SUPPORTING",
                    entry_point_count=1,
                ),
            ),
            scenario_entry_points=index.entries,
            authoritative_inventory_digest=inventory_digest,
            projection_generation_ref=f"J-P04@r{reader.revision}",
            verification_status="VERIFIED",
        )

    def _overview(
        self, reader: _PinnedReader, query: PublicQuery
    ) -> PlatformOverviewView:
        assert isinstance(query, GetPlatformOverview)
        index = reader.scenario_index()
        reporting = reader.exact("J-AR10", index.c001_reporting_ref)
        assert reporting is not None
        reporting_body = _body(reporting)
        headline_values, content = _reporting_values(
            reader, index.c001_reporting_ref
        )
        if content.verification_status != "CONTENT_BYTES_VERIFIED":
            raise PublicQueryAssemblyError(
                "UNVERIFIED_CONTENT",
                index.c001_reporting_ref,
                "The overview requires verified reporting content.",
            )
        reconciliation = reader.product(index.c001_reconciliation_ref)
        exception = reader.product(index.c001_exception_ref)
        issue = reader.product(index.c001_issue_ref)
        readiness = reader.product(
            index.c001_readiness_ref, "aegis.readiness_assessment"
        )
        decision = reader.product(index.c001_decision_ref, "pythia.governed_decision")
        decision_body = _product_body(decision)
        planning = reader.product(
            str(decision_body["planning_snapshot_ref"]),
            "pythia.planning_input_snapshot",
        )
        admission = reader.one_product(
            "hermes.business_event_admission_result",
            predicate=lambda body: body.get("eligible_for_g01") is True,
            subject_ref="C-001 admission",
        )
        for contract, product_ref in (
            ("G-02", admission.record_identity),
            ("G-03", index.c001_reconciliation_ref),
            ("G-07", index.c001_exception_ref),
            ("G-08", index.c001_issue_ref),
            ("G-10", index.c001_readiness_ref),
            ("G-11", planning.record_identity),
            ("G-12", index.c001_decision_ref),
            ("G-06", index.c001_reporting_ref),
        ):
            reader.publication(contract, product_ref)
        issue_body = _product_body(issue)
        counted_exceptions = reader.find_products(
            "argus.recognition_completeness_exception"
        )
        for counted_exception in counted_exceptions:
            reader.use(counted_exception)
        exception_count = len(counted_exceptions)
        readiness_item = _readiness_summary(readiness)
        return PlatformOverviewView(
            company_label="Nexus Group",
            reporting_period=str(reporting_body["period_id"]),
            headline_reporting_version_ref=index.c001_reporting_ref,
            headline_values=headline_values,
            module_summaries=(
                ModuleSummary(
                    module="Hermes",
                    summary_code="RECONCILIATION_FAILED",
                    primary_product_ref=reconciliation.record_identity,
                    route=f"/hermes/reconciliation/{reconciliation.record_identity}",
                ),
                ModuleSummary(
                    module="Atlas",
                    summary_code="RESTATED_REPORT_AVAILABLE",
                    primary_product_ref=index.c001_reporting_ref,
                    route=(
                        f"/atlas/reporting/{reporting_body['period_id']}/"
                        f"{index.c001_reporting_ref}"
                    ),
                ),
                ModuleSummary(
                    module="Argus",
                    summary_code="COMPLETENESS_EXCEPTION",
                    primary_product_ref=exception.record_identity,
                    route=f"/argus/exceptions/{exception.record_identity}",
                ),
                ModuleSummary(
                    module="Aegis",
                    summary_code="REMEDIATION_VERIFIED",
                    primary_product_ref=issue.record_identity,
                    route=f"/aegis/cases/{issue.record_identity}",
                ),
                ModuleSummary(
                    module="Pythia",
                    summary_code="HIRING_DEFERRED",
                    primary_product_ref=decision.record_identity,
                    route=f"/pythia/decisions/{decision.record_identity}",
                ),
            ),
            machine_exception_count=exception_count,
            governance_issue_states=(
                GovernanceIssueState(
                    issue_ref=str(issue_body["product_ref"]),
                    status=str(issue_body["status"]),
                    owner_ref=str(issue_body["owner_ref"]),
                ),
            ),
            readiness_summary=(readiness_item,),
            governed_decision_ref=decision.record_identity,
            journey_links=(
                JourneyLink(
                    journey_id="O-J01",
                    label="Trace a reported number",
                    route=(
                        f"/trace/reporting/{index.c001_reporting_ref}/"
                        "subscription_revenue_minor"
                    ),
                    availability="AVAILABLE",
                ),
                JourneyLink(
                    journey_id="O-J02",
                    label="Explain a broken quarter",
                    route=f"/atlas/reporting/{reporting_body['period_id']}",
                    availability="AVAILABLE",
                ),
                JourneyLink(
                    journey_id="O-J03",
                    label="Follow governed truth into a decision",
                    route=f"/pythia/decisions/{index.c001_decision_ref}",
                    availability="AVAILABLE",
                ),
                JourneyLink(
                    journey_id="O-SJ01",
                    label="Prove reversal and replacement integrity",
                    route=f"/corrections/{index.ct1_verification_ref}",
                    availability="AVAILABLE",
                ),
            ),
        )

    def _reconciliation(
        self, reader: _PinnedReader, query: PublicQuery
    ) -> RecognitionPopulationReconciliationView | CashApplicationIdentityReconciliationView:
        assert isinstance(query, GetSourceReconciliation)
        record = reader.product(query.reconciliation_ref)
        body = _product_body(record)
        result = str(body["result"])
        if result not in {"PASSED", "FAILED", "REVIEW"}:
            raise PublicQueryAssemblyError(
                "INTERNAL_FAILURE",
                query.reconciliation_ref,
                "The reconciliation result is unsupported.",
            )
        publication = reader.publication("G-03", query.reconciliation_ref)
        del publication
        if body.get("reconciliation_type") == "RECOGNITION_POPULATION":
            exception = reader.one_product(
                "argus.recognition_completeness_exception",
                predicate=lambda item: item.get("test_run_ref") is not None,
                subject_ref=query.reconciliation_ref,
            )
            exception_body = _product_body(exception)
            test = reader.product(
                str(exception_body["test_run_ref"]),
                "argus.recognition_completeness_test_run",
            )
            test_body = _product_body(test)
            if test_body.get("reconciliation_ref") != query.reconciliation_ref:
                raise PublicQueryAssemblyError(
                    "INTERNAL_FAILURE",
                    query.reconciliation_ref,
                    "The reconciliation and assurance result do not bind exactly.",
                )
            return RecognitionPopulationReconciliationView(
                reconciliation_ref=query.reconciliation_ref,
                reconciliation_type="RECOGNITION_POPULATION",
                scope_ref=str(body["scope_ref"]),
                performed_at=str(body["performed_at"]),
                source_refs=(str(body["recognition_schedule_ref"]),),
                reconciliation_status=cast(
                    Literal["PASSED", "FAILED", "REVIEW"], result
                ),
                downstream_exception_ref=str(exception_body["product_ref"]),
                period_id=str(body["period_id"]),
                expected_item_count=int(body["expected_item_count"]),
                posted_item_count=int(body["posted_item_count"]),
                submitted_unposted_count=int(body["submitted_unposted_count"]),
                deferred_count=int(body["deferred_count"]),
                expected_amount_minor=int(body["expected_amount_minor"]),
                posted_amount_minor=int(body["posted_amount_minor"]),
                difference_minor=int(body["difference_minor"]),
                currency=str(body["currency"]),
            )
        if body.get("reconciliation_type") == "CASH_APPLICATION_IDENTITY":
            source = reader.one_product(
                "argus.cash_application_identity_exception",
                subject_ref=query.reconciliation_ref,
            )
            source_body = _product_body(source)
            test = reader.product(
                str(source_body["test_run_ref"]),
                "argus.cash_application_identity_test_run",
            )
            test_body = _product_body(test)
            if test_body.get("reconciliation_ref") != query.reconciliation_ref:
                raise PublicQueryAssemblyError(
                    "INTERNAL_FAILURE",
                    query.reconciliation_ref,
                    "The reconciliation and assurance result do not bind exactly.",
                )
            publication_ref = str(test_body["referenced_journal_publication_ref"])
            g13 = reader.exact("J-AR13", publication_ref)
            assert g13 is not None
            g13_payload = _body(g13).get("canonical_payload")
            if not isinstance(g13_payload, dict) or not isinstance(
                g13_payload.get("journal_id"), str
            ):
                raise PublicQueryAssemblyError(
                    "INTERNAL_FAILURE",
                    query.reconciliation_ref,
                    "The referenced-journal publication is invalid.",
                )
            source_record = reader.exact("J-AR17", str(g13_payload["journal_id"]))
            assert source_record is not None
            return CashApplicationIdentityReconciliationView(
                reconciliation_ref=query.reconciliation_ref,
                reconciliation_type="CASH_APPLICATION_IDENTITY",
                scope_ref=str(body["scope_ref"]),
                performed_at=str(body["performed_at"]),
                source_refs=(
                    f"J-AR17:{source_record.record_identity}",
                    f"J-AR13:{g13.record_identity}",
                    str(body["party_mapping_ref"]),
                ),
                reconciliation_status=cast(
                    Literal["PASSED", "FAILED", "REVIEW"], result
                ),
                downstream_exception_ref=str(source_body["product_ref"]),
                cash_application_ref=str(body["cash_application_ref"]),
                receipt_party_ref=str(body["receipt_party_ref"]),
                application_party_ref=str(body["application_party_ref"]),
                party_mapping_ref=str(body["party_mapping_ref"]),
                identity_match=bool(body["identity_match"]),
            )
        raise PublicQueryAssemblyError(
            "NOT_FOUND",
            query.reconciliation_ref,
            "The requested reconciliation variant was not found.",
        )

    def _reporting_history(
        self, reader: _PinnedReader, query: PublicQuery
    ) -> ReportingHistoryView:
        assert isinstance(query, GetReportingHistory)
        history = reader.runtime.get_reporting_history(str(query.period_id))
        if not history.versions:
            raise PublicQueryAssemblyError(
                "NOT_FOUND",
                str(query.period_id),
                "The requested reporting period was not found.",
            )
        versions = tuple(_reporting_summary(reader, item.record) for item in history.versions)
        predecessor = next((item for item in versions if item.version == 1), None)
        successor = next((item for item in versions if item.version == 2), None)
        bridge: tuple[RestatementBridgeItem, ...] = ()
        if predecessor is not None and successor is not None:
            before = {
                item.field: item for item in predecessor.statement_values
            }
            after = {item.field: item for item in successor.statement_values}
            field = "subscription_revenue_minor"
            if field in before and field in after:
                successor_record = reader.exact(
                    "J-AR10", successor.reporting_version_ref
                )
                assert successor_record is not None
                successor_body = _body(successor_record)
                bridge = (
                    RestatementBridgeItem(
                        predecessor_version_ref=predecessor.reporting_version_ref,
                        successor_version_ref=successor.reporting_version_ref,
                        statement_field=field,
                        adjustment_minor=(
                            after[field].amount_minor - before[field].amount_minor
                        ),
                        currency=after[field].currency,
                        restatement_case_ref=str(
                            successor_body["restatement_case_id"]
                        ),
                    ),
                )
        return ReportingHistoryView(
            period_id=query.period_id,
            versions=versions,
            restatement_bridge=bridge,
        )

    def _reporting_version(
        self, reader: _PinnedReader, query: PublicQuery
    ) -> PreScopeReportingVersionView | RestatedReportingVersionView:
        assert isinstance(query, GetReportingVersion)
        record = reader.exact("J-AR10", query.reporting_version_ref)
        assert record is not None
        body = _body(record)
        publication = reader.publication("G-06", query.reporting_version_ref)
        publication_body = _body(publication)
        payload = publication_body.get("canonical_payload")
        if not isinstance(payload, dict):
            raise PublicQueryAssemblyError(
                "INTERNAL_FAILURE",
                query.reporting_version_ref,
                "The reporting publication payload is unavailable.",
            )
        values, content = _reporting_values(reader, query.reporting_version_ref)
        currency = values[0].currency if values else "GBP"
        common = {
            "reporting_version_ref": query.reporting_version_ref,
            "period_id": str(body["period_id"]),
            "version": int(body["version"]),
            "published_at": str(body["published_at"]),
            "statement_values": values,
            "currency": currency,
            "content_ref": str(body["content_ref"]),
            "content_verification_status": content.verification_status,
            "traceable_fields": tuple(
                item.field for item in values if item.trace_available
            ),
        }
        if payload.get("publication_origin") == "PRE_SCOPE_IMPORT":
            return PreScopeReportingVersionView(
                publication_origin="PRE_SCOPE_IMPORT",
                import_attestation_ref=str(payload["import_attestation_ref"]),
                original_authority_ref=str(payload["original_authority_ref"]),
                source_ref=str(payload["source_ref"]),
                **common,
            )
        if payload.get("publication_origin") != "RESTATEMENT_PUBLICATION":
            raise PublicQueryAssemblyError(
                "INTERNAL_FAILURE",
                query.reporting_version_ref,
                "The reporting publication origin is unsupported.",
            )
        return RestatedReportingVersionView(
            publication_origin="RESTATEMENT_PUBLICATION",
            predecessor_version_ref=str(payload["predecessor_version_ref"]),
            restatement_case_ref=str(payload["restatement_case_ref"]),
            manifest_hash=str(payload["manifest_hash"]),
            published_by_event_id=str(payload["published_by_event_id"]),
            **common,
        )

    def _assurance_exception(
        self, reader: _PinnedReader, query: PublicQuery
    ) -> RecognitionCompletenessExceptionView | CashApplicationIdentityExceptionView:
        assert isinstance(query, GetAssuranceException)
        exception = reader.product(query.exception_ref)
        outer = _body(exception)
        body = _product_body(exception)
        test = reader.product(str(body["test_run_ref"]))
        test_body = _product_body(test)
        evidence_refs = reader.evidence(exception)
        issue = reader.one_product(
            "aegis.issue",
            predicate=lambda item: item.get("prior_issue_ref") is not None
            and any(
                _contains_identity(
                    _product_body(candidate).get("affected_refs"),
                    query.exception_ref,
                )
                for candidate in reader.find_products("aegis.finding")
                if item.get("finding_refs")
                and _product_body(candidate).get("product_ref")
                in item.get("finding_refs", [])
            ),
            subject_ref=query.exception_ref,
        )
        reader.publication("G-07", query.exception_ref)
        discriminator = outer.get("product_discriminator")
        if discriminator == "argus.recognition_completeness_exception":
            return RecognitionCompletenessExceptionView(
                test_run_ref=str(test_body["product_ref"]),
                test_definition_ref=str(test_body["test_definition_ref"]),
                exception_ref=query.exception_ref,
                exception_type="RECOGNITION_COMPLETENESS",
                assertion=str(body["assertion"]),
                severity=str(body["severity"]),
                evidence_refs=evidence_refs,
                related_governance_case_ref=issue.record_identity,
                subject_refs=_string_tuple(body.get("subject_refs")),
                period_id=str(body["period_id"]),
                expected_amount_minor=int(body["expected_amount_minor"]),
                actual_amount_minor=int(body["actual_amount_minor"]),
                difference_minor=int(body["difference_minor"]),
                currency=str(body["currency"]),
            )
        if discriminator == "argus.cash_application_identity_exception":
            return CashApplicationIdentityExceptionView(
                test_run_ref=str(test_body["product_ref"]),
                test_definition_ref=str(test_body["test_definition_ref"]),
                exception_ref=query.exception_ref,
                exception_type="CASH_APPLICATION_IDENTITY",
                assertion=str(body["assertion"]),
                severity=str(body["severity"]),
                evidence_refs=evidence_refs,
                related_governance_case_ref=issue.record_identity,
                receipt_party_ref=str(body["receipt_party_ref"]),
                application_party_ref=str(body["application_party_ref"]),
                journal_id=str(body["journal_id"]),
                amount_minor=int(body["amount_minor"]),
                currency=str(body["currency"]),
            )
        raise PublicQueryAssemblyError(
            "NOT_FOUND",
            query.exception_ref,
            "The requested assurance exception was not found.",
        )

    def _governance_case(
        self, reader: _PinnedReader, query: PublicQuery
    ) -> GovernanceCaseView:
        assert isinstance(query, GetGovernanceCase)
        requested = reader.product(query.issue_ref, "aegis.issue")
        requested_body = _product_body(requested)
        prior_issue_ref = requested_body.get("prior_issue_ref")
        if prior_issue_ref is None:
            initial = requested
            initial_body = requested_body
        else:
            initial = reader.product(str(prior_issue_ref), "aegis.issue")
            initial_body = _product_body(initial)
            if initial_body.get("prior_issue_ref") is not None:
                raise PublicQueryAssemblyError(
                    "INTERNAL_FAILURE",
                    query.issue_ref,
                    "The governance issue version chain is invalid.",
                )
        finding_refs = _string_tuple(initial_body.get("finding_refs"))
        if len(finding_refs) != 1:
            raise PublicQueryAssemblyError(
                "INTERNAL_FAILURE", query.issue_ref, "The issue finding is ambiguous."
            )
        finding = reader.product(finding_refs[0], "aegis.finding")
        finding_body = _product_body(finding)
        review = reader.product(
            str(finding_body["review_ref"]), "aegis.exception_review"
        )
        review_body = _product_body(review)
        exception_ref = str(review_body["exception_ref"])
        exception = reader.product(exception_ref)
        successor = (
            requested
            if prior_issue_ref is not None
            else reader.one_product(
                "aegis.issue",
                predicate=lambda body: body.get("prior_issue_ref")
                == initial.record_identity,
                subject_ref=query.issue_ref,
            )
        )
        successor_body = _product_body(successor)
        directive_refs = _string_tuple(successor_body.get("directive_refs"))
        verification_refs = _string_tuple(successor_body.get("verification_refs"))
        if len(directive_refs) != 1 or len(verification_refs) != 1:
            raise PublicQueryAssemblyError(
                "INTERNAL_FAILURE",
                query.issue_ref,
                "The governance remediation chain is incomplete.",
            )
        directive = reader.product(
            directive_refs[0], "aegis.remediation_directive"
        )
        verification = reader.product(verification_refs[0])
        verification_body = _product_body(verification)
        correction_refs = tuple(
            str(value)
            for key, value in sorted(verification_body.items())
            if key in {"journal_ref", "reversal_journal_ref", "replacement_journal_ref"}
        )
        readiness_records = reader.find_products("aegis.readiness_assessment")
        readiness_refs = tuple(
            sorted(
                str(_product_body(item)["product_ref"])
                for item in readiness_records
                if any(
                    upstream.get("product_ref") == successor.record_identity
                    for upstream in _body(item).get("upstream_publication_refs", [])
                    if isinstance(upstream, dict)
                )
            )
        )
        for record in readiness_records:
            if str(_product_body(record).get("product_ref")) in readiness_refs:
                reader.use(record)
        reader.publication("G-08", initial.record_identity)
        reader.publication("G-08", successor.record_identity)
        reader.publication("G-09", directive.record_identity)
        reader.publication("G-07", verification.record_identity)
        reader.use(exception)
        return GovernanceCaseView(
            exception_ref=exception_ref,
            review_ref=review.record_identity,
            review_disposition=str(review_body["review_outcome"]),
            finding_ref=finding.record_identity,
            initial_issue_ref=initial.record_identity,
            initial_issue_status=str(initial_body["status"]),
            owner_ref=str(initial_body["owner_ref"]),
            remediation_directive_ref=directive.record_identity,
            correction_refs=correction_refs,
            verification_ref=verification.record_identity,
            prior_issue_refs=(initial.record_identity,),
            final_issue_ref=successor.record_identity,
            final_issue_status=str(successor_body["status"]),
            readiness_refs=readiness_refs,
        )

    def _readiness_matrix(
        self, reader: _PinnedReader, query: PublicQuery
    ) -> ReadinessMatrixView:
        assert isinstance(query, GetReadinessMatrix)
        reporting = reader.exact("J-AR10", query.reporting_version_ref)
        assert reporting is not None
        del reporting
        reader.publication("G-06", query.reporting_version_ref)
        records = reader.find_products("aegis.readiness_assessment")
        selected = tuple(
            item
            for item in records
            if (
                (body := _product_body(item)).get("reporting_version_ref")
                == query.reporting_version_ref
                and body.get("period_id") == query.period_id
                and body.get("purpose_ref") == query.purpose_ref
                and body.get("scope_ref") == query.scope_ref
            )
        )
        if len(selected) != 1:
            raise PublicQueryAssemblyError(
                "NOT_FOUND",
                query.reporting_version_ref,
                "No exact purpose-specific readiness row was found.",
            )
        record = reader.use(selected[0])
        summary = _readiness_summary(record)
        reader.publication("G-10", summary.readiness_ref)
        return ReadinessMatrixView(
            reporting_version_ref=query.reporting_version_ref,
            period_id=query.period_id,
            rows=(
                ReadinessRow(
                    readiness_ref=summary.readiness_ref,
                    purpose_ref=summary.purpose_ref,
                    scope_ref=summary.scope_ref,
                    status=summary.status,
                    basis_refs=summary.basis_refs,
                    limitation_codes=summary.limitation_codes,
                    assessed_by_ref=summary.assessed_by_ref,
                ),
            ),
        )

    def _governed_decision(
        self, reader: _PinnedReader, query: PublicQuery
    ) -> GovernedDecisionView:
        assert isinstance(query, GetGovernedDecision)
        decision = reader.product(query.decision_ref, "pythia.governed_decision")
        decision_body = _product_body(decision)
        plan_ref = str(decision_body["planning_snapshot_ref"])
        controlled = reader.runtime.get_controlled_planning_input(plan_ref)
        reader.use(controlled.planning_input.record)
        reader.use(controlled.readiness.product.record)
        reader.use(controlled.reporting_version.record)
        plan_body = _product_body(controlled.planning_input.record)
        approval = reader.one_product(
            "source.operational_decision_approval",
            predicate=lambda body: body.get("decision_ref") == query.decision_ref,
            subject_ref=query.decision_ref,
        )
        approval_body = _product_body(approval)
        candidate = reader.product(
            str(approval_body["candidate_ref"]), "source.business_event_candidate"
        )
        admission = reader.one_product(
            "hermes.business_event_admission_result",
            predicate=lambda body: body.get("source_record_ref")
            == candidate.record_identity,
            subject_ref=candidate.record_identity,
        )
        admission_body = _product_body(admission)
        for contract, product_ref in (
            ("G-06", str(plan_body["reporting_version_ref"])),
            ("G-10", str(plan_body["readiness_ref"])),
            ("G-11", plan_ref),
            ("G-12", query.decision_ref),
            ("G-02", admission.record_identity),
        ):
            reader.publication(contract, product_ref)
        frozen = tuple(
            sorted(
                {
                    str(plan_body["reporting_version_ref"]),
                    str(plan_body["readiness_ref"]),
                    *_string_tuple(plan_body.get("assumption_refs")),
                }
            )
        )
        return GovernedDecisionView(
            planning_input_ref=plan_ref,
            reporting_version_ref=str(plan_body["reporting_version_ref"]),
            readiness_ref=str(plan_body["readiness_ref"]),
            purpose_ref=str(plan_body["purpose_ref"]),
            scope_ref=str(plan_body["scope_ref"]),
            frozen_input_refs=frozen,
            decision_ref=query.decision_ref,
            decision_type=str(decision_body["decision_type"]),
            position_ref=str(decision_body["position_ref"]),
            original_start_date=str(decision_body["original_start_date"]),
            recommended_start_date=str(decision_body["recommended_start_date"]),
            monthly_cost_minor=int(decision_body["monthly_cost_minor"]),
            currency=str(decision_body["currency"]),
            reason_code=str(decision_body["reason_code"]),
            approval_ref=approval.record_identity,
            approval_outcome=cast(
                Literal["APPROVED", "REJECTED"], approval_body["outcome"]
            ),
            candidate_ref=candidate.record_identity,
            candidate_admission_outcome=cast(
                Literal["ACCEPTED", "REJECTED", "UNSUPPORTED"],
                admission_body["outcome"],
            ),
        )

    def _trace_reporting_value(
        self, reader: _PinnedReader, query: PublicQuery
    ) -> ReportingValueTraceView:
        assert isinstance(query, TraceReportingValue)
        reporting = reader.exact("J-AR10", query.reporting_version_ref)
        assert reporting is not None
        content = reader.runtime.resolve_reporting_content(
            query.reporting_version_ref
        )
        if content.proof is not None:
            reader.use(content.proof.record)
        if content.verification_status != "CONTENT_BYTES_VERIFIED":
            raise PublicQueryAssemblyError(
                "UNVERIFIED_CONTENT",
                query.reporting_version_ref,
                "The requested trace requires verified reporting content.",
            )
        try:
            trace = reader.runtime.trace_reporting_value(
                query.reporting_version_ref,
                query.statement_field,
            )
        except ReadModelError as error:
            raise PublicQueryAssemblyError(
                "TRACE_INTEGRITY_FAILURE",
                query.reporting_version_ref,
                "The directed reporting trace could not be verified.",
            ) from error
        for node in trace.nodes:
            if node.record_family != "EXTERNAL":
                record = reader.exact(
                    node.record_family,
                    node.record_identity,
                    required=False,
                )
                if record is not None:
                    reader.use(record)
        return ReportingValueTraceView(
            reporting_version_ref=trace.reporting_version_ref,
            statement_field=trace.statement_field,
            statement_value_minor=trace.statement_value_minor,
            currency=trace.currency,
            content_verification_status="CONTENT_BYTES_VERIFIED",
            nodes=tuple(
                TraceNodeView(
                    node_ref=item.node_ref,
                    role=item.role,
                    record_family=item.record_family,
                    record_identity=item.record_identity,
                    semantic_hash=item.semantic_hash,
                )
                for item in trace.nodes
            ),
            edges=tuple(
                TraceEdgeView(
                    source_ref=item.source_ref,
                    target_ref=item.target_ref,
                    relationship=item.relationship,
                )
                for item in trace.edges
            ),
        )

    def _correction_integrity(
        self, reader: _PinnedReader, query: PublicQuery
    ) -> CorrectionIntegrityView:
        assert isinstance(query, GetCorrectionIntegrity)
        verification = reader.product(
            query.verification_ref,
            "argus.cash_application_correction_verification",
        )
        body = _product_body(verification)
        checks = body.get("check_results")
        if not isinstance(checks, dict) or not all(
            checks.get(key) is True
            for key in (
                "control_account_net_zero",
                "journals_balanced",
                "replacement_customer_correct",
                "reversal_equal_and_opposite",
                "reversal_source_bound",
            )
        ):
            raise PublicQueryAssemblyError(
                "UNAVAILABLE",
                query.verification_ref,
                "The correction verification has not passed every required check.",
            )
        source_ref = str(body["source_journal_ref"]).removeprefix("J-AR17:")
        reversal_ref = str(body["reversal_journal_ref"]).removeprefix("J-AR08:")
        replacement_ref = str(body["replacement_journal_ref"]).removeprefix(
            "J-AR08:"
        )
        source = reader.exact("J-AR17", source_ref)
        assert source is not None
        g13_matches = tuple(
            item
            for item in reader.records
            if item.record_family == "J-AR13"
            and _body(item).get("contract_id") == "G-13"
            and isinstance(_body(item).get("canonical_payload"), dict)
            and cast(dict[str, object], _body(item)["canonical_payload"]).get(
                "journal_id"
            )
            == source_ref
        )
        if len(g13_matches) != 1:
            raise PublicQueryAssemblyError(
                "UNAVAILABLE",
                source_ref,
                "The exact referenced-journal publication is unavailable.",
            )
        g13 = reader.use(g13_matches[0])
        g13_payload = _body(g13).get("canonical_payload")
        if (
            not isinstance(g13_payload, dict)
            or source.semantic_hash != body["source_hash"]
            or g13_payload.get("source_hash") != body["source_hash"]
        ):
            raise PublicQueryAssemblyError(
                "TRACE_INTEGRITY_FAILURE",
                query.verification_ref,
                "The referenced-journal source binding is inconsistent.",
            )
        reversal = reader.runtime.get_journal(reversal_ref)
        replacement = reader.runtime.get_journal(replacement_ref)
        if reversal is None or replacement is None:
            raise PublicQueryAssemblyError(
                "NOT_FOUND",
                query.verification_ref,
                "The correction journals were not found.",
            )
        journal_reads = (reversal, replacement)
        balances: list[JournalBalanceResult] = []
        ar_movement = 0
        identity_before = ""
        identity_after = ""
        proposal_refs: list[str] = []
        for journal in journal_reads:
            reader.use(journal.header.record)
            header = _body(journal.header.record)
            proposal_ref = str(header["source_proposal_ref"])
            proposal_refs.append(proposal_ref)
            proposal = reader.exact("J-AR05", proposal_ref)
            assert proposal is not None
            if journal.header.record.record_identity == reversal_ref:
                origin = _body(proposal).get("origin_basis")
                if not isinstance(origin, dict) or body["source_hash"] not in origin.get(
                    "input_hashes", []
                ):
                    raise PublicQueryAssemblyError(
                        "TRACE_INTEGRITY_FAILURE",
                        query.verification_ref,
                        "The reversal proposal does not bind its declared source hash.",
                    )
            debit = int(header["total_debit_minor"])
            credit = int(header["total_credit_minor"])
            balances.append(
                JournalBalanceResult(
                    journal_ref=journal.header.record.record_identity,
                    debits_minor=debit,
                    credits_minor=credit,
                    currency=str(header["currency"]),
                    balanced=debit == credit,
                )
            )
            for line in journal.ordered_lines:
                reader.use(line.record)
                line_body = _body(line.record)
                if line_body.get("account_id") != "ACC-AR":
                    continue
                ar_movement += int(line_body["debit_minor"]) - int(
                    line_body["credit_minor"]
                )
                dimensions = line_body.get("dimensions")
                if not isinstance(dimensions, dict):
                    continue
                customer = dimensions.get("customer_id")
                if isinstance(customer, str):
                    if journal.header.record.record_identity == reversal_ref:
                        identity_before = customer
                    else:
                        identity_after = customer
        source_body = _body(source)
        for line in source_body.get("line_tuples", []):
            if not isinstance(line, dict) or line.get("account_id") != "ACC-AR":
                continue
            dimensions = line.get("dimensions")
            if isinstance(dimensions, dict) and isinstance(
                dimensions.get("customer_id"), str
            ):
                identity_before = str(dimensions["customer_id"])
        lifecycle_events = tuple(
            item
            for item in reader.records
            if item.record_family == "J-AR06"
            and isinstance(_body(item).get("subject_ref"), dict)
            and cast(dict[str, object], _body(item)["subject_ref"]).get("object_ref")
            in proposal_refs
        )
        if len(lifecycle_events) != 6:
            raise PublicQueryAssemblyError(
                "TRACE_INTEGRITY_FAILURE",
                query.verification_ref,
                "The correction proposal lifecycle is incomplete.",
            )
        for event in lifecycle_events:
            reader.use(event)
        if ar_movement != 0 or not all(item.balanced for item in balances):
            raise PublicQueryAssemblyError(
                "TRACE_INTEGRITY_FAILURE",
                query.verification_ref,
                "The displayed correction arithmetic disagrees with verification.",
            )
        issue = reader.one_product(
            "aegis.issue",
            predicate=lambda item: query.verification_ref
            in item.get("verification_refs", []),
            subject_ref=query.verification_ref,
        )
        reader.publication("G-07", query.verification_ref)
        reader.publication("G-08", issue.record_identity)
        return CorrectionIntegrityView(
            source_projection_ref=f"J-AR17:{source_ref}",
            source_projection_hash=str(body["source_hash"]),
            reversal_proposal_ref=str(_body(reversal.header.record)["source_proposal_ref"]),
            reversal_journal_ref=reversal_ref,
            replacement_proposal_ref=str(
                _body(replacement.header.record)["source_proposal_ref"]
            ),
            replacement_journal_ref=replacement_ref,
            identity_before=identity_before,
            identity_after=identity_after,
            reversal_binding_status="BOUND_BEFORE_COMPARE",
            journal_balance_results=tuple(balances),
            control_account_net_movement_minor=ar_movement,
            currency=str(source_body["currency"]),
            verification_ref=query.verification_ref,
            issue_update_ref=issue.record_identity,
        )
