"""Closed Q-ANALYTICS@v1 dataset and relationship registry."""

from __future__ import annotations

from dataclasses import dataclass

from finance_assurance.exports.registry import ColumnDefinition
from finance_assurance.runtime.canonical import canonical_sha256

REGISTRY_ID = "Q-ANALYTICS"
REGISTRY_VERSION = 1
STORAGE_KEY = "q-analytics-v1"


@dataclass(frozen=True, slots=True)
class AnalyticalDatasetDefinition:
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


def _column(name: str, type_: str = "text", *, nullable: bool = False, origin: str = "EXACT_VIEW_FIELD", transformation: str = "EXACT_COPY", enum: tuple[str, ...] = ()) -> ColumnDefinition:
    return ColumnDefinition(name=name, type=type_, nullable=nullable, description=f"Artifact Q contract column {name}.", value_origin=origin, transformation=transformation, enum_values=enum)  # type: ignore[arg-type]


def _dataset(dataset_id: str, name: str, owners: tuple[str, ...], fields: tuple[ColumnDefinition, ...], natural_key: tuple[str, ...], queries: tuple[str, ...], views: tuple[str, ...]) -> AnalyticalDatasetDefinition:
    return AnalyticalDatasetDefinition(dataset_id, name, "shared substrate", owners, f"Closed Artifact Q analytical dataset {name}.", (_column("row_key", origin="PACKAGE_STRUCTURAL_METADATA", transformation="STABLE_ROW_KEY"), *fields), (("row_key",), natural_key), queries, views)


def _t(name: str, **kwargs: object) -> ColumnDefinition:
    return _column(name, **kwargs)  # type: ignore[arg-type]


def _i(name: str, **kwargs: object) -> ColumnDefinition:
    return _column(name, "integer", **kwargs)  # type: ignore[arg-type]


def _b(name: str, **kwargs: object) -> ColumnDefinition:
    return _column(name, "boolean", **kwargs)  # type: ignore[arg-type]


def _h(name: str, **kwargs: object) -> ColumnDefinition:
    return _column(name, "hash", **kwargs)  # type: ignore[arg-type]


def _n(name: str, type_: str = "text") -> ColumnDefinition:
    return _column(name, type_, nullable=True)


