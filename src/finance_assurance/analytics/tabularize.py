"""Lossless Q-V00/Q-V01..Q-V06 to Q-D01..Q-D16 tabularization."""

from __future__ import annotations

from dataclasses import dataclass

from finance_assurance.analytics.contracts import (
    AnalyticalDiscoveryDescriptor,
    AnalyticalDiscoveryView,
    AnalyticalQuery,
    AnalyticalView,
)
from finance_assurance.analytics.query_service import query_instance_ref
from finance_assurance.exports.tabularize import stable_row_key
from finance_assurance.runtime.canonical import canonical_sha256


@dataclass(frozen=True, slots=True)
class ExecutedAnalyticalQuery:
    request: AnalyticalQuery
    view: AnalyticalView


def _row(dataset_id: str, natural_key: tuple[object, ...], **values: object) -> dict[str, object]:
    return {"row_key": stable_row_key(dataset_id, *natural_key), **values}


def _record(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not isinstance(value.get("body"), dict):
        raise ValueError("analytical exact-record value is invalid")
    return value


def _opaque(value: object) -> str | None:
    return str(value["object_id"]) if isinstance(value, dict) and isinstance(value.get("object_id"), str) else None


def _evidence(body: dict[str, object]) -> list[dict[str, object]]:
    value = body.get("evidence_refs", [])
    if not isinstance(value, list) or any(not isinstance(item, dict) for item in value):
        raise ValueError("evidence_refs is invalid")
    return value  # type: ignore[return-value]


def _add_evidence(rows: dict[str, list[dict[str, object]]], parent_dataset: str, parent_key: str, role: str, values: list[dict[str, object]]) -> None:
    for ordinal, value in enumerate(values):
        evidence_ref = value.get("ref_id", value.get("record_identity"))
        content_hash = value.get("content_hash", value.get("semantic_hash"))
        if not isinstance(evidence_ref, str) or not isinstance(content_hash, str):
            raise ValueError("evidence binding is incomplete")
        rows["Q-D12"].append(_row("Q-D12", (parent_dataset, parent_key, role, ordinal), parent_dataset_id=parent_dataset, parent_row_key=parent_key, evidence_ordinal=ordinal, evidence_role=role, evidence_ref=evidence_ref, description=str(value.get("description", "Exact publication evidence authority")), content_hash=content_hash, verification_status="DECLARED_HASH_ONLY", verification_proof_ref=None))


def _mapping(catalogue: dict[str, object]) -> dict[str, str]:
    values = catalogue.get("mappings")
    if not isinstance(values, list):
        raise ValueError("catalogue mappings are invalid")
    mapped = {str(item["account_id"]): str(item["statement_field"]) for item in values if isinstance(item, dict)}
    if len(mapped) != len(values):
        raise ValueError("catalogue mappings are not unique")
    return mapped


def tabularize_analytics(*, descriptor: AnalyticalDiscoveryDescriptor, discovery: AnalyticalDiscoveryView, executed: tuple[ExecutedAnalyticalQuery, ...], p_package_context: dict[str, object], export_ref: str) -> dict[str, list[dict[str, object]]]:
    rows = {f"Q-D{number:02d}": [] for number in range(1, 17)}
    catalogue_result = next(item for item in executed if item.request.query_id == "Q-Q01")
    catalogue_record = _record(catalogue_result.view.data["catalogue"])
    catalogue = catalogue_record["body"]
    assert isinstance(catalogue, dict)
    mapping = _mapping(catalogue)
    catalog_ref = str(catalogue["catalog_ref"])
    for item in catalogue["accounts"]:  # type: ignore[index]
        rows["Q-D01"].append(_row("Q-D01", (catalog_ref, item["account_id"]), catalog_ref=catalog_ref, **item))
    for item in catalogue["statement_lines"]:  # type: ignore[index]
        rows["Q-D02"].append(_row("Q-D02", (catalog_ref, item["statement_field"]), catalog_ref=catalog_ref, **item))
    for item in catalogue["mappings"]:  # type: ignore[index]
        rows["Q-D03"].append(_row("Q-D03", (catalog_ref, item["account_id"]), catalog_ref=catalog_ref, **item))
    catalogue_header = _row("Q-D15", (catalog_ref,), catalog_id=catalogue["catalog_id"], catalog_version=catalogue["catalog_version"], catalog_ref=catalog_ref, effective_from=catalogue["effective_from"], effective_to=catalogue["effective_to"], status=catalogue["status"], record_semantic_hash=catalogue_record["semantic_hash"])
    rows["Q-D15"].append(catalogue_header)
    _add_evidence(rows, "Q-D15", str(catalogue_header["row_key"]), "CATALOGUE_EVIDENCE", _evidence(catalogue))

    for result in executed:
        scenario_ref = str(result.request.scenario_ref)
        data = result.view.data
        if result.request.query_id == "Q-Q02":
            header_record = _record(data["journal"]); header = header_record["body"]; assert isinstance(header, dict)
            proposal_record = _record(data["proposal"]); proposal = proposal_record["body"]; assert isinstance(proposal, dict)
            event_record = _record(data["posting_event"]); event = event_record["body"]; assert isinstance(event, dict)
            origin = proposal["origin_basis"]; assert isinstance(origin, dict)
            predecessor_record = data["predecessor_proposal"]
            predecessor = _record(predecessor_record) if predecessor_record is not None else None
            predecessor_body = predecessor["body"] if predecessor else None
            predecessor_origin = predecessor_body["origin_basis"] if isinstance(predecessor_body, dict) else None
            origin_type = str(proposal["origin_type"])
            direct_source = origin.get("reverses_journal_id", origin.get("corrects_journal_id"))
            header_row = _row("Q-D04", (scenario_ref, header["journal_id"]), scenario_ref=scenario_ref, journal_id=header["journal_id"], record_semantic_hash=header_record["semantic_hash"], entry_class=header["entry_class"], source_proposal_ref=header["source_proposal_ref"], source_proposal_semantic_hash=proposal_record["semantic_hash"], posted_by_event_id=header["posted_by_event_id"], ledger_period_id=header["ledger_period_id"], effective_date=header["effective_date"], posted_at=header["posted_at"], currency=header["currency"], total_debit_minor=header["total_debit_minor"], total_credit_minor=header["total_credit_minor"], origin_type=origin_type, source_lineage_mode="PREDECESSOR_ORIGIN" if predecessor else "DIRECT_ORIGIN", source_business_event_ref=predecessor_origin.get("business_event_ref") if isinstance(predecessor_origin, dict) else None, source_posting_rule_ref=predecessor_origin.get("posting_rule_ref") if isinstance(predecessor_origin, dict) else None, source_projection_ref=f"J-AR17:{direct_source}" if direct_source else None, reverses_journal_id=origin.get("reverses_journal_id"), corrects_journal_id=origin.get("corrects_journal_id"), restatement_case_ref=origin.get("restatement_case_id"), directive_ref=_opaque(origin.get("directive_ref")), restatement_policy_ref=_opaque(origin.get("restatement_policy_ref")), correction_policy_ref=_opaque(origin.get("correction_policy_ref")), predecessor_proposal_ref=predecessor["record_identity"] if predecessor else None, predecessor_proposal_semantic_hash=predecessor["semantic_hash"] if predecessor else None)
            rows["Q-D04"].append(header_row)
            for line_record in data["lines"]:  # type: ignore[index]
                exact = _record(line_record); line = exact["body"]; assert isinstance(line, dict); dims = line["dimensions"]; assert isinstance(dims, dict)
                rows["Q-D05"].append(_row("Q-D05", (scenario_ref, line["journal_id"], line["line_no"]), scenario_ref=scenario_ref, journal_id=line["journal_id"], journal_line_id=line["journal_line_id"], line_no=line["line_no"], account_id=line["account_id"], statement_field=mapping[str(line["account_id"])], debit_minor=line["debit_minor"], credit_minor=line["credit_minor"], currency=line["currency"], legal_entity_id=dims["legal_entity_id"], customer_id=dims.get("customer_id"), contract_id=dims.get("contract_id"), record_semantic_hash=exact["semantic_hash"]))
            for ordinal, input_hash in enumerate(origin["input_hashes"]):  # type: ignore[index]
                verified = origin_type == "REVERSAL"
                rows["Q-D06"].append(_row("Q-D06", (scenario_ref, header["journal_id"], ordinal), scenario_ref=scenario_ref, journal_id=header["journal_id"], input_ordinal=ordinal, input_hash=input_hash, verification_status="CONTENT_BYTES_VERIFIED" if verified else "DECLARED_HASH_ONLY", verification_proof_ref=f"J-AR17:{origin['reverses_journal_id']}" if verified else None))
            _add_evidence(rows, "Q-D04", str(header_row["row_key"]), "JOURNAL_EVIDENCE", _evidence(header))
            _add_evidence(rows, "Q-D04", str(header_row["row_key"]), "PROPOSAL_EVIDENCE", _evidence(proposal))
            _add_evidence(rows, "Q-D04", str(header_row["row_key"]), "POSTING_EVENT_EVIDENCE", _evidence(event))
        elif result.request.query_id == "Q-Q03":
            exact = _record(data["business_event"]); body = exact["body"]; assert isinstance(body, dict); payload = body["payload"]; assert isinstance(payload, dict)
            row = _row("Q-D07", (scenario_ref, body["business_event_id"]), scenario_ref=scenario_ref, business_event_ref=body["business_event_id"], event_type=body["event_type"], correlation_id=body["correlation_id"], occurred_at=body["occurred_at"], recorded_at=body["recorded_at"], effective_date=body["effective_date"], source_system=body["source_system"], legal_entity_id=body["legal_entity_id"], contract_ref=_opaque(payload["contract_ref"]), recognition_schedule_ref=_opaque(payload["recognition_schedule_ref"]), service_period_start=payload["service_period_start"], service_period_end=payload["service_period_end"], amount_minor=payload["amount_minor"], currency=payload["currency"], record_semantic_hash=exact["semantic_hash"])
            rows["Q-D07"].append(row); _add_evidence(rows, "Q-D07", str(row["row_key"]), "BUSINESS_EVENT_EVIDENCE", _evidence(body))
        elif result.request.query_id == "Q-Q04":
            source = _record(data["source"]); source_body = source["body"]; assert isinstance(source_body, dict)
            publication = _record(data["publication"]); pub = publication["body"]; assert isinstance(pub, dict); payload = pub["canonical_payload"]; basis = pub["publication_basis"]; upstream = pub["upstream_authoritative_refs"][0]["authoritative_ref"]
            source_key = f"J-AR17:{source['record_identity']}"
            row = _row("Q-D08", (scenario_ref, source_key), scenario_ref=scenario_ref, source_projection_ref=source_key, source_hash=payload["source_hash"], j_ar17_semantic_hash=source["semantic_hash"], g13_publication_ref=pub["publication_ref"], g13_publication_semantic_hash=publication["semantic_hash"], g13_payload_hash=pub["payload_hash"], g13_upstream_authoritative_ref=f"{upstream['record_family']}:{upstream['record_identity']}", g13_source_record_semantic_hash=upstream["semantic_hash"], projection_type=payload["projection_type"], projection_version=payload["projection_version"], journal_id=source_body["journal_id"], ledger_period_id=source_body["ledger_period_id"], currency=source_body["currency"], authored_by_f=payload["authored_by_f"], publication_basis_type=basis["basis_type"], publication_admission_identity=basis["admission_identity"], publication_referenced_source_ref=basis["referenced_source_ref"])
            rows["Q-D08"].append(row)
            for line in source_body["line_tuples"]:
                dims=line["dimensions"]
                rows["Q-D09"].append(_row("Q-D09", (scenario_ref, source_key, line["line_no"]), scenario_ref=scenario_ref, source_projection_ref=source_key, journal_id=source_body["journal_id"], line_no=line["line_no"], account_id=line["account_id"], statement_field=mapping[str(line["account_id"])], debit_minor=line["debit_minor"], credit_minor=line["credit_minor"], currency=line["currency"], legal_entity_id=dims["legal_entity_id"], customer_id=dims.get("customer_id"), contract_id=dims.get("contract_id")))
            _add_evidence(rows, "Q-D08", str(row["row_key"]), "REFERENCED_PUBLICATION_EVIDENCE", _evidence(pub))
        elif result.request.query_id == "Q-Q05":
            variant = str(data["state_basis_type"]); exact = _record(data["base_fact"] if variant == "BASE_FACT" else data["publication"]); transition = _record(data["transition_event"]) if data["transition_event"] else None
            body = exact["body"]; assert isinstance(body, dict); period = body if variant == "BASE_FACT" else body["canonical_payload"]; assert isinstance(period, dict)
            row = _row("Q-D10", (period["period_id"], variant), period_id=period["period_id"], state_basis_type=variant, state_authoritative_ref=f"{exact['record_family']}:{exact['record_identity']}", state_record_semantic_hash=exact["semantic_hash"], state_token=result.request.state_token, status=period["status"], start_date=period["start_date"], end_date=period["end_date"], ledger_currency=period["ledger_currency"], opened_at=period.get("opened_at"), soft_closed_at=period.get("soft_closed_at"), soft_close_event_id=period.get("soft_close_event_id"), hard_closed_at=period.get("hard_closed_at"), hard_close_event_id=period.get("hard_close_event_id"), close_policy_ref=_opaque(period.get("close_policy_ref")), state_publication_ref=body.get("publication_ref") if variant != "BASE_FACT" else None, transition_event_ref=transition["record_identity"] if transition else None)
            rows["Q-D10"].append(row)
            if transition:
                tb=transition["body"]; assert isinstance(tb, dict); _add_evidence(rows, "Q-D10", str(row["row_key"]), "PERIOD_EVIDENCE", _evidence(tb))
        elif result.request.query_id == "Q-Q06":
            exact=_record(data["posting_rule"]); body=exact["body"]; assert isinstance(body, dict)
            row=_row("Q-D11", (body["posting_rule_ref"],), posting_rule_ref=body["posting_rule_ref"], posting_rule_id=body["posting_rule_id"], rule_version=body["rule_version"], trigger_event_type=body["trigger_event_type"], effective_from=body["effective_from"], effective_to=body["effective_to"], status=body["status"], content_ref=body["content_ref"], content_hash=body["content_hash"], content_schema_version=body["content_schema_version"], record_semantic_hash=exact["semantic_hash"])
            rows["Q-D11"].append(row); _add_evidence(rows, "Q-D11", str(row["row_key"]), "POSTING_RULE_EVIDENCE", _evidence(body))

    q00_request = {"discovery_descriptor_ref": discovery.discovery_descriptor_ref, "semantic_as_of": str(discovery.semantic_as_of), "workspace_ref": discovery.workspace_ref}
    q00_instance = f"Q00:{canonical_sha256(q00_request)[7:31]}"
    rows["Q-D13"].append(_row("Q-D13", (q00_instance,), query_instance_ref=q00_instance, query_id="Q-Q00", view_contract="Q-V00", view_contract_version=1, scope_type="WORKSPACE", scope_ref=discovery.workspace_ref, canonical_request_hash=canonical_sha256(q00_request), query_revision=discovery.query_revision, semantic_as_of=str(discovery.semantic_as_of), compatibility_mode=discovery.compatibility_mode))
    for result in executed:
        instance=query_instance_ref(result.request)
        rows["Q-D13"].append(_row("Q-D13", (instance,), query_instance_ref=instance, query_id=result.request.query_id, view_contract=result.view.view_contract, view_contract_version=1, scope_type="SCENARIO", scope_ref=str(result.request.scenario_ref), canonical_request_hash=result.request.request_hash, query_revision=result.view.query_revision, semantic_as_of=str(result.view.semantic_as_of_time), compatibility_mode=result.view.compatibility_mode))
        for ordinal, source in enumerate(result.view.source_refs):
            rows["Q-D14"].append(_row("Q-D14", (instance, ordinal), query_instance_ref=instance, source_ordinal=ordinal, source_family=str(source).split(":",1)[0], source_ref=source))
    rows["Q-D16"].append(_row("Q-D16", (discovery.discovery_descriptor_ref,), p_package_context_row_key=stable_row_key("P-D01", export_ref), workspace_ref=discovery.workspace_ref, p_discovery_descriptor_ref=descriptor.p_discovery_descriptor_ref, p_discovery_descriptor_hash=p_package_context["discovery_descriptor_hash"], q_discovery_descriptor_ref=discovery.discovery_descriptor_ref, q_discovery_descriptor_hash=discovery.discovery_descriptor_hash, evidence_registry_id="P-EVIDENCE", evidence_registry_version=1, analytical_registry_id="Q-ANALYTICS", analytical_registry_version=1, query_revision=discovery.query_revision, semantic_as_of=str(discovery.semantic_as_of), compatibility_mode=discovery.compatibility_mode, scenario_set_digest=discovery.scenario_set_digest, ledger_semantics_catalog_ref=discovery.ledger_semantics_catalog_ref, relationship_contract_version=2))
    return rows
