"""Lossless O-V00/O-V01..O-V11 to P-D01..P-D21 tabularization."""

from __future__ import annotations

from dataclasses import dataclass

from finance_assurance.exports.contracts import ExportDiscoveryView
from finance_assurance.product.contracts import PublicSuccessEnvelope
from finance_assurance.product.query_models import PublicQuery
from finance_assurance.runtime.canonical import canonical_sha256


@dataclass(frozen=True, slots=True)
class ExecutedPublicQuery:
    request: PublicQuery
    envelope: PublicSuccessEnvelope
    canonical_request_hash: str
    query_instance_ref: str


def stable_row_key(dataset_id: str, *natural_key: object) -> str:
    digest = canonical_sha256([dataset_id, *natural_key]).removeprefix("sha256:")
    return f"{dataset_id}:{digest[:24]}"


def query_instance_ref(request_body: object) -> str:
    digest = canonical_sha256(request_body).removeprefix("sha256:")
    return f"QUERY:{digest[:24]}"


def _row(dataset_id: str, natural_key: tuple[object, ...], **values: object) -> dict[str, object]:
    return {"row_key": stable_row_key(dataset_id, *natural_key), **values}


def _data(item: ExecutedPublicQuery) -> dict[str, object]:
    value = item.envelope.data.model_dump(mode="json")
    if not isinstance(value, dict):
        raise TypeError("Artifact O view data must be an object")
    return value


def _only(executed: tuple[ExecutedPublicQuery, ...], query_id: str) -> ExecutedPublicQuery:
    values = tuple(item for item in executed if item.request.query_id == query_id)
    if len(values) != 1:
        raise ValueError(f"expected exactly one {query_id} result")
    return values[0]