DATASETS = (
    _dataset("Q-D01", "accounts", ("Atlas",), tuple(_t(x) for x in ("catalog_ref", "account_id", "account_name", "account_class", "normal_balance", "control_role")), ("catalog_ref", "account_id"), ("Q-Q01",), ("Q-V01",)),
    _dataset("Q-D02", "statement_lines", ("Atlas",), (_t("catalog_ref"), _t("statement_field"), _t("statement_label"), _t("statement_class"), _i("display_order")), ("catalog_ref", "statement_field"), ("Q-Q01",), ("Q-V01",)),
    _dataset("Q-D03", "account_statement_mappings", ("Atlas",), tuple(_t(x) for x in ("catalog_ref", "account_id", "statement_field", "mapping_role")), ("catalog_ref", "account_id"), ("Q-Q01",), ("Q-V01",)),
    _dataset("Q-D04", "journal_headers", ("Atlas",), (
        _t("scenario_ref"), _t("journal_id"), _h("record_semantic_hash"), _t("entry_class"), _t("source_proposal_ref"), _h("source_proposal_semantic_hash"), _t("posted_by_event_id"), _t("ledger_period_id"), _t("effective_date", type_="date"), _t("posted_at", type_="timestamp"), _t("currency"), _i("total_debit_minor"), _i("total_credit_minor"), _t("origin_type"), _t("source_lineage_mode"), _n("source_business_event_ref"), _n("source_posting_rule_ref"), _n("source_projection_ref"), _n("reverses_journal_id"), _n("corrects_journal_id"), _n("restatement_case_ref"), _n("directive_ref"), _n("restatement_policy_ref"), _n("correction_policy_ref"), _n("predecessor_proposal_ref"), _n("predecessor_proposal_semantic_hash", "hash")
    ), ("scenario_ref", "journal_id"), ("Q-Q02",), ("Q-V02",)),
    _dataset("Q-D05", "journal_lines", ("Atlas",), (_t("scenario_ref"), _t("journal_id"), _t("journal_line_id"), _i("line_no"), _t("account_id"), _t("statement_field"), _i("debit_minor"), _i("credit_minor"), _t("currency"), _t("legal_entity_id"), _n("customer_id"), _n("contract_id"), _h("record_semantic_hash")), ("scenario_ref", "journal_id", "line_no"), ("Q-Q02",), ("Q-V02",)),
    _dataset("Q-D06", "journal_input_hashes", ("Atlas", "shared substrate"), (_t("scenario_ref"), _t("journal_id"), _i("input_ordinal"), _h("input_hash"), _t("verification_status"), _n("verification_proof_ref")), ("scenario_ref", "journal_id", "input_ordinal"), ("Q-Q02",), ("Q-V02",)),
    _dataset("Q-D07", "business_events", ("SourceDomain", "shared substrate"), (_t("scenario_ref"), _t("business_event_ref"), _t("event_type"), _t("correlation_id"), _t("occurred_at", type_="timestamp"), _t("recorded_at", type_="timestamp"), _t("effective_date", type_="date"), _t("source_system"), _t("legal_entity_id"), _t("contract_ref"), _t("recognition_schedule_ref"), _t("service_period_start", type_="date"), _t("service_period_end", type_="date"), _i("amount_minor"), _t("currency"), _h("record_semantic_hash")), ("scenario_ref", "business_event_ref"), ("Q-Q03",), ("Q-V03",)),
    _dataset("Q-D08", "referenced_journals", ("AtlasReadBoundary",), (*tuple(_t(x) for x in ("scenario_ref", "source_projection_ref", "source_hash", "j_ar17_semantic_hash", "g13_publication_ref", "g13_publication_semantic_hash", "g13_payload_hash", "g13_upstream_authoritative_ref", "g13_source_record_semantic_hash", "projection_type", "journal_id", "ledger_period_id", "currency", "publication_basis_type", "publication_admission_identity", "publication_referenced_source_ref")), _i("projection_version"), _b("authored_by_f")), ("scenario_ref", "source_projection_ref"), ("Q-Q04",), ("Q-V04",)),
    _dataset("Q-D09", "referenced_journal_lines", ("AtlasReadBoundary",), (_t("scenario_ref"), _t("source_projection_ref"), _t("journal_id"), _i("line_no"), _t("account_id"), _t("statement_field"), _i("debit_minor"), _i("credit_minor"), _t("currency"), _t("legal_entity_id"), _n("customer_id"), _n("contract_id")), ("scenario_ref", "source_projection_ref", "line_no"), ("Q-Q04",), ("Q-V04",)),
    _dataset("Q-D10", "accounting_periods", ("Atlas",), (_t("period_id"), _t("state_basis_type"), _t("state_authoritative_ref"), _h("state_record_semantic_hash"), _n("state_token"), _t("status"), _t("start_date", type_="date"), _t("end_date", type_="date"), _t("ledger_currency"), _n("opened_at", "timestamp"), _n("soft_closed_at", "timestamp"), _n("soft_close_event_id"), _n("hard_closed_at", "timestamp"), _n("hard_close_event_id"), _n("close_policy_ref"), _n("state_publication_ref"), _n("transition_event_ref")), ("period_id", "state_basis_type"), ("Q-Q05",), ("Q-V05",)),
    _dataset("Q-D11", "posting_rules", ("Atlas",), (_t("posting_rule_ref"), _t("posting_rule_id"), _i("rule_version"), _t("trigger_event_type"), _t("effective_from", type_="date"), _n("effective_to", "date"), _t("status"), _t("content_ref"), _h("content_hash"), _i("content_schema_version"), _h("record_semantic_hash")), ("posting_rule_ref",), ("Q-Q06",), ("Q-V06",)),
    _dataset("Q-D12", "analytical_evidence_bindings", ("shared substrate",), (_t("parent_dataset_id"), _t("parent_row_key"), _i("evidence_ordinal"), _t("evidence_role"), _t("evidence_ref"), _t("description"), _h("content_hash"), _t("verification_status"), _n("verification_proof_ref")), ("parent_dataset_id", "parent_row_key", "evidence_role", "evidence_ordinal"), ("Q-Q01", "Q-Q02", "Q-Q03", "Q-Q04", "Q-Q05", "Q-Q06"), ("Q-V01", "Q-V02", "Q-V03", "Q-V04", "Q-V05", "Q-V06")),
    _dataset("Q-D13", "analytical_query_executions", ("shared substrate",), (_t("query_instance_ref"), _t("query_id"), _t("view_contract"), _i("view_contract_version"), _t("scope_type"), _t("scope_ref"), _h("canonical_request_hash"), _i("query_revision"), _t("semantic_as_of", type_="timestamp"), _t("compatibility_mode")), ("query_instance_ref",), ("Q-Q00", "Q-Q01", "Q-Q02", "Q-Q03", "Q-Q04", "Q-Q05", "Q-Q06"), ("Q-V00", "Q-V01", "Q-V02", "Q-V03", "Q-V04", "Q-V05", "Q-V06")),
    _dataset("Q-D14", "analytical_query_sources", ("shared substrate",), (_t("query_instance_ref"), _i("source_ordinal"), _t("source_family"), _t("source_ref")), ("query_instance_ref", "source_ordinal"), ("Q-Q01", "Q-Q02", "Q-Q03", "Q-Q04", "Q-Q05", "Q-Q06"), ("Q-V01", "Q-V02", "Q-V03", "Q-V04", "Q-V05", "Q-V06")),
    _dataset("Q-D15", "ledger_semantics_catalogues", ("Atlas",), (_t("catalog_id"), _i("catalog_version"), _t("catalog_ref"), _t("effective_from", type_="date"), _n("effective_to", "date"), _t("status"), _h("record_semantic_hash")), ("catalog_ref",), ("Q-Q01",), ("Q-V01",)),
    _dataset("Q-D16", "analytical_context", ("shared substrate",), (_t("p_package_context_row_key"), _t("workspace_ref"), _t("p_discovery_descriptor_ref"), _h("p_discovery_descriptor_hash"), _t("q_discovery_descriptor_ref"), _h("q_discovery_descriptor_hash"), _t("evidence_registry_id"), _i("evidence_registry_version"), _t("analytical_registry_id"), _i("analytical_registry_version"), _i("query_revision"), _t("semantic_as_of", type_="timestamp"), _t("compatibility_mode"), _h("scenario_set_digest"), _t("ledger_semantics_catalog_ref"), _i("relationship_contract_version")), ("q_discovery_descriptor_ref",), ("Q-Q00",), ("Q-V00",)),
)

