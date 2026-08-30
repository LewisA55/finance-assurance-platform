"""Closed P-EVIDENCE@v1 dataset and relationship registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from finance_assurance.runtime.canonical import canonical_sha256

REGISTRY_ID = "P-EVIDENCE"
REGISTRY_VERSION = 1
STORAGE_KEY = "p-evidence-v1"

ColumnType = Literal["text", "integer", "boolean", "date", "timestamp", "hash", "enum"]
ValueOrigin = Literal[
    "O_VIEW_FIELD",
    "O_ENVELOPE_FIELD",
    "O_QUERY_FIELD",
    "P_DISCOVERY_FIELD",
    "P_TRANSPORT_METADATA",
    "P_STRUCTURAL_METADATA",
]
Transformation = Literal[
    "EXACT_COPY",
    "PARENT_CONTEXT_COPY",
    "ARRAY_ORDINAL",
    "STABLE_ROW_KEY",
    "REFERENCE_ROLE_MATCH",
    "CONSTANT",
]


@dataclass(frozen=True, slots=True)
class ColumnDefinition:
    name: str
    type: ColumnType
    nullable: bool
    description: str
    value_origin: ValueOrigin
    transformation: Transformation
    source_path: str | None = None
    enum_values: tuple[str, ...] = ()

    def document(self) -> dict[str, object]:
        value: dict[str, object] = {
            "description": self.description,
            "name": self.name,
            "nullable": self.nullable,
            "transformation": self.transformation,
            "type": self.type,
            "value_origin": self.value_origin,
        }
        if self.enum_values:
            value["enum_values"] = list(self.enum_values)
        if self.source_path is not None:
            value["source_path"] = self.source_path
        return value


@dataclass(frozen=True, slots=True)
class DatasetDefinition:
    dataset_id: str
    name: str
    export_steward: str
    semantic_owners: tuple[str, ...]
    description: str
    columns: tuple[ColumnDefinition, ...]
    unique_keys: tuple[tuple[str, ...], ...]
    source_query_ids: tuple[str, ...]
    source_view_ids: tuple[str, ...]

    @property
    def header(self) -> tuple[str, ...]:
        return tuple(item.name for item in self.columns)

    def schema_document(self) -> dict[str, object]:
        return {
            "columns": [item.document() for item in self.columns],
            "dataset_id": self.dataset_id,
            "dataset_version": 1,
            "description": self.description,
            "export_steward": self.export_steward,
            "primary_key": ["row_key"],
            "registry_id": REGISTRY_ID,
            "schema_contract_version": 1,
            "semantic_owners": list(self.semantic_owners),
            "unique_keys": [list(item) for item in self.unique_keys],
        }


def _col(
    name: str,
    type_: ColumnType = "text",
    *,
    nullable: bool = False,
    origin: ValueOrigin = "O_VIEW_FIELD",
    path: str | None = None,
    transform: Transformation = "EXACT_COPY",
    enum: tuple[str, ...] = (),
) -> ColumnDefinition:
    return ColumnDefinition(
        name=name,
        type=type_,
        nullable=nullable,
        description=f"Artifact P contract column {name}.",
        value_origin=origin,
        source_path=path,
        transformation=transform,
        enum_values=enum,
    )


def _row() -> ColumnDefinition:
    return _col(
        "row_key",
        origin="P_STRUCTURAL_METADATA",
        transform="STABLE_ROW_KEY",
    )


def _scenario() -> ColumnDefinition:
    return _col(
        "scenario_ref",
        origin="P_DISCOVERY_FIELD",
        path="P-V00.scenarios[].scenario_ref",
        transform="PARENT_CONTEXT_COPY",
    )


def _p_transport(name: str, type_: ColumnType = "text") -> ColumnDefinition:
    return _col(name, type_, origin="P_TRANSPORT_METADATA", transform="CONSTANT")


def _p_struct(name: str, type_: ColumnType = "text") -> ColumnDefinition:
    return _col(name, type_, origin="P_STRUCTURAL_METADATA", transform="CONSTANT")


def _ordinal(name: str) -> ColumnDefinition:
    return _col(
        name,
        "integer",
        origin="P_STRUCTURAL_METADATA",
        transform="ARRAY_ORDINAL",
    )


def _view(name: str, path: str, type_: ColumnType = "text", **kwargs: object) -> ColumnDefinition:
    return _col(name, type_, path=path, **kwargs)  # type: ignore[arg-type]


def _dataset(
    dataset_id: str,
    name: str,
    owners: tuple[str, ...],
    columns: tuple[ColumnDefinition, ...],
    natural_key: tuple[str, ...],
    queries: tuple[str, ...],
    views: tuple[str, ...],
) -> DatasetDefinition:
    return DatasetDefinition(
        dataset_id=dataset_id,
        name=name,
        export_steward="shared substrate",
        semantic_owners=owners,
        description=f"Closed Artifact P evidence dataset {name}.",
        columns=(_row(), *columns),
        unique_keys=(("row_key",), natural_key),
        source_query_ids=queries,
        source_view_ids=views,
    )


def _nullable_variant(name: str, path: str, type_: ColumnType = "text") -> ColumnDefinition:
    return _view(name, path, type_, nullable=True)


DATASETS: tuple[DatasetDefinition, ...] = (
    _dataset(
        "P-D01",
        "package_context",
        ("shared substrate",),
        (
            _p_transport("export_ref"),
            _view("workspace_ref", "O-V01.data.workspace_ref"),
            _view("runtime_release", "O-V01.data.runtime_release"),
            _col("query_revision", "integer", origin="O_ENVELOPE_FIELD", path="O-V*.query_revision"),
            _col("semantic_as_of", "timestamp", origin="O_ENVELOPE_FIELD", path="O-V*.semantic_as_of_time"),
            _p_transport("exported_at", "timestamp"),
            _col("compatibility_mode", "enum", origin="O_ENVELOPE_FIELD", path="O-V*.compatibility_read_mode", enum=("EXACT_ORIGINAL",)),
            _p_transport("synthetic_data", "boolean"),
            _view("synthetic_data_notice", "O-V01.data.synthetic_data_notice"),
            _view("authoritative_inventory_digest", "O-V01.data.authoritative_inventory_digest", "hash"),
            _view("projection_generation_ref", "O-V01.data.projection_generation_ref"),
            _p_transport("producer_release"),
            _view("verification_status", "O-V01.data.verification_status", "enum", enum=("VERIFIED", "FAILED")),
            _view("company_label", "O-V02.data.company_label"),
            _view("reporting_period", "O-V02.data.reporting_period"),
            _view("headline_reporting_version_ref", "O-V02.data.headline_reporting_version_ref"),
            _view("machine_exception_count", "O-V02.data.machine_exception_count", "integer"),
            _view("governed_decision_ref", "O-V02.data.governed_decision_ref"),
            _col("scenario_set_digest", "hash", origin="P_DISCOVERY_FIELD", path="P-V00.scenario_set_digest"),
            _col("discovery_descriptor_ref", origin="P_DISCOVERY_FIELD", path="P-V00.discovery_descriptor_ref"),
            _col("discovery_descriptor_hash", "hash", origin="P_DISCOVERY_FIELD", path="P-V00.discovery_descriptor_hash"),
            _p_transport("evidence_registry_version"),
        ),
        ("export_ref",),
        ("P-Q00", "O-Q01", "O-Q02"),
        ("P-V00", "O-V01", "O-V02"),
    ),
    _dataset(
        "P-D02",
        "scenarios",
        ("shared substrate",),
        (
            _col("scenario_ref", origin="P_DISCOVERY_FIELD", path="P-V00.scenarios[].scenario_ref", transform="PARENT_CONTEXT_COPY"),
            _col("canonical_family", "enum", origin="P_DISCOVERY_FIELD", path="P-V00.scenarios[].canonical_family", enum=("C-001", "CT-1")),
            _view("status", "O-V01.data.scenario_summaries[].status", "enum", enum=("AVAILABLE", "UNAVAILABLE", "FAILED")),
            _col("public_role", origin="P_DISCOVERY_FIELD", path="P-V00.scenarios[].public_role"),
            _view("entry_point_count", "O-V01.data.scenario_summaries[].entry_point_count", "integer"),
        ),
        ("scenario_ref",),
        ("P-Q00", "O-Q01"),
        ("P-V00", "O-V01"),
    ),
    _dataset(
        "P-D03",
        "module_lenses",
        ("Hermes", "Atlas", "Argus", "Aegis", "Pythia"),
        (
            _scenario(),
            _view("module", "O-V02.data.module_summaries[].module", "enum", enum=("Hermes", "Atlas", "Argus", "Aegis", "Pythia")),
            _view("summary_code", "O-V02.data.module_summaries[].summary_code"),
            _view("primary_product_ref", "O-V02.data.module_summaries[].primary_product_ref"),
        ),
        ("scenario_ref", "module"),
        ("O-Q02",),
        ("O-V02",),
    ),
    _dataset(
        "P-D04",
        "source_reconciliations",
        ("Hermes",),
        (
            _scenario(),
            _view("reconciliation_ref", "O-V03.data.reconciliation_ref"),
            _view("reconciliation_type", "O-V03.data.reconciliation_type", "enum", enum=("RECOGNITION_POPULATION", "CASH_APPLICATION_IDENTITY")),
            _view("scope_ref", "O-V03.data.scope_ref"),
            _view("performed_at", "O-V03.data.performed_at", "timestamp"),
            _view("reconciliation_status", "O-V03.data.reconciliation_status", "enum", enum=("PASSED", "FAILED", "REVIEW")),
            _view("downstream_exception_ref", "O-V03.data.downstream_exception_ref"),
            _nullable_variant("period_id", "O-V03.data.period_id"),
            _nullable_variant("expected_item_count", "O-V03.data.expected_item_count", "integer"),
            _nullable_variant("posted_item_count", "O-V03.data.posted_item_count", "integer"),
            _nullable_variant("submitted_unposted_count", "O-V03.data.submitted_unposted_count", "integer"),
            _nullable_variant("deferred_count", "O-V03.data.deferred_count", "integer"),
            _nullable_variant("expected_amount_minor", "O-V03.data.expected_amount_minor", "integer"),
            _nullable_variant("posted_amount_minor", "O-V03.data.posted_amount_minor", "integer"),
            _nullable_variant("difference_minor", "O-V03.data.difference_minor", "integer"),
            _view(
                "currency",
                "O-V03.data.currency",
                "enum",
                nullable=True,
                enum=("GBP",),
            ),
            _nullable_variant("cash_application_ref", "O-V03.data.cash_application_ref"),
            _nullable_variant("receipt_party_ref", "O-V03.data.receipt_party_ref"),
            _nullable_variant("application_party_ref", "O-V03.data.application_party_ref"),
            _nullable_variant("party_mapping_ref", "O-V03.data.party_mapping_ref"),
            _nullable_variant("identity_match", "O-V03.data.identity_match", "boolean"),
        ),
        ("scenario_ref", "reconciliation_ref"),
        ("O-Q03",),
        ("O-V03",),
    ),
    _dataset(
        "P-D05",
        "reporting_versions",
        ("Atlas",),
        (
            _scenario(),
            _view("reporting_version_ref", "O-V05.data.reporting_version_ref"),
            _view("period_id", "O-V05.data.period_id"),
            _view("version", "O-V05.data.version", "integer"),
            _view("publication_origin", "O-V05.data.publication_origin", "enum", enum=("PRE_SCOPE_IMPORT", "RESTATEMENT_PUBLICATION")),
            _view("published_at", "O-V05.data.published_at", "timestamp"),
            _view("currency", "O-V05.data.currency", "enum", enum=("GBP",)),
            _view("content_ref", "O-V05.data.content_ref"),
            _view("content_verification_status", "O-V05.data.content_verification_status", "enum", enum=("CONTENT_BYTES_VERIFIED", "DECLARED_HASH_ONLY", "MISSING", "UNAVAILABLE")),
            _nullable_variant("predecessor_version_ref", "O-V05.data.predecessor_version_ref"),
            _nullable_variant("restatement_case_ref", "O-V05.data.restatement_case_ref"),
            _nullable_variant("manifest_hash", "O-V05.data.manifest_hash", "hash"),
            _nullable_variant("published_by_event_id", "O-V05.data.published_by_event_id"),
            _nullable_variant("import_attestation_ref", "O-V05.data.import_attestation_ref"),
            _nullable_variant("original_authority_ref", "O-V05.data.original_authority_ref"),
            _nullable_variant("source_ref", "O-V05.data.source_ref"),
        ),
        ("scenario_ref", "reporting_version_ref"),
        ("O-Q05",),
        ("O-V05",),
    ),
    _dataset(
        "P-D06",
        "reporting_values",
        ("Atlas",),
        (
            _scenario(),
            _view("reporting_version_ref", "O-V05.data.reporting_version_ref", transform="PARENT_CONTEXT_COPY"),
            _view("period_id", "O-V05.data.period_id", transform="PARENT_CONTEXT_COPY"),
            _view("statement_field", "O-V05.data.statement_values[].field"),
            _view("label", "O-V05.data.statement_values[].label"),
            _view("amount_minor", "O-V05.data.statement_values[].amount_minor", "integer"),
            _view(
                "currency",
                "O-V05.data.statement_values[].currency",
                "enum",
                enum=("GBP",),
            ),
            _view("content_verification_status", "O-V05.data.statement_values[].content_verification_status", "enum", enum=("CONTENT_BYTES_VERIFIED", "DECLARED_HASH_ONLY", "MISSING", "UNAVAILABLE")),
            _view("trace_available", "O-V05.data.statement_values[].trace_available", "boolean"),
        ),
        ("scenario_ref", "reporting_version_ref", "statement_field"),
        ("O-Q05",),
        ("O-V05",),
    ),
    _dataset(
        "P-D07",
        "restatement_bridges",
        ("Atlas",),
        (
            _scenario(),
            _view("period_id", "O-V04.data.period_id", transform="PARENT_CONTEXT_COPY"),
            _view("predecessor_version_ref", "O-V04.data.restatement_bridge[].predecessor_version_ref"),
            _view("successor_version_ref", "O-V04.data.restatement_bridge[].successor_version_ref"),
            _view("statement_field", "O-V04.data.restatement_bridge[].statement_field"),
            _view("adjustment_minor", "O-V04.data.restatement_bridge[].adjustment_minor", "integer"),
            _view(
                "currency",
                "O-V04.data.restatement_bridge[].currency",
                "enum",
                enum=("GBP",),
            ),
            _view("restatement_case_ref", "O-V04.data.restatement_bridge[].restatement_case_ref"),
        ),
        ("scenario_ref", "predecessor_version_ref", "successor_version_ref", "statement_field"),
        ("O-Q04",),
        ("O-V04",),
    ),
    _dataset(
        "P-D08",
        "assurance_exceptions",
        ("Argus",),
        (
            _scenario(),
            _view("exception_type", "O-V06.data.exception_type", "enum", enum=("RECOGNITION_COMPLETENESS", "CASH_APPLICATION_IDENTITY")),
            _view("test_run_ref", "O-V06.data.test_run_ref"),
            _view("test_definition_ref", "O-V06.data.test_definition_ref"),
            _view("exception_ref", "O-V06.data.exception_ref"),
            _view("assertion", "O-V06.data.assertion"),
            _view("severity", "O-V06.data.severity"),
            _view("related_governance_case_ref", "O-V06.data.related_governance_case_ref"),
            _nullable_variant("period_id", "O-V06.data.period_id"),
            _nullable_variant("expected_amount_minor", "O-V06.data.expected_amount_minor", "integer"),
            _nullable_variant("actual_amount_minor", "O-V06.data.actual_amount_minor", "integer"),
            _nullable_variant("difference_minor", "O-V06.data.difference_minor", "integer"),
            _nullable_variant("receipt_party_ref", "O-V06.data.receipt_party_ref"),
            _nullable_variant("application_party_ref", "O-V06.data.application_party_ref"),
            _nullable_variant("journal_id", "O-V06.data.journal_id"),
            _nullable_variant("amount_minor", "O-V06.data.amount_minor", "integer"),
            _view("currency", "O-V06.data.currency", "enum", enum=("GBP",)),
        ),
        ("scenario_ref", "exception_ref"),
        ("O-Q06",),
        ("O-V06",),
    ),
    _dataset(
        "P-D09",
        "governance_cases",
        ("Aegis",),
        (
            _scenario(),
            *tuple(_view(name, f"O-V07.data.{name}") for name in (
                "exception_ref", "review_ref", "review_disposition", "finding_ref",
                "initial_issue_ref", "initial_issue_status", "owner_ref",
                "remediation_directive_ref", "verification_ref", "final_issue_ref",
                "final_issue_status",
            )),
        ),
        ("scenario_ref", "exception_ref"),
        ("O-Q07",),
        ("O-V07",),
    ),
    _dataset(
        "P-D10",
        "readiness_assessments",
        ("Aegis",),
        (
            _scenario(),
            _view("readiness_ref", "O-V08.data.rows[].readiness_ref"),
            _view("reporting_version_ref", "O-V08.data.reporting_version_ref", transform="PARENT_CONTEXT_COPY"),
            _view("period_id", "O-V08.data.period_id", transform="PARENT_CONTEXT_COPY"),
            _view("purpose_ref", "O-V08.data.rows[].purpose_ref"),
            _view("scope_ref", "O-V08.data.rows[].scope_ref"),
            _view("status", "O-V08.data.rows[].status", "enum", enum=("BLOCKED", "USABLE_WITH_REVIEW", "APPROVED")),
            _view("assessed_by_ref", "O-V08.data.rows[].assessed_by_ref"),
        ),
        ("scenario_ref", "readiness_ref"),
        ("O-Q08",),
        ("O-V08",),
    ),
    _dataset(
        "P-D11",
        "governed_decisions",
        ("Pythia", "source business domain", "Hermes"),
        (
            _scenario(),
            *tuple(
                _view(name, f"O-V09.data.{name}")
                for name in (
                    "planning_input_ref",
                    "reporting_version_ref",
                    "readiness_ref",
                    "purpose_ref",
                    "scope_ref",
                    "decision_ref",
                    "decision_type",
                    "position_ref",
                )
            ),
            _view("original_start_date", "O-V09.data.original_start_date", "date"),
            _view(
                "recommended_start_date",
                "O-V09.data.recommended_start_date",
                "date",
            ),
            _view("monthly_cost_minor", "O-V09.data.monthly_cost_minor", "integer"),
            _view("currency", "O-V09.data.currency", "enum", enum=("GBP",)),
            _view("reason_code", "O-V09.data.reason_code"),
            _view("approval_ref", "O-V09.data.approval_ref"),
            _view(
                "approval_outcome",
                "O-V09.data.approval_outcome",
                "enum",
                enum=("APPROVED", "REJECTED"),
            ),
            _view("candidate_ref", "O-V09.data.candidate_ref"),
            _view(
                "candidate_admission_outcome",
                "O-V09.data.candidate_admission_outcome",
                "enum",
                enum=("ACCEPTED", "REJECTED", "UNSUPPORTED"),
            ),
        ),
        ("scenario_ref", "decision_ref"),
        ("O-Q09",),
        ("O-V09",),
    ),
    _dataset(
        "P-D12",
        "decision_inputs",
        ("Pythia",),
        (
            _scenario(),
            _view("decision_ref", "O-V09.data.decision_ref", transform="PARENT_CONTEXT_COPY"),
            _view("planning_input_ref", "O-V09.data.planning_input_ref", transform="PARENT_CONTEXT_COPY"),
            _ordinal("input_ordinal"),
            _view("input_ref", "O-V09.data.frozen_input_refs[]"),
        ),
        ("scenario_ref", "decision_ref", "input_ordinal"),
        ("O-Q09",),
        ("O-V09",),
    ),
    _dataset(
        "P-D13",
        "correction_cases",
        ("Argus", "Atlas", "Aegis", "shared read model"),
        (
            _scenario(),
            _view("source_projection_ref", "O-V11.data.source_projection_ref"),
            _view("source_projection_hash", "O-V11.data.source_projection_hash", "hash"),
            *tuple(
                _view(name, f"O-V11.data.{name}")
                for name in (
                    "reversal_proposal_ref",
                    "reversal_journal_ref",
                    "replacement_proposal_ref",
                    "replacement_journal_ref",
                    "identity_before",
                    "identity_after",
                )
            ),
            _view(
                "reversal_binding_status",
                "O-V11.data.reversal_binding_status",
                "enum",
                enum=("BOUND_BEFORE_COMPARE",),
            ),
            _view("control_account_net_movement_minor", "O-V11.data.control_account_net_movement_minor", "integer"),
            _view("currency", "O-V11.data.currency", "enum", enum=("GBP",)),
            _view("verification_ref", "O-V11.data.verification_ref"),
            _view("issue_update_ref", "O-V11.data.issue_update_ref"),
        ),
        ("scenario_ref", "verification_ref"),
        ("O-Q11",),
        ("O-V11",),
    ),
    _dataset(
        "P-D14",
        "correction_journals",
        ("Atlas",),
        (
            _scenario(),
            _p_struct("correction_row_key"),
            _col("journal_role", "enum", origin="P_STRUCTURAL_METADATA", transform="REFERENCE_ROLE_MATCH", enum=("REVERSAL", "REPLACEMENT")),
            _view("journal_ref", "O-V11.data.journal_balance_results[].journal_ref"),
            _view("debits_minor", "O-V11.data.journal_balance_results[].debits_minor", "integer"),
            _view("credits_minor", "O-V11.data.journal_balance_results[].credits_minor", "integer"),
            _view(
                "currency",
                "O-V11.data.journal_balance_results[].currency",
                "enum",
                enum=("GBP",),
            ),
            _view("balanced", "O-V11.data.journal_balance_results[].balanced", "boolean"),
        ),
        ("correction_row_key", "journal_role"),
        ("O-Q11",),
        ("O-V11",),
    ),
    _dataset(
        "P-D15",
        "reference_bindings",
        ("shared substrate",),
        (
            _scenario(),
            _p_struct("parent_dataset_id"),
            _p_struct("parent_row_key"),
            _col("reference_role", "enum", origin="P_STRUCTURAL_METADATA", transform="REFERENCE_ROLE_MATCH", enum=("RECONCILIATION_SOURCE", "EXCEPTION_SUBJECT", "EXCEPTION_EVIDENCE", "GOVERNANCE_CORRECTION", "GOVERNANCE_PRIOR_ISSUE", "GOVERNANCE_READINESS", "READINESS_BASIS")),
            _ordinal("reference_ordinal"),
            _view("reference_ref", "O-V*.data.<registered_reference_array>[]"),
        ),
        ("parent_dataset_id", "parent_row_key", "reference_role", "reference_ordinal"),
        ("O-Q03", "O-Q06", "O-Q07", "O-Q08"),
        ("O-V03", "O-V06", "O-V07", "O-V08"),
    ),
    _dataset(
        "P-D16",
        "trace_nodes",
        ("shared substrate",),
        (
            _scenario(),
            _col("reporting_version_ref", origin="O_QUERY_FIELD", path="O-Q10.reporting_version_ref", transform="PARENT_CONTEXT_COPY"),
            _col("statement_field", origin="O_QUERY_FIELD", path="O-Q10.statement_field", transform="PARENT_CONTEXT_COPY"),
            *tuple(_view(name, f"O-V10.data.nodes[].{name}", "hash" if name == "semantic_hash" else "text", nullable=name == "semantic_hash") for name in ("node_ref", "role", "record_family", "record_identity", "semantic_hash")),
        ),
        ("scenario_ref", "reporting_version_ref", "statement_field", "node_ref"),
        ("O-Q10",),
        ("O-V10",),
    ),
    _dataset(
        "P-D17",
        "trace_edges",
        ("shared substrate",),
        (
            _scenario(),
            _col("reporting_version_ref", origin="O_QUERY_FIELD", path="O-Q10.reporting_version_ref", transform="PARENT_CONTEXT_COPY"),
            _col("statement_field", origin="O_QUERY_FIELD", path="O-Q10.statement_field", transform="PARENT_CONTEXT_COPY"),
            *tuple(_view(name, f"O-V10.data.edges[].{name}") for name in ("source_ref", "target_ref", "relationship")),
        ),
        ("scenario_ref", "reporting_version_ref", "statement_field", "source_ref", "target_ref", "relationship"),
        ("O-Q10",),
        ("O-V10",),
    ),
    _dataset(
        "P-D18",
        "query_executions",
        ("shared substrate",),
        (
            _p_struct("query_instance_ref"),
            _col("query_id", "enum", origin="P_STRUCTURAL_METADATA", transform="CONSTANT", enum=("P-Q00", "O-Q01", "O-Q02", "O-Q03", "O-Q04", "O-Q05", "O-Q06", "O-Q07", "O-Q08", "O-Q09", "O-Q10", "O-Q11")),
            _col("view_id", "enum", origin="P_STRUCTURAL_METADATA", transform="CONSTANT", enum=("P-V00", "O-V01", "O-V02", "O-V03", "O-V04", "O-V05", "O-V06", "O-V07", "O-V08", "O-V09", "O-V10", "O-V11")),
            _col("view_contract_version", "integer", origin="P_STRUCTURAL_METADATA", transform="CONSTANT"),
            _col("scope_type", "enum", origin="P_STRUCTURAL_METADATA", transform="CONSTANT", enum=("WORKSPACE", "SCENARIO")),
            _p_struct("scope_ref"),
            _col("query_revision", "integer", origin="P_DISCOVERY_FIELD", path="P-V00.query_revision"),
            _col("semantic_as_of", "timestamp", origin="P_DISCOVERY_FIELD", path="P-V00.semantic_as_of"),
            _col("compatibility_mode", "enum", origin="P_DISCOVERY_FIELD", path="P-V00.compatibility_mode", enum=("EXACT_ORIGINAL",)),
            _p_struct("canonical_request_hash", "hash"),
        ),
        ("query_instance_ref",),
        ("P-Q00", "O-Q01", "O-Q02", "O-Q03", "O-Q04", "O-Q05", "O-Q06", "O-Q07", "O-Q08", "O-Q09", "O-Q10", "O-Q11"),
        ("P-V00", "O-V01", "O-V02", "O-V03", "O-V04", "O-V05", "O-V06", "O-V07", "O-V08", "O-V09", "O-V10", "O-V11"),
    ),
    _dataset(
        "P-D19",
        "query_sources",
        ("shared substrate",),
        (
            _p_struct("query_instance_ref"),
            _ordinal("semantic_source_ordinal"),
            _col("semantic_source_ref", origin="O_ENVELOPE_FIELD", path="O-V*.source_refs[]"),
        ),
        ("query_instance_ref", "semantic_source_ordinal"),
        ("O-Q01", "O-Q02", "O-Q03", "O-Q04", "O-Q05", "O-Q06", "O-Q07", "O-Q08", "O-Q09", "O-Q10", "O-Q11"),
        ("O-V01", "O-V02", "O-V03", "O-V04", "O-V05", "O-V06", "O-V07", "O-V08", "O-V09", "O-V10", "O-V11"),
    ),
    _dataset(
        "P-D20",
        "readiness_limitations",
        ("Aegis",),
        (
            _scenario(),
            _view("readiness_ref", "O-V08.data.rows[].readiness_ref", transform="PARENT_CONTEXT_COPY"),
            _ordinal("limitation_ordinal"),
            _view("limitation_code", "O-V08.data.rows[].limitation_codes[]"),
        ),
        ("scenario_ref", "readiness_ref", "limitation_ordinal"),
        ("O-Q08",),
        ("O-V08",),
    ),
    _dataset(
        "P-D21",
        "scenario_entry_points",
        ("shared substrate",),
        (
            _col("scenario_ref", origin="P_DISCOVERY_FIELD", path="P-V00.entry_points[].scenario_ref", transform="PARENT_CONTEXT_COPY"),
            _view(
                "journey_id",
                "O-V01.data.scenario_entry_points[].journey_id",
                "enum",
                enum=("O-J01", "O-J02", "O-J03", "O-SJ01"),
            ),
            _view(
                "semantic_role",
                "O-V01.data.scenario_entry_points[].semantic_role",
            ),
            _view("exact_ref", "O-V01.data.scenario_entry_points[].exact_ref"),
            _view(
                "source_kind",
                "O-V01.data.scenario_entry_points[].source_kind",
                "enum",
                enum=(
                    "AUTHORITATIVE_RECORD",
                    "CONTRACT_PUBLICATION",
                    "LABELLED_PROJECTION",
                ),
            ),
            _view(
                "availability",
                "O-V01.data.scenario_entry_points[].availability",
                "enum",
                enum=("AVAILABLE", "UNAVAILABLE"),
            ),
        ),
        ("scenario_ref", "journey_id"),
        ("P-Q00", "O-Q01"),
        ("P-V00", "O-V01"),
    ),
)

DATASET_BY_ID = {item.dataset_id: item for item in DATASETS}


def _standard(
    relationship_id: str,
    from_dataset: str,
    from_columns: tuple[str, ...],
    to_dataset: str,
    to_columns: tuple[str, ...],
    *,
    enforcement: str,
) -> dict[str, object]:
    return {
        "cardinality": "MANY_TO_ONE",
        "enforcement": enforcement,
        "from_columns": list(from_columns),
        "from_dataset": from_dataset,
        "from_registry": REGISTRY_ID,
        "relationship_id": relationship_id,
        "relationship_type": "STANDARD",
        "required": True,
        "to_columns": list(to_columns),
        "to_dataset": to_dataset,
        "to_registry": REGISTRY_ID,
    }


def _relationships() -> tuple[dict[str, object], ...]:
    values: list[dict[str, object]] = []
    scenario_children = (
        *(f"P-D{number:02d}" for number in range(3, 18)),
        "P-D20",
        "P-D21",
    )
    for dataset_id in scenario_children:
        values.append(
            _standard(
                f"P-RL01-{dataset_id}",
                dataset_id,
                ("scenario_ref",),
                "P-D02",
                ("scenario_ref",),
                enforcement="CONSUMER_RELATIONSHIP",
            )
        )
    values.extend(
        (
            _standard("P-RL02", "P-D06", ("scenario_ref", "reporting_version_ref"), "P-D05", ("scenario_ref", "reporting_version_ref"), enforcement="CONSUMER_RELATIONSHIP"),
            _standard("P-RL03", "P-D07", ("scenario_ref", "predecessor_version_ref"), "P-D05", ("scenario_ref", "reporting_version_ref"), enforcement="CONSUMER_RELATIONSHIP"),
            _standard("P-RL04", "P-D07", ("scenario_ref", "successor_version_ref"), "P-D05", ("scenario_ref", "reporting_version_ref"), enforcement="CONSUMER_RELATIONSHIP"),
            _standard("P-RL05", "P-D10", ("scenario_ref", "reporting_version_ref"), "P-D05", ("scenario_ref", "reporting_version_ref"), enforcement="CONSUMER_RELATIONSHIP"),
            _standard("P-RL06", "P-D11", ("scenario_ref", "reporting_version_ref"), "P-D05", ("scenario_ref", "reporting_version_ref"), enforcement="CONSUMER_RELATIONSHIP"),
            _standard("P-RL07", "P-D11", ("scenario_ref", "readiness_ref"), "P-D10", ("scenario_ref", "readiness_ref"), enforcement="CONSUMER_RELATIONSHIP"),
            _standard("P-RL08", "P-D12", ("scenario_ref", "decision_ref"), "P-D11", ("scenario_ref", "decision_ref"), enforcement="CONSUMER_RELATIONSHIP"),
            _standard("P-RL09", "P-D14", ("correction_row_key",), "P-D13", ("row_key",), enforcement="CONSUMER_RELATIONSHIP"),
            _standard("P-RL10", "P-D20", ("scenario_ref", "readiness_ref"), "P-D10", ("scenario_ref", "readiness_ref"), enforcement="CONSUMER_RELATIONSHIP"),
            _standard("P-RL11", "P-D17", ("scenario_ref", "reporting_version_ref", "statement_field", "source_ref"), "P-D16", ("scenario_ref", "reporting_version_ref", "statement_field", "node_ref"), enforcement="INTEGRITY_ONLY"),
            _standard("P-RL12", "P-D17", ("scenario_ref", "reporting_version_ref", "statement_field", "target_ref"), "P-D16", ("scenario_ref", "reporting_version_ref", "statement_field", "node_ref"), enforcement="INTEGRITY_ONLY"),
            _standard("P-RL13", "P-D19", ("query_instance_ref",), "P-D18", ("query_instance_ref",), enforcement="CONSUMER_RELATIONSHIP"),
        )
    )
    values.append(
        {
            "allowed_targets": [
                {
                    "dataset_id": dataset_id,
                    "registry_id": REGISTRY_ID,
                    "target_key_columns": ["row_key"],
                }
                for dataset_id in ("P-D04", "P-D08", "P-D09", "P-D10")
            ],
            "dataset_selector_column": "parent_dataset_id",
            "enforcement": "INTEGRITY_ONLY",
            "from_dataset": "P-D15",
            "from_registry": REGISTRY_ID,
            "key_column": "parent_row_key",
            "relationship_id": "P-RL14",
            "relationship_type": "POLYMORPHIC_PARENT",
            "required": True,
        }
    )
    values.append(
        {
            **_standard("P-RL15", "P-D18", ("scope_ref",), "P-D02", ("scenario_ref",), enforcement="INTEGRITY_ONLY"),
            "condition": {"column": "scope_type", "equals": "SCENARIO"},
        }
    )
    return tuple(values)


RELATIONSHIPS = _relationships()


def registry_contract_hash() -> str:
    return canonical_sha256(
        {
            "datasets": [item.schema_document() for item in DATASETS],
            "registry_id": REGISTRY_ID,
            "registry_version": REGISTRY_VERSION,
            "relationships": list(RELATIONSHIPS),
            "storage_key": STORAGE_KEY,
        }
    )
