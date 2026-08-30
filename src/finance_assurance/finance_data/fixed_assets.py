"""Hermes admission and Atlas posting rules for the fixed-asset vertical."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from finance_assurance.exports.serialization import canonical_json_bytes, sha256_bytes

AssetEventType = Literal[
    "CAPITAL_ASSET_INVOICE_APPROVED",
    "CAPITAL_ASSET_INVOICE_PAID",
    "FIXED_ASSET_DEPRECIATION_DUE",
    "FIXED_ASSET_AMORTISATION_DUE",
    "FIXED_ASSET_IMPAIRMENT_APPROVED",
    "FIXED_ASSET_DISPOSED",
]


@dataclass(frozen=True, slots=True)
class FixedAsset:
    """One admitted fixed-asset source master used by Atlas projections."""

    asset_id: str
    legal_entity_id: str
    asset_class: str
    source_system: str
    source_record_ref: str
    acquisition_business_event_ref: str
    capital_purchase_order_id: str
    capital_goods_receipt_id: str
    capital_invoice_id: str
    acquisition_date: str
    in_service_date: str
    cost_minor: int
    residual_value_minor: int
    currency: str
    useful_life_months: int
    depreciation_method: str
    disposal_date: str
    asset_status: str

    @property
    def asset_account_id(self) -> str:
        if self.asset_class == "GOODWILL":
            return "1600"
        if self.asset_class == "CAPITALISED_SOFTWARE":
            return "1700"
        return "1500"

    @property
    def accumulated_account_id(self) -> str:
        if self.asset_class == "GOODWILL":
            return "1610"
        if self.asset_class == "CAPITALISED_SOFTWARE":
            return "1710"
        return "1510"


@dataclass(frozen=True, slots=True)
class SourceAdmissionCandidate:
    """One source-domain candidate presented to Hermes admission."""

    source_dataset_path: str
    source_system: str
    source_record_ref: str
    source_payload: dict[str, object]
    candidate_business_event_ref: str
    event_time: str
    ingested_at: str
    legal_entity_id: str
    currency: str
    duplicate_of_ref: str = ""
    late_arrival: bool = False


@dataclass(frozen=True, slots=True)
class AdmissionResult:
    """Immutable Hermes decision over one exact source record."""

    admission_result_id: str
    source_dataset_path: str
    source_system: str
    source_record_ref: str
    source_record_hash: str
    candidate_business_event_ref: str
    admission_decision: str
    decision_reason: str
    event_time: str
    ingested_at: str
    legal_entity_id: str
    currency: str
    duplicate_of_ref: str
    quarantine_ref: str

    def as_row(self) -> dict[str, object]:
        return {
            "admission_result_id": self.admission_result_id,
            "source_dataset_path": self.source_dataset_path,
            "source_system": self.source_system,
            "source_record_ref": self.source_record_ref,
            "source_record_hash": self.source_record_hash,
            "candidate_business_event_ref": self.candidate_business_event_ref,
            "admission_decision": self.admission_decision,
            "decision_reason": self.decision_reason,
            "event_time": self.event_time,
            "ingested_at": self.ingested_at,
            "legal_entity_id": self.legal_entity_id,
            "currency": self.currency,
            "duplicate_of_ref": self.duplicate_of_ref,
            "quarantine_ref": self.quarantine_ref,
        }


class HermesSourceAdmissionService:
    """Admit, warn, or quarantine exact source-domain candidates."""

    def admit(self, candidate: SourceAdmissionCandidate) -> AdmissionResult:
        if not candidate.source_record_ref or not candidate.source_dataset_path:
            raise ValueError("source identity is required for Hermes admission")
        encoded_payload = {
            key: (
                "true"
                if value is True
                else "false"
                if value is False
                else str(value)
            )
            for key, value in candidate.source_payload.items()
        }
        source_hash = sha256_bytes(canonical_json_bytes(encoded_payload))
        identity_hash = sha256_bytes(
            canonical_json_bytes(
                {
                    "source_dataset_path": candidate.source_dataset_path,
                    "source_record_ref": candidate.source_record_ref,
                    "source_record_hash": source_hash,
                }
            )
        ).removeprefix("sha256:")[:20].upper()
        if candidate.duplicate_of_ref:
            decision = "QUARANTINED"
            reason = "DUPLICATE_SOURCE_IDENTITY"
            business_event_ref = ""
            quarantine_ref = f"QUAR-{identity_hash}"
        elif candidate.late_arrival:
            decision = "ADMITTED_WITH_WARNING"
            reason = "LATE_ARRIVAL"
            business_event_ref = candidate.candidate_business_event_ref
            quarantine_ref = ""
        else:
            decision = "ADMITTED"
            reason = "VALID_SOURCE_RECORD"
            business_event_ref = candidate.candidate_business_event_ref
            quarantine_ref = ""
        return AdmissionResult(
            admission_result_id=f"ADM-{identity_hash}",
            source_dataset_path=candidate.source_dataset_path,
            source_system=candidate.source_system,
            source_record_ref=candidate.source_record_ref,
            source_record_hash=source_hash,
            candidate_business_event_ref=business_event_ref,
            admission_decision=decision,
            decision_reason=reason,
            event_time=candidate.event_time,
            ingested_at=candidate.ingested_at,
            legal_entity_id=candidate.legal_entity_id,
            currency=candidate.currency,
            duplicate_of_ref=candidate.duplicate_of_ref,
            quarantine_ref=quarantine_ref,
        )


# Compatibility name retained for the independently verified A2.2a interface.
HermesFixedAssetAdmissionService = HermesSourceAdmissionService


@dataclass(frozen=True, slots=True)
class FixedAssetPostingInput:
    """Admitted business-event facts available to Atlas posting rules."""

    origin_class: str
    event_type: AssetEventType
    asset: FixedAsset
    event_amount_minor: int
    gross_cost_minor: int = 0
    accumulated_depreciation_minor: int = 0
    disposal_proceeds_minor: int = 0


@dataclass(frozen=True, slots=True)
class FixedAssetPosting:
    """One deterministic Atlas posting-rule output."""

    posting_rule_ref: str
    journal_amount_minor: int
    lines: tuple[tuple[str, int, int], ...]


class AtlasFixedAssetPostingRules:
    """Derive journal instructions only from admitted business events."""

    def derive(self, value: FixedAssetPostingInput) -> FixedAssetPosting:
        if value.origin_class != "BUSINESS_EVENT":
            raise ValueError("only BUSINESS_EVENT may enter fixed-asset posting")
        amount = value.event_amount_minor
        if amount < 0:
            raise ValueError("fixed-asset posting amount cannot be negative")
        if value.event_type == "CAPITAL_ASSET_INVOICE_APPROVED":
            return FixedAssetPosting(
                posting_rule_ref="PR-CAPITAL-ASSET-INVOICE@v1",
                journal_amount_minor=amount,
                lines=(
                    (value.asset.asset_account_id, amount, 0),
                    ("2000", 0, amount),
                ),
            )
        if value.event_type == "CAPITAL_ASSET_INVOICE_PAID":
            return FixedAssetPosting(
                posting_rule_ref="PR-CAPITAL-ASSET-PAYMENT@v1",
                journal_amount_minor=amount,
                lines=(("2000", amount, 0), ("1000", 0, amount)),
            )
        if value.event_type in {
            "FIXED_ASSET_DEPRECIATION_DUE",
            "FIXED_ASSET_AMORTISATION_DUE",
            "FIXED_ASSET_IMPAIRMENT_APPROVED",
        }:
            rule = {
                "FIXED_ASSET_DEPRECIATION_DUE": "PR-FIXED-ASSET-DEPRECIATION@v1",
                "FIXED_ASSET_AMORTISATION_DUE": "PR-INTANGIBLE-AMORTISATION@v1",
                "FIXED_ASSET_IMPAIRMENT_APPROVED": "PR-ASSET-IMPAIRMENT@v1",
            }[value.event_type]
            return FixedAssetPosting(
                posting_rule_ref=rule,
                journal_amount_minor=amount,
                lines=(
                    ("6300", amount, 0),
                    (value.asset.accumulated_account_id, 0, amount),
                ),
            )
        if value.event_type == "FIXED_ASSET_DISPOSED":
            gross = value.gross_cost_minor
            accumulated = value.accumulated_depreciation_minor
            proceeds = value.disposal_proceeds_minor
            gain_loss = gross - accumulated - proceeds
            if gross <= 0 or accumulated < 0 or proceeds < 0:
                raise ValueError("fixed-asset disposal facts are invalid")
            debit_lines = [
                (value.asset.accumulated_account_id, accumulated, 0),
                ("1000", proceeds, 0),
            ]
            if gain_loss >= 0:
                debit_lines.append(("6300", gain_loss, 0))
            else:
                debit_lines.append(("6300", 0, -gain_loss))
            return FixedAssetPosting(
                posting_rule_ref="PR-FIXED-ASSET-DISPOSAL@v1",
                journal_amount_minor=gross,
                lines=(*debit_lines, (value.asset.asset_account_id, 0, gross)),
            )
        raise ValueError(f"unsupported fixed-asset event: {value.event_type}")