DATASET_BY_ID = {item.dataset_id: item for item in DATASETS}


def _standard(rid: str, fr: str, fc: tuple[str, ...], tr: str, tc: tuple[str, ...], *, from_registry: str = REGISTRY_ID, to_registry: str = REGISTRY_ID, enforcement: str = "CONSUMER_RELATIONSHIP", condition: dict[str, str] | None = None) -> dict[str, object]:
    value: dict[str, object] = {"relationship_id": rid, "relationship_type": "STANDARD", "from_registry": from_registry, "from_dataset": fr, "from_columns": list(fc), "to_registry": to_registry, "to_dataset": tr, "to_columns": list(tc), "cardinality": "MANY_TO_ONE", "required": True, "enforcement": enforcement}
    if condition is not None:
        value["condition"] = condition
    return value


def _relationships() -> tuple[dict[str, object], ...]:
    r: list[dict[str, object]] = [
        _standard("Q-RL01", "Q-D03", ("account_id",), "Q-D01", ("account_id",)),
        _standard("Q-RL02", "Q-D03", ("statement_field",), "Q-D02", ("statement_field",)),
        _standard("Q-RL03", "Q-D05", ("journal_id",), "Q-D04", ("journal_id",)),
        _standard("Q-RL04", "Q-D05", ("account_id",), "Q-D01", ("account_id",)),
        _standard("Q-RL05", "Q-D05", ("statement_field",), "Q-D02", ("statement_field",)),
        _standard("Q-RL06", "Q-D06", ("journal_id",), "Q-D04", ("journal_id",)),
        _standard("Q-RL07", "Q-D09", ("source_projection_ref",), "Q-D08", ("source_projection_ref",)),
        _standard("Q-RL08", "Q-D09", ("account_id",), "Q-D01", ("account_id",)),
        _standard("Q-RL09", "Q-D09", ("statement_field",), "Q-D02", ("statement_field",)),
        _standard("Q-RL10", "Q-D04", ("ledger_period_id",), "Q-D10", ("period_id",)),
        _standard("Q-RL11", "Q-D08", ("ledger_period_id",), "Q-D10", ("period_id",)),
        _standard("Q-RL13", "Q-D14", ("query_instance_ref",), "Q-D13", ("query_instance_ref",)),
        _standard("Q-RL14", "P-D06", ("statement_field",), "Q-D02", ("statement_field",), from_registry="P-EVIDENCE"),
        _standard("Q-RL15", "P-D07", ("statement_field",), "Q-D02", ("statement_field",), from_registry="P-EVIDENCE"),
        _standard("Q-RL16", "P-D13", ("source_projection_ref",), "Q-D08", ("source_projection_ref",), from_registry="P-EVIDENCE"),
        _standard("Q-RL17", "P-D14", ("journal_ref",), "Q-D04", ("journal_id",), from_registry="P-EVIDENCE"),
        _standard("Q-RL18", "Q-D04", ("source_business_event_ref",), "Q-D07", ("business_event_ref",), enforcement="INTEGRITY_ONLY", condition={"column": "source_lineage_mode", "equals": "PREDECESSOR_ORIGIN"}),
        _standard("Q-RL19", "Q-D04", ("source_posting_rule_ref",), "Q-D11", ("posting_rule_ref",), enforcement="INTEGRITY_ONLY", condition={"column": "source_lineage_mode", "equals": "PREDECESSOR_ORIGIN"}),
        _standard("Q-RL20", "Q-D04", ("source_projection_ref",), "Q-D08", ("source_projection_ref",), enforcement="INTEGRITY_ONLY", condition={"column": "source_lineage_mode", "equals": "DIRECT_ORIGIN"}),
        _standard("Q-RL21", "Q-D01", ("catalog_ref",), "Q-D15", ("catalog_ref",)),
        _standard("Q-RL22", "Q-D02", ("catalog_ref",), "Q-D15", ("catalog_ref",)),
        _standard("Q-RL23", "Q-D03", ("catalog_ref",), "Q-D15", ("catalog_ref",)),
    ]
    r.append({"relationship_id": "Q-RL12", "relationship_type": "POLYMORPHIC_PARENT", "from_registry": REGISTRY_ID, "from_dataset": "Q-D12", "dataset_selector_column": "parent_dataset_id", "key_column": "parent_row_key", "allowed_targets": [{"registry_id": REGISTRY_ID, "dataset_id": item, "target_key_columns": ["row_key"]} for item in ("Q-D04", "Q-D07", "Q-D08", "Q-D10", "Q-D11", "Q-D15")], "required": True, "enforcement": "INTEGRITY_ONLY"})
    for dataset_id in ("Q-D04", "Q-D05", "Q-D06", "Q-D07", "Q-D08", "Q-D09"):
        r.append(_standard(f"Q-RL24-{dataset_id}", dataset_id, ("scenario_ref",), "P-D02", ("scenario_ref",), to_registry="P-EVIDENCE"))
    r.extend((
        _standard("Q-RL25", "Q-D13", ("scope_ref",), "P-D02", ("scenario_ref",), to_registry="P-EVIDENCE", enforcement="INTEGRITY_ONLY", condition={"column": "scope_type", "equals": "SCENARIO"}),
        _standard("Q-RL26", "Q-D04", ("scenario_ref", "restatement_case_ref"), "P-D05", ("scenario_ref", "restatement_case_ref"), to_registry="P-EVIDENCE", enforcement="INTEGRITY_ONLY", condition={"column": "origin_type", "equals": "RESTATEMENT_ADJUSTMENT"}),
        _standard("Q-RL27", "Q-D16", ("p_package_context_row_key",), "P-D01", ("row_key",), to_registry="P-EVIDENCE", enforcement="INTEGRITY_ONLY"),
        _standard("Q-RL28", "Q-D16", ("ledger_semantics_catalog_ref",), "Q-D15", ("catalog_ref",), enforcement="INTEGRITY_ONLY"),
    ))
    return tuple(r)


RELATIONSHIPS = _relationships()


def registry_contract_hash() -> str:
    return canonical_sha256({"datasets": [item.schema_document() for item in DATASETS], "registry_id": REGISTRY_ID, "registry_version": REGISTRY_VERSION, "relationships": list(RELATIONSHIPS), "storage_key": STORAGE_KEY})
