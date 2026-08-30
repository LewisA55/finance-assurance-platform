from __future__ import annotations

from pytest import raises

from finance_assurance.finance_data.fixed_assets import (
    AtlasFixedAssetPostingRules,
    FixedAsset,
    FixedAssetPostingInput,
    HermesFixedAssetAdmissionService,
    SourceAdmissionCandidate,
)


def _asset() -> FixedAsset:
    return FixedAsset(
        asset_id="FA-TEST-001",
        legal_entity_id="NEXUS-UK",
        asset_class="COMPUTER_EQUIPMENT",
        source_system="FIXED_ASSET_SUBLEDGER",
        source_record_ref="FA-MASTER-TEST-001",
        acquisition_business_event_ref="BE-TEST-001",
        capital_purchase_order_id="CPO-TEST-001",
        capital_goods_receipt_id="CGR-TEST-001",
        capital_invoice_id="CINV-TEST-001",
        acquisition_date="2026-01-12",
        in_service_date="2026-01-10",
        cost_minor=12_000_000,
        residual_value_minor=0,
        currency="GBP",
        useful_life_months=48,
        depreciation_method="STRAIGHT_LINE_MONTHLY",
        disposal_date="",
        asset_status="ACTIVE",
    )


def test_atlas_fixed_asset_rules_derive_balanced_postings() -> None:
    asset = _asset()
    rules = AtlasFixedAssetPostingRules()

    acquisition = rules.derive(
        FixedAssetPostingInput(
            origin_class="BUSINESS_EVENT",
            event_type="CAPITAL_ASSET_INVOICE_APPROVED",
            asset=asset,
            event_amount_minor=asset.cost_minor,
        )
    )
    depreciation = rules.derive(
        FixedAssetPostingInput(
            origin_class="BUSINESS_EVENT",
            event_type="FIXED_ASSET_DEPRECIATION_DUE",
            asset=asset,
            event_amount_minor=250_000,
        )
    )

    assert acquisition.lines == (
        ("1500", 12_000_000, 0),
        ("2000", 0, 12_000_000),
    )
    assert depreciation.lines == (
        ("6300", 250_000, 0),
        ("1510", 0, 250_000),
    )
    assert sum(line[1] for line in acquisition.lines) == sum(
        line[2] for line in acquisition.lines
    )


def test_atlas_fixed_asset_rules_reject_accounting_event_input() -> None:
    with raises(ValueError, match="only BUSINESS_EVENT"):
        AtlasFixedAssetPostingRules().derive(
            FixedAssetPostingInput(
                origin_class="ACCOUNTING_EVENT",
                event_type="FIXED_ASSET_DEPRECIATION_DUE",
                asset=_asset(),
                event_amount_minor=250_000,
            )
        )


def test_hermes_quarantines_duplicate_without_admitting_event() -> None:
    result = HermesFixedAssetAdmissionService().admit(
        SourceAdmissionCandidate(
            source_dataset_path="procurement/capital_invoices.csv",
            source_system="ACCOUNTS_PAYABLE",
            source_record_ref="CINV-DUPLICATE#APPROVAL",
            source_payload={
                "capital_invoice_id": "CINV-DUPLICATE",
                "invoice_amount_minor": 12_000_000,
                "currency": "GBP",
            },
            candidate_business_event_ref="BE-CANDIDATE-DUPLICATE",
            event_time="2026-01-12T12:00:00Z",
            ingested_at="2026-08-24T21:00:00Z",
            legal_entity_id="NEXUS-UK",
            currency="GBP",
            duplicate_of_ref="CINV-ORIGINAL",
        )
    )

    assert result.admission_decision == "QUARANTINED"
    assert result.candidate_business_event_ref == ""
    assert result.quarantine_ref.startswith("QUAR-")