def tabularize(
    *,
    discovery: ExportDiscoveryView,
    executed: tuple[ExecutedPublicQuery, ...],
    export_ref: str,
    exported_at: str,
    producer_release: str,
) -> dict[str, list[dict[str, object]]]:
    """Return the complete closed P-EVIDENCE row registry."""

    rows: dict[str, list[dict[str, object]]] = {
        f"P-D{number:02d}": [] for number in range(1, 22)
    }
    manifest = _only(executed, "O-Q01")
    overview = _only(executed, "O-Q02")
    manifest_data = _data(manifest)
    overview_data = _data(overview)
    rows["P-D01"].append(
        _row(
            "P-D01",
            (export_ref,),
            export_ref=export_ref,
            workspace_ref=manifest_data["workspace_ref"],
            runtime_release=manifest_data["runtime_release"],
            query_revision=manifest.envelope.query_revision,
            semantic_as_of=str(manifest.envelope.semantic_as_of_time),
            exported_at=exported_at,
            compatibility_mode=manifest.envelope.compatibility_read_mode,
            synthetic_data=True,
            synthetic_data_notice=manifest_data["synthetic_data_notice"],
            authoritative_inventory_digest=manifest_data[
                "authoritative_inventory_digest"
            ],
            projection_generation_ref=manifest_data["projection_generation_ref"],
            producer_release=producer_release,
            verification_status=manifest_data["verification_status"],
            company_label=overview_data["company_label"],
            reporting_period=overview_data["reporting_period"],
            headline_reporting_version_ref=overview_data[
                "headline_reporting_version_ref"
            ],
            machine_exception_count=overview_data["machine_exception_count"],
            governed_decision_ref=overview_data["governed_decision_ref"],
            scenario_set_digest=discovery.scenario_set_digest,
            discovery_descriptor_ref=discovery.discovery_descriptor_ref,
            discovery_descriptor_hash=discovery.discovery_descriptor_hash,
            evidence_registry_version="P-EVIDENCE@v1",
        )
    )

    summaries = {
        str(item["scenario_ref"]): item for item in manifest_data["scenario_summaries"]
    }
    for scenario in discovery.scenarios:
        summary = summaries[scenario.scenario_ref]
        rows["P-D02"].append(
            _row(
                "P-D02",
                (scenario.scenario_ref,),
                scenario_ref=scenario.scenario_ref,
                canonical_family=scenario.canonical_family,
                status=summary["status"],
                public_role=scenario.public_role,
                entry_point_count=summary["entry_point_count"],
            )
        )

    c001_ref = next(
        item.scenario_ref
        for item in discovery.scenarios
        if item.canonical_family == "C-001"
    )
    for item in overview_data["module_summaries"]:
        rows["P-D03"].append(
            _row(
                "P-D03",
                (c001_ref, item["module"]),
                scenario_ref=c001_ref,
                module=item["module"],
                summary_code=item["summary_code"],
                primary_product_ref=item["primary_product_ref"],
            )
        )

    parent_refs: list[tuple[str, str, str, str, int, str]] = []
    for result in executed:
        query_id = result.request.query_id
        data = _data(result)
        scenario_ref = str(result.request.scenario_ref)
        if query_id == "O-Q03":
            reconciliation_ref = str(data["reconciliation_ref"])
            row = _row(
                "P-D04",
                (scenario_ref, reconciliation_ref),
                scenario_ref=scenario_ref,
                reconciliation_ref=reconciliation_ref,
                reconciliation_type=data["reconciliation_type"],
                scope_ref=data["scope_ref"],
                performed_at=data["performed_at"],
                reconciliation_status=data["reconciliation_status"],
                downstream_exception_ref=data["downstream_exception_ref"],
                period_id=data.get("period_id"),
                expected_item_count=data.get("expected_item_count"),
                posted_item_count=data.get("posted_item_count"),
                submitted_unposted_count=data.get("submitted_unposted_count"),
                deferred_count=data.get("deferred_count"),
                expected_amount_minor=data.get("expected_amount_minor"),
                posted_amount_minor=data.get("posted_amount_minor"),
                difference_minor=data.get("difference_minor"),
                currency=data.get("currency"),
                cash_application_ref=data.get("cash_application_ref"),
                receipt_party_ref=data.get("receipt_party_ref"),
                application_party_ref=data.get("application_party_ref"),
                party_mapping_ref=data.get("party_mapping_ref"),
                identity_match=data.get("identity_match"),
            )
            rows["P-D04"].append(row)
            for ordinal, ref in enumerate(data["source_refs"]):
                parent_refs.append(
                    (
                        scenario_ref,
                        "P-D04",
                        str(row["row_key"]),
                        "RECONCILIATION_SOURCE",
                        ordinal,
                        str(ref),
                    )
                )
        elif query_id == "O-Q04":
            for item in data["restatement_bridge"]:
                rows["P-D07"].append(
                    _row(
                        "P-D07",
                        (
                            scenario_ref,
                            item["predecessor_version_ref"],
                            item["successor_version_ref"],
                            item["statement_field"],
                        ),
                        scenario_ref=scenario_ref,
                        period_id=data["period_id"],
                        predecessor_version_ref=item["predecessor_version_ref"],
                        successor_version_ref=item["successor_version_ref"],
                        statement_field=item["statement_field"],
                        adjustment_minor=item["adjustment_minor"],
                        currency=item["currency"],
                        restatement_case_ref=item["restatement_case_ref"],
                    )
                )
        elif query_id == "O-Q05":
            version_ref = str(data["reporting_version_ref"])
            version_row = {
                "scenario_ref": scenario_ref,
                "reporting_version_ref": version_ref,
                "period_id": data["period_id"],
                "version": data["version"],
                "publication_origin": data["publication_origin"],
                "published_at": data["published_at"],
                "currency": data["currency"],
                "content_ref": data["content_ref"],
                "content_verification_status": data["content_verification_status"],
                "predecessor_version_ref": data.get("predecessor_version_ref"),
                "restatement_case_ref": data.get("restatement_case_ref"),
                "manifest_hash": data.get("manifest_hash"),
                "published_by_event_id": data.get("published_by_event_id"),
                "import_attestation_ref": data.get("import_attestation_ref"),
                "original_authority_ref": data.get("original_authority_ref"),
                "source_ref": data.get("source_ref"),
            }
            rows["P-D05"].append(
                _row("P-D05", (scenario_ref, version_ref), **version_row)
            )
            for value in data["statement_values"]:
                rows["P-D06"].append(
                    _row(
                        "P-D06",
                        (scenario_ref, version_ref, value["field"]),
                        scenario_ref=scenario_ref,
                        reporting_version_ref=version_ref,
                        period_id=data["period_id"],
                        statement_field=value["field"],
                        label=value["label"],
                        amount_minor=value["amount_minor"],
                        currency=value["currency"],
                        content_verification_status=value[
                            "content_verification_status"
                        ],
                        trace_available=value["trace_available"],
                    )
                )
        elif query_id == "O-Q06":
            exception_ref = str(data["exception_ref"])
            row = _row(
                "P-D08",
                (scenario_ref, exception_ref),
                scenario_ref=scenario_ref,
                exception_type=data["exception_type"],
                test_run_ref=data["test_run_ref"],
                test_definition_ref=data["test_definition_ref"],
                exception_ref=exception_ref,
                assertion=data["assertion"],
                severity=data["severity"],
                related_governance_case_ref=data["related_governance_case_ref"],
                period_id=data.get("period_id"),
                expected_amount_minor=data.get("expected_amount_minor"),
                actual_amount_minor=data.get("actual_amount_minor"),
                difference_minor=data.get("difference_minor"),
                receipt_party_ref=data.get("receipt_party_ref"),
                application_party_ref=data.get("application_party_ref"),
                journal_id=data.get("journal_id"),
                amount_minor=data.get("amount_minor"),
                currency=data["currency"],
            )
            rows["P-D08"].append(row)
            for role, field in (
                ("EXCEPTION_SUBJECT", "subject_refs"),
                ("EXCEPTION_EVIDENCE", "evidence_refs"),
            ):
                for ordinal, ref in enumerate(data.get(field, [])):
                    parent_refs.append(
                        (
                            scenario_ref,
                            "P-D08",
                            str(row["row_key"]),
                            role,
                            ordinal,
                            str(ref),
                        )
                    )
        elif query_id == "O-Q07":
            row = _row(
                "P-D09",
                (scenario_ref, data["exception_ref"]),
                scenario_ref=scenario_ref,
                exception_ref=data["exception_ref"],
                review_ref=data["review_ref"],
                review_disposition=data["review_disposition"],
                finding_ref=data["finding_ref"],
                initial_issue_ref=data["initial_issue_ref"],
                initial_issue_status=data["initial_issue_status"],
                owner_ref=data["owner_ref"],
                remediation_directive_ref=data["remediation_directive_ref"],
                verification_ref=data["verification_ref"],
                final_issue_ref=data["final_issue_ref"],
                final_issue_status=data["final_issue_status"],
            )
            rows["P-D09"].append(row)
            for role, field in (
                ("GOVERNANCE_CORRECTION", "correction_refs"),
                ("GOVERNANCE_PRIOR_ISSUE", "prior_issue_refs"),
                ("GOVERNANCE_READINESS", "readiness_refs"),
            ):
                for ordinal, ref in enumerate(data[field]):
                    parent_refs.append(
                        (
                            scenario_ref,
                            "P-D09",
                            str(row["row_key"]),
                            role,
                            ordinal,
                            str(ref),
                        )
                    )
        elif query_id == "O-Q08":
            for item in data["rows"]:
                readiness_ref = str(item["readiness_ref"])
                row = _row(
                    "P-D10",
                    (scenario_ref, readiness_ref),
                    scenario_ref=scenario_ref,
                    readiness_ref=readiness_ref,
                    reporting_version_ref=data["reporting_version_ref"],
                    period_id=data["period_id"],
                    purpose_ref=item["purpose_ref"],
                    scope_ref=item["scope_ref"],
                    status=item["status"],
                    assessed_by_ref=item["assessed_by_ref"],
                )
                rows["P-D10"].append(row)
                for ordinal, ref in enumerate(item["basis_refs"]):
                    parent_refs.append(
                        (
                            scenario_ref,
                            "P-D10",
                            str(row["row_key"]),
                            "READINESS_BASIS",
                            ordinal,
                            str(ref),
                        )
                    )
                for ordinal, code in enumerate(item["limitation_codes"]):
                    rows["P-D20"].append(
                        _row(
                            "P-D20",
                            (scenario_ref, readiness_ref, ordinal),
                            scenario_ref=scenario_ref,
                            readiness_ref=readiness_ref,
                            limitation_ordinal=ordinal,
                            limitation_code=code,
                        )
                    )
        elif query_id == "O-Q09":
            decision_ref = str(data["decision_ref"])
            rows["P-D11"].append(
                _row(
                    "P-D11",
                    (scenario_ref, decision_ref),
                    scenario_ref=scenario_ref,
                    **{
                        key: value
                        for key, value in data.items()
                        if key != "frozen_input_refs"
                    },
                )
            )
            for ordinal, ref in enumerate(data["frozen_input_refs"]):
                rows["P-D12"].append(
                    _row(
                        "P-D12",
                        (scenario_ref, decision_ref, ordinal),
                        scenario_ref=scenario_ref,
                        decision_ref=decision_ref,
                        planning_input_ref=data["planning_input_ref"],
                        input_ordinal=ordinal,
                        input_ref=ref,
                    )
                )
        elif query_id == "O-Q10":
            request = result.request.model_dump(mode="json")
            reporting_ref = request["reporting_version_ref"]
            statement_field = request["statement_field"]
            for item in data["nodes"]:
                rows["P-D16"].append(
                    _row(
                        "P-D16",
                        (scenario_ref, reporting_ref, statement_field, item["node_ref"]),
                        scenario_ref=scenario_ref,
                        reporting_version_ref=reporting_ref,
                        statement_field=statement_field,
                        **item,
                    )
                )
            for item in data["edges"]:
                rows["P-D17"].append(
                    _row(
                        "P-D17",
                        (
                            scenario_ref,
                            reporting_ref,
                            statement_field,
                            item["source_ref"],
                            item["target_ref"],
                            item["relationship"],
                        ),
                        scenario_ref=scenario_ref,
                        reporting_version_ref=reporting_ref,
                        statement_field=statement_field,
                        **item,
                    )
                )
        elif query_id == "O-Q11":
            verification_ref = str(data["verification_ref"])
            correction = _row(
                "P-D13",
                (scenario_ref, verification_ref),
                scenario_ref=scenario_ref,
                **{
                    key: value
                    for key, value in data.items()
                    if key != "journal_balance_results"
                },
            )
            rows["P-D13"].append(correction)
            roles = {
                str(data["reversal_journal_ref"]): "REVERSAL",
                str(data["replacement_journal_ref"]): "REPLACEMENT",
            }
            for item in data["journal_balance_results"]:
                journal_ref = str(item["journal_ref"])
                rows["P-D14"].append(
                    _row(
                        "P-D14",
                        (correction["row_key"], roles[journal_ref]),
                        scenario_ref=scenario_ref,
                        correction_row_key=correction["row_key"],
                        journal_role=roles[journal_ref],
                        **item,
                    )
                )

    for scenario_ref, dataset_id, parent_key, role, ordinal, ref in parent_refs:
        rows["P-D15"].append(
            _row(
                "P-D15",
                (dataset_id, parent_key, role, ordinal),
                scenario_ref=scenario_ref,
                parent_dataset_id=dataset_id,
                parent_row_key=parent_key,
                reference_role=role,
                reference_ordinal=ordinal,
                reference_ref=ref,
            )
        )

    p_request = {
        "discovery_descriptor_ref": discovery.discovery_descriptor_ref,
        "semantic_as_of": str(discovery.semantic_as_of),
        "workspace_ref": discovery.workspace_ref,
    }
    p_hash = canonical_sha256(p_request)
    p_instance = query_instance_ref(p_request)
    rows["P-D18"].append(
        _row(
            "P-D18",
            (p_instance,),
            query_instance_ref=p_instance,
            query_id="P-Q00",
            view_id="P-V00",
            view_contract_version=1,
            scope_type="WORKSPACE",
            scope_ref=discovery.workspace_ref,
            query_revision=discovery.query_revision,
            semantic_as_of=str(discovery.semantic_as_of),
            compatibility_mode=discovery.compatibility_mode,
            canonical_request_hash=p_hash,
        )
    )
    for result in executed:
        rows["P-D18"].append(
            _row(
                "P-D18",
                (result.query_instance_ref,),
                query_instance_ref=result.query_instance_ref,
                query_id=result.request.query_id,
                view_id=result.envelope.view_contract,
                view_contract_version=result.envelope.view_contract_version,
                scope_type="SCENARIO",
                scope_ref=str(result.request.scenario_ref),
                query_revision=result.envelope.query_revision,
                semantic_as_of=str(result.envelope.semantic_as_of_time),
                compatibility_mode=result.envelope.compatibility_read_mode,
                canonical_request_hash=result.canonical_request_hash,
            )
        )
        for ordinal, source_ref in enumerate(result.envelope.source_refs):
            rows["P-D19"].append(
                _row(
                    "P-D19",
                    (result.query_instance_ref, ordinal),
                    query_instance_ref=result.query_instance_ref,
                    semantic_source_ordinal=ordinal,
                    semantic_source_ref=source_ref,
                )
            )

    actual_entries = {
        (
            item["journey_id"],
            item["semantic_role"],
            item["exact_ref"],
            item["source_kind"],
            item["availability"],
        )
        for item in manifest_data["scenario_entry_points"]
    }
    expected_entries = {
        (
            item.journey_id,
            item.semantic_role,
            item.exact_ref,
            item.source_kind,
            item.availability,
        )
        for item in discovery.entry_points
    }
    if actual_entries != expected_entries:
        raise ValueError("P-Q00 and O-V01 entry points do not match exactly")
    for item in discovery.entry_points:
        rows["P-D21"].append(
            _row(
                "P-D21",
                (item.scenario_ref, item.journey_id),
                scenario_ref=item.scenario_ref,
                journey_id=item.journey_id,
                semantic_role=item.semantic_role,
                exact_ref=item.exact_ref,
                source_kind=item.source_kind,
                availability=item.availability,
            )
        )
    return rows
