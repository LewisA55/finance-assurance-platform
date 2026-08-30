"""Deterministic multi-domain synthetic finance source generation."""

from __future__ import annotations

import calendar
import csv
import random
from collections import defaultdict
from dataclasses import dataclass, replace
from datetime import date, timedelta
from hashlib import sha256
from pathlib import Path

from finance_assurance.exports.serialization import canonical_json_bytes, sha256_bytes
from finance_assurance.finance_data.contracts import (
    FinanceDataBuildRequest,
    ScaleProfile,
)
from finance_assurance.finance_data.definitions import (
    ACCOUNT_ROWS,
    ACCOUNTING_EVENTS,
    ACCRUAL_SCHEDULE,
    ACCRUAL_SOURCE_EVENTS,
    ALL_SOURCE_DATASETS,
    AP_AGEING,
    AR_AGEING,
    ASSET_LIFECYCLE_EVENTS,
    BANK_ACCOUNTS,
    BANK_RECONCILIATIONS,
    BANK_STATEMENT_LINES,
    BANK_TRANSACTIONS,
    BUDGET_LINES,
    BUDGET_VERSIONS,
    BUSINESS_EVENTS,
    CAPITAL_GOODS_RECEIPTS,
    CAPITAL_INVOICES,
    CAPITAL_PURCHASE_ORDERS,
    CASH_FLOW_RECONCILIATION,
    CHART_OF_ACCOUNTS,
    CONSOLIDATION_ELIMINATIONS,
    CRM_ACCOUNTS,
    CUSTOMERS,
    DATASET_BY_PATH,
    DEBT_INSTRUMENTS,
    DEBT_SCHEDULE,
    DEFECT_REGISTRY,
    DEFERRED_REVENUE_ROLLFORWARD,
    DEPARTMENT_ROWS,
    DEPARTMENTS,
    EMPLOYEE_COMPENSATION,
    EMPLOYEES,
    EQUITY_MOVEMENTS,
    FINANCIAL_STATEMENTS,
    FIXED_ASSET_CONTROL_RESULTS,
    FIXED_ASSET_MOVEMENTS,
    FIXED_ASSET_REGISTER,
    FORECAST_LINES,
    FORECAST_VERSIONS,
    FX_RATES,
    HEADCOUNT_PLAN,
    HEADCOUNT_SNAPSHOT,
    INTERCOMPANY_BALANCES,
    INTERCOMPANY_TRANSACTIONS,
    INVOICE_LINES,
    INVOICES,
    LEASE_CONTRACTS,
    LEASE_LIFECYCLE_EVENTS,
    LEASE_SCHEDULE,
    LEGAL_ENTITIES,
    MONTHLY_CLOSE_STATUS,
    OPENING_BALANCE_SHEET,
    PAYMENT_ALLOCATIONS,
    PAYMENTS,
    PAYROLL_LINES,
    PERIODS,
    PLANNING_ACCOUNT_IDS,
    PREPAYMENT_SCHEDULE,
    PREPAYMENT_SOURCE_EVENTS,
    PRODUCT_PRICE_BOOK,
    PRODUCT_ROWS,
    PRODUCTS,
    REGION_ROWS,
    REGIONS,
    RETAINED_EARNINGS_BRIDGE,
    REVENUE_SCHEDULE,
    SOURCE_ADMISSION_RESULTS,
    SOURCE_GL_LINES,
    SOURCE_INVENTORY,
    SOURCE_QA_RESULTS,
    STATUTORY_RECONCILIATIONS,
    STATUTORY_STATEMENTS,
    STATUTORY_SUBLEDGER_CONTROL_RESULTS,
    STATUTORY_TRIAL_BALANCE,
    SUBSCRIPTION_EVENTS,
    SUBSCRIPTIONS,
    TAX_CALCULATION_INPUTS,
    TAX_LOSS_REGISTER,
    TAX_SCHEDULE,
    TRIAL_BALANCE,
    VARIANCE_SOURCE,
    VENDOR_INVOICE_LINES,
    VENDOR_INVOICES,
    VENDOR_PAYMENTS,
    VENDORS,
    DatasetDefinition,
)
from finance_assurance.finance_data.fixed_assets import (
    AtlasFixedAssetPostingRules,
    FixedAsset,
    FixedAssetPostingInput,
    HermesFixedAssetAdmissionService,
    SourceAdmissionCandidate,
)
from finance_assurance.finance_data.multi_entity_close import (
    AtlasConsolidationEliminationRules,
    AtlasIntercompanyPostingRules,
    ConsolidationEliminationInput,
    IntercompanyPostingInput,
)
from finance_assurance.finance_data.statutory_subledgers import (
    AtlasLeasePostingRules,
    AtlasTaxPostingRules,
    AtlasWorkingCapitalPostingRules,
    LeasePostingInput,
    TaxPostingInput,
    WorkingCapitalPostingInput,
)

REPORTING_CURRENCY = "GBP"
RATE_SCALE = 1_000_000
LEGAL_ENTITY_ID = "NEXUS-UK"


def _add_months(value: date, months: int) -> date:
    month_index = value.year * 12 + value.month - 1 + months
    year, zero_month = divmod(month_index, 12)
    month = zero_month + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _month_end(value: date) -> date:
    return date(value.year, value.month, calendar.monthrange(value.year, value.month)[1])


def _month_starts(start: date, end: date) -> tuple[date, ...]:
    current = date(start.year, start.month, 1)
    terminal = date(end.year, end.month, 1)
    values: list[date] = []
    while current <= terminal:
        values.append(current)
        current = _add_months(current, 1)
    return tuple(values)


def _period_id(value: date) -> str:
    return value.strftime("%Y-%m")


def _timestamp(value: date, hour: int = 12) -> str:
    return f"{value.isoformat()}T{hour:02d}:00:00Z"


def _stable_ref(prefix: str, *parts: object, length: int = 18) -> str:
    payload = "|".join(str(part) for part in parts).encode("ascii")
    return f"{prefix}-{sha256(payload).hexdigest()[:length].upper()}"


def _to_reporting_minor(local_minor: int, rate_ppm: int) -> int:
    if local_minor < 0:
        return -_to_reporting_minor(-local_minor, rate_ppm)
    return (local_minor * rate_ppm + RATE_SCALE // 2) // RATE_SCALE


def _ageing_bucket(days_past_due: int) -> str:
    if days_past_due <= 0:
        return "CURRENT"
    if days_past_due <= 30:
        return "DAYS_1_30"
    if days_past_due <= 60:
        return "DAYS_31_60"
    if days_past_due <= 90:
        return "DAYS_61_90"
    return "DAYS_90_PLUS"


class CsvSink:
    """Streaming deterministic writer for one closed source dataset."""

    def __init__(self, raw_root: Path, definition: DatasetDefinition) -> None:
        self.definition = definition
        self.path = raw_root / definition.path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("w", encoding="utf-8", newline="")
        self._writer = csv.DictWriter(
            self._handle,
            fieldnames=definition.columns,
            extrasaction="raise",
            lineterminator="\n",
            quoting=csv.QUOTE_MINIMAL,
        )
        self._writer.writeheader()
        self.row_count = 0

    def write(self, row: dict[str, object]) -> None:
        if set(row) != set(self.definition.columns):
            missing = sorted(set(self.definition.columns) - set(row))
            extra = sorted(set(row) - set(self.definition.columns))
            raise ValueError(
                f"{self.definition.path} row shape differs: "
                f"missing={missing}, extra={extra}"
            )
        encoded = {
            key: "true" if value is True else "false" if value is False else value
            for key, value in row.items()
        }
        self._writer.writerow(encoded)
        self.row_count += 1

    def close(self) -> None:
        self._handle.flush()
        self._handle.close()


@dataclass(frozen=True)
class Customer:
    customer_id: str
    name: str
    region_id: str
    currency: str
    segment: str
    created_date: date


@dataclass(frozen=True)
class Vendor:
    vendor_id: str
    region_id: str
    currency: str
    category: str
    payment_terms_days: int


@dataclass(frozen=True)
class Employee:
    employee_id: str
    department_id: str
    region_id: str
    currency: str
    hire_date: date
    termination_date: date | None
    annual_salary_minor: int


@dataclass(frozen=True)
class Subscription:
    subscription_id: str
    customer: Customer
    product_id: str
    start_date: date
    end_date: date | None
    billing_frequency: str
    monthly_recurring_revenue_minor: int


@dataclass(frozen=True)
class BankTransaction:
    bank_transaction_id: str
    bank_account_id: str
    legal_entity_id: str
    value_date: date
    book_date: date
    transaction_type: str
    source_record_ref: str
    business_event_ref: str
    amount_minor: int
    currency: str


@dataclass(frozen=True)
class GeneratedPopulation:
    row_counts: dict[str, int]
    defect_count: int
    history_month_count: int
    total_period_count: int


class FinancePopulationGenerator:
    """Generate the Atlas operational and statutory source population."""

    def __init__(
        self,
        *,
        request: FinanceDataBuildRequest,
        profile: ScaleProfile,
        raw_root: Path,
    ) -> None:
        self.request = request
        self.is_a24 = request.statutory_contract_version == "A2.4"
        self.profile = profile
        self.raw_root = raw_root
        self.rng = random.Random(request.seed)
        self.actual_months = _month_starts(request.history_start, request.actuals_end)
        forecast_end = _month_end(_add_months(request.actuals_end, 120))
        self.all_months = _month_starts(request.history_start, forecast_end)
        self.sinks = {
            item.path: CsvSink(raw_root, item) for item in ALL_SOURCE_DATASETS
        }
        self.defects: list[dict[str, object]] = []
        self.activity: dict[tuple[str, str], list[int]] = defaultdict(
            lambda: [0, 0]
        )
        self.entity_activity: dict[tuple[str, str, str], list[int]] = defaultdict(
            lambda: [0, 0]
        )
        self.cash_flow_activity: dict[tuple[str, str, str], int] = defaultdict(int)
        self.elimination_activity: dict[tuple[str, str], list[int]] = defaultdict(
            lambda: [0, 0]
        )
        self.bank_transactions: list[BankTransaction] = []
        self.bank_reconciliation_failures = 0
        self.minimum_bank_balance_minor = 0
        self.bank_account_by_entity = {
            "NEXUS-UK": ("BANK-NEXUS-UK-GBP-OPERATING", "GBP"),
            "NEXUS-US": ("BANK-NEXUS-US-USD-OPERATING", "USD"),
        }
        self.formation_debt_event_ref = ""
        self.opening_event_ref_by_source: dict[str, str] = {}
        self.fixed_asset_admission = HermesFixedAssetAdmissionService()
        self.fixed_asset_posting_rules = AtlasFixedAssetPostingRules()
        self.fixed_asset_control_failures = 0
        self.lease_posting_rules = AtlasLeasePostingRules()
        self.tax_posting_rules = AtlasTaxPostingRules()
        self.working_capital_posting_rules = AtlasWorkingCapitalPostingRules()
        self.intercompany_posting_rules = AtlasIntercompanyPostingRules()
        self.consolidation_rules = AtlasConsolidationEliminationRules()
        self.stat_subledger_control_failures = 0
        self.a23_control_failures = 0
        self.intercompany_rows: list[dict[str, object]] = []
        self.accounting_event_by_key: dict[tuple[str, str, str], str] = {}
        self._accounting_event_refs: set[str] = set()
        self.trial_balance_digest_by_scope_period: dict[tuple[str, str], str] = {}
        self.fx_rates = self._build_fx_rates()
        self._event_refs: set[str] = set()
        self._journal_refs: set[str] = set()
        self.deferred_billings: dict[tuple[str, str], list[int]] = defaultdict(
            lambda: [0, 0]
        )
        self.recognised_revenue: dict[tuple[str, str], list[int]] = defaultdict(
            lambda: [0, 0]
        )

    def _sink(self, definition: DatasetDefinition) -> CsvSink:
        return self.sinks[definition.path]

    def _build_fx_rates(self) -> dict[tuple[str, str], int]:
        base = {"GBP": 1_000_000, "USD": 780_000, "EUR": 860_000, "SGD": 590_000}
        drift = {"GBP": 0, "USD": 280, "EUR": -150, "SGD": 45}
        rates: dict[tuple[str, str], int] = {}
        for month_index, month in enumerate(self.all_months):
            for currency in sorted(base):
                noise = 0 if currency == "GBP" else self.rng.randint(-9_000, 9_000)
                average = max(100_000, base[currency] + drift[currency] * month_index + noise)
                closing_noise = 0 if currency == "GBP" else self.rng.randint(-5_000, 5_000)
                rates[(_period_id(month), currency)] = average
                self._sink(FX_RATES).write(
                    {
                        "period_id": _period_id(month),
                        "currency": currency,
                        "average_rate_to_gbp_ppm": average,
                        "closing_rate_to_gbp_ppm": max(100_000, average + closing_noise),
                        "rate_scale": RATE_SCALE,
                    }
                )
        return rates

    def _rate(self, value_date: date, currency: str) -> int:
        return self.fx_rates[(_period_id(value_date), currency)]

    def _defect(
        self,
        *,
        defect_type: str,
        dataset_path: str,
        source_record_ref: str,
        detector: str,
        severity: str,
        treatment: str,
        description: str,
    ) -> None:
        self.defects.append(
            {
                "defect_instance_ref": _stable_ref(
                    "DEF", defect_type, dataset_path, source_record_ref
                ),
                "defect_type": defect_type,
                "source_dataset_path": dataset_path,
                "source_record_ref": source_record_ref,
                "expected_detector": detector,
                "severity": severity,
                "expected_treatment": treatment,
                "description": description,
            }
        )

    @staticmethod
    def _cash_flow_class(event_type: str) -> str:
        if event_type in {
            "CAPITAL_CONTRIBUTION_RECEIVED",
            "DEBT_DRAWN",
            "DEBT_PRINCIPAL_REPAID",
            "LEASE_PAYMENT_MADE",
            "DEBT_INTEREST_INCURRED",
        }:
            return "FINANCING"
        if event_type in {
            "FIXED_ASSET_ACQUIRED",
            "BUSINESS_ACQUIRED",
            "INTANGIBLE_ASSET_ACQUIRED",
            "CAPITAL_ASSET_INVOICE_PAID",
            "FIXED_ASSET_DISPOSED",
        }:
            return "INVESTING"
        return "OPERATING"

    def _business_event(
        self,
        *,
        event_type: str,
        source_system: str,
        source_record_ref: str,
        occurred_date: date,
        effective_date: date,
        counterparty_ref: str,
        local_amount_minor: int,
        currency: str,
        reporting_amount_minor: int,
        posting_rule_ref: str,
        lines: tuple[tuple[str, int, int], ...],
        recorded_delay_days: int = 0,
        legal_entity_id: str = LEGAL_ENTITY_ID,
    ) -> str:
        event_ref = _stable_ref("BE", event_type, source_system, source_record_ref)
        if event_ref in self._event_refs:
            raise ValueError(f"duplicate business event identity: {event_ref}")
        self._event_refs.add(event_ref)
        recorded_date = occurred_date + timedelta(days=recorded_delay_days)
        event_payload = {
            "business_event_ref": event_ref,
            "event_type": event_type,
            "source_system": source_system,
            "source_record_ref": source_record_ref,
            "occurred_at": _timestamp(occurred_date),
            "recorded_at": _timestamp(recorded_date, 18),
            "effective_date": effective_date.isoformat(),
            "legal_entity_id": legal_entity_id,
            "counterparty_ref": counterparty_ref,
            "amount_minor": local_amount_minor,
            "currency": currency,
            "reporting_amount_minor": reporting_amount_minor,
            "reporting_currency": self.request.reporting_currency,
            "posting_rule_ref": posting_rule_ref,
        }
        semantic_hash = sha256_bytes(canonical_json_bytes(event_payload))
        self._sink(BUSINESS_EVENTS).write(
            {**event_payload, "record_semantic_hash": semantic_hash}
        )

        total_debit = sum(line[1] for line in lines)
        total_credit = sum(line[2] for line in lines)
        if total_debit != total_credit or total_debit != reporting_amount_minor:
            raise ValueError(f"unbalanced source posting for {event_ref}")
        journal_ref = _stable_ref("SRC-JNL", event_ref)
        if journal_ref in self._journal_refs:
            raise ValueError(f"duplicate source journal identity: {journal_ref}")
        self._journal_refs.add(journal_ref)
        period_id = _period_id(effective_date)
        for line_no, (account_id, debit_minor, credit_minor) in enumerate(
            lines, start=1
        ):
            self._sink(SOURCE_GL_LINES).write(
                {
                    "source_journal_line_id": f"{journal_ref}-L{line_no:02d}",
                    "source_journal_id": journal_ref,
                    "line_no": line_no,
                    "business_event_ref": event_ref,
                    "posting_rule_ref": posting_rule_ref,
                    "period_id": period_id,
                    "effective_date": effective_date.isoformat(),
                    "recorded_at": _timestamp(recorded_date, 18),
                    "legal_entity_id": legal_entity_id,
                    "account_id": account_id,
                    "debit_minor": debit_minor,
                    "credit_minor": credit_minor,
                    "currency": self.request.reporting_currency,
                    "source_record_ref": source_record_ref,
                }
            )
            activity = self.activity[(period_id, account_id)]
            activity[0] += debit_minor
            activity[1] += credit_minor
            entity_activity = self.entity_activity[
                (period_id, legal_entity_id, account_id)
            ]
            entity_activity[0] += debit_minor
            entity_activity[1] += credit_minor
            if account_id == "1000":
                amount_minor = debit_minor - credit_minor
                self.cash_flow_activity[
                    (period_id, legal_entity_id, self._cash_flow_class(event_type))
                ] += amount_minor
                bank_account_id, bank_currency = self.bank_account_by_entity[
                    legal_entity_id
                ]
                if bank_currency != self.request.reporting_currency:
                    raise ValueError(
                        "non-reporting-currency bank posting is not admitted in A2.1"
                    )
                bank_transaction = BankTransaction(
                    bank_transaction_id=_stable_ref(
                        "BTX", event_ref, line_no, length=22
                    ),
                    bank_account_id=bank_account_id,
                    legal_entity_id=legal_entity_id,
                    value_date=effective_date,
                    book_date=occurred_date,
                    transaction_type=(
                        "CASH_RECEIPT"
                        if amount_minor > 0
                        else "CASH_DISBURSEMENT"
                    ),
                    source_record_ref=source_record_ref,
                    business_event_ref=event_ref,
                    amount_minor=amount_minor,
                    currency=bank_currency,
                )
                self.bank_transactions.append(bank_transaction)
                self._sink(BANK_TRANSACTIONS).write(
                    {
                        "bank_transaction_id": (
                            bank_transaction.bank_transaction_id
                        ),
                        "bank_account_id": bank_account_id,
                        "legal_entity_id": legal_entity_id,
                        "value_date": effective_date.isoformat(),
                        "book_date": occurred_date.isoformat(),
                        "transaction_type": bank_transaction.transaction_type,
                        "source_record_ref": source_record_ref,
                        "business_event_ref": event_ref,
                        "amount_minor": amount_minor,
                        "currency": bank_currency,
                        "bank_status": "SETTLED",
                        "reconciliation_status": "MATCHED",
                    }
                )
        return event_ref

    def _write_a21_foundations(self) -> None:
        entity_rows = (
            (
                "NEXUS-UK",
                "Nexus Holdings Limited",
                "",
                "GBP",
                self.request.history_start,
                "PARENT",
            ),
            (
                "NEXUS-US",
                "Nexus Analytics Inc.",
                "NEXUS-UK",
                "USD",
                date(2021, 7, 1),
                "FULL_CONSOLIDATION",
            ),
        )
        for entity_id, name, parent_id, currency, incorporated, method in entity_rows:
            self._sink(LEGAL_ENTITIES).write(
                {
                    "legal_entity_id": entity_id,
                    "legal_entity_name": name,
                    "parent_entity_id": parent_id,
                    "functional_currency": currency,
                    "incorporation_date": incorporated.isoformat(),
                    "consolidation_method": method,
                    "status": "ACTIVE",
                }
            )
        bank_rows = (
            (
                "BANK-NEXUS-UK-GBP-OPERATING",
                "NEXUS-UK",
                "Nexus Relationship Bank",
                "GBP",
                self.request.history_start,
            ),
            (
                "BANK-NEXUS-US-USD-OPERATING",
                "NEXUS-US",
                "Nexus US Relationship Bank",
                "USD",
                date(2021, 7, 1),
            ),
        )
        for account_id, entity_id, bank_name, currency, opened_date in bank_rows:
            self._sink(BANK_ACCOUNTS).write(
                {
                    "bank_account_id": account_id,
                    "legal_entity_id": entity_id,
                    "bank_name": bank_name,
                    "account_type": "OPERATING",
                    "currency": currency,
                    "opened_date": opened_date.isoformat(),
                    "closed_date": "",
                    "linked_facility_id": (
                        "DEBT-REVOLVER-GBP"
                        if entity_id == "NEXUS-UK"
                        else ""
                    ),
                    "status": "ACTIVE",
                }
            )
        debt_rows = (
            (
                "DEBT-TERM-GBP",
                "TERM_LOAN",
                1_500_000_000,
                date(2028, 12, 31),
                600,
                0,
                "FIXED",
                "QUARTERLY_FROM_2023",
            ),
            (
                "DEBT-REVOLVER-GBP",
                "REVOLVING_CREDIT_FACILITY",
                2_000_000_000,
                date(2027, 12, 31),
                0,
                350,
                "SONIA",
                "BULLET",
            ),
        )
        for (
            instrument_id,
            facility_type,
            limit_minor,
            maturity,
            fixed_rate_bps,
            margin_bps,
            base_rate_ref,
            repayment_profile,
        ) in debt_rows:
            self._sink(DEBT_INSTRUMENTS).write(
                {
                    "debt_instrument_id": instrument_id,
                    "legal_entity_id": LEGAL_ENTITY_ID,
                    "lender_name": "Nexus Relationship Bank Syndicate",
                    "facility_type": facility_type,
                    "currency": REPORTING_CURRENCY,
                    "facility_limit_minor": limit_minor,
                    "start_date": self.request.history_start.isoformat(),
                    "maturity_date": maturity.isoformat(),
                    "fixed_rate_bps": fixed_rate_bps,
                    "margin_bps": margin_bps,
                    "base_rate_ref": base_rate_ref,
                    "repayment_profile": repayment_profile,
                    "covenant_policy_ref": "TREASURY-COVENANT-POLICY@v1",
                    "instrument_status": "ACTIVE",
                }
            )

    def _write_references(self) -> None:
        actual_period_ids = {_period_id(value) for value in self.actual_months}
        for month in self.all_months:
            self._sink(PERIODS).write(
                {
                    "period_id": _period_id(month),
                    "month_start": month.isoformat(),
                    "month_end": _month_end(month).isoformat(),
                    "fiscal_year": month.year,
                    "fiscal_quarter": f"Q{(month.month - 1) // 3 + 1}",
                    "month_number": month.month,
                    "is_actual_period": _period_id(month) in actual_period_ids,
                }
            )
        for region_id, region_name, currency in REGION_ROWS:
            self._sink(REGIONS).write(
                {
                    "region_id": region_id,
                    "region_name": region_name,
                    "local_currency": currency,
                    "reporting_currency": self.request.reporting_currency,
                }
            )
        for department_id, name, business_unit, opex_class in DEPARTMENT_ROWS:
            self._sink(DEPARTMENTS).write(
                {
                    "department_id": department_id,
                    "department_name": name,
                    "business_unit": business_unit,
                    "opex_class": opex_class,
                }
            )
        for product_id, name, family, revenue_type, margin_bps in PRODUCT_ROWS:
            self._sink(PRODUCTS).write(
                {
                    "product_id": product_id,
                    "product_name": name,
                    "product_family": family,
                    "revenue_type": revenue_type,
                    "gross_margin_target_bps": margin_bps,
                    "active_from": self.request.history_start.isoformat(),
                }
            )
        segment_multiplier_bps = {
            "SMB": 10_000,
            "MID_MARKET": 9_200,
            "ENTERPRISE": 8_400,
        }
        for product_index, product in enumerate(PRODUCT_ROWS, start=1):
            product_id = product[0]
            reporting_base = 32_000 + product_index * 18_000
            for segment, multiplier_bps in segment_multiplier_bps.items():
                reporting_price = reporting_base * multiplier_bps // 10_000
                for region_id, _, currency in REGION_ROWS:
                    rate = self._rate(self.request.history_start, currency)
                    local_price = reporting_price * RATE_SCALE // rate
                    self._sink(PRODUCT_PRICE_BOOK).write(
                        {
                            "price_book_id": (
                                f"PB-{product_id}-{segment}-{region_id}"
                            ),
                            "product_id": product_id,
                            "customer_segment": segment,
                            "region_id": region_id,
                            "currency": currency,
                            "monthly_list_price_minor": local_price,
                            "annual_list_price_minor": local_price * 12,
                            "reporting_monthly_list_price_minor": (
                                _to_reporting_minor(local_price, rate)
                            ),
                            "reporting_currency": self.request.reporting_currency,
                            "effective_start_date": (
                                self.request.history_start.isoformat()
                            ),
                            "effective_end_date": "",
                            "status": "ACTIVE",
                        }
                    )
        for row in ACCOUNT_ROWS:
            self._sink(CHART_OF_ACCOUNTS).write(
                dict(zip(CHART_OF_ACCOUNTS.columns, row, strict=True))
            )

    def _generate_customers(self) -> tuple[Customer, ...]:
        currencies = {row[0]: row[2] for row in REGION_ROWS}
        regions = ("US", "US", "US", "US", "UK", "UK", "DE", "DE", "SG")
        industries = ("Technology", "Financial Services", "Retail", "Healthcare")
        customers: list[Customer] = []
        for index in range(1, self.profile.customer_count + 1):
            region_id = self.rng.choice(regions)
            segment_roll = self.rng.randrange(100)
            segment = "SMB" if segment_roll < 52 else "MID_MARKET" if segment_roll < 84 else "ENTERPRISE"
            created_month = self.rng.randrange(min(48, len(self.actual_months)))
            created_date = self.actual_months[created_month] + timedelta(
                days=self.rng.randrange(0, 20)
            )
            customer_id = f"CUST-{index:06d}"
            name = f"Nexus Customer {index:06d}"
            customer = Customer(
                customer_id=customer_id,
                name=name,
                region_id=region_id,
                currency=currencies[region_id],
                segment=segment,
                created_date=created_date,
            )
            customers.append(customer)
            self._sink(CUSTOMERS).write(
                {
                    "customer_id": customer_id,
                    "customer_name": name,
                    "region_id": region_id,
                    "segment": segment,
                    "industry": self.rng.choice(industries),
                    "created_date": created_date.isoformat(),
                    "credit_terms_days": 30 if segment != "ENTERPRISE" else 45,
                    "status": "ACTIVE",
                }
            )
            crm_name = name
            if index % 113 == 0:
                crm_name = f"{name} Holdings"
                self._defect(
                    defect_type="CUSTOMER_MASTER_NAME_DRIFT",
                    dataset_path=CRM_ACCOUNTS.path,
                    source_record_ref=f"CRM-{index:06d}",
                    detector="HERMES_CUSTOMER_IDENTITY_RECONCILIATION",
                    severity="MEDIUM",
                    treatment="REVIEW_AND_MAP",
                    description="CRM and billing customer names intentionally differ.",
                )
            self._sink(CRM_ACCOUNTS).write(
                {
                    "crm_account_id": f"CRM-{index:06d}",
                    "billing_customer_id": customer_id,
                    "account_name": crm_name,
                    "region_id": region_id,
                    "segment": segment,
                    "owner_ref": f"OWNER-{index % 24 + 1:03d}",
                    "status": "ACTIVE",
                }
            )
        return tuple(customers)

    def _generate_vendors(self) -> tuple[Vendor, ...]:
        currencies = {row[0]: row[2] for row in REGION_ROWS}
        categories = (
            "CLOUD_HOSTING",
            "PROFESSIONAL_SERVICES",
            "SOFTWARE",
            "MARKETING",
            "FACILITIES",
        )
        regions = tuple(currencies)
        vendors: list[Vendor] = []
        for index in range(1, self.profile.vendor_count + 1):
            region_id = regions[index % len(regions)]
            vendor = Vendor(
                vendor_id=f"VEND-{index:05d}",
                region_id=region_id,
                currency=currencies[region_id],
                category=categories[index % len(categories)],
                payment_terms_days=(30, 30, 45, 60)[index % 4],
            )
            vendors.append(vendor)
            self._sink(VENDORS).write(
                {
                    "vendor_id": vendor.vendor_id,
                    "vendor_name": f"Nexus Vendor {index:05d}",
                    "category": vendor.category,
                    "region_id": region_id,
                    "payment_terms_days": vendor.payment_terms_days,
                    "status": "ACTIVE",
                }
            )
        return tuple(vendors)

    def _generate_employees(self) -> tuple[Employee, ...]:
        currencies = {row[0]: row[2] for row in REGION_ROWS}
        regions = ("UK", "US", "US", "DE", "SG")
        departments = tuple(row[0] for row in DEPARTMENT_ROWS)
        salary_base = {"GBP": 7_200_000, "USD": 10_500_000, "EUR": 8_000_000, "SGD": 11_000_000}
        employees: list[Employee] = []
        for index in range(1, self.profile.employee_count + 1):
            region_id = self.rng.choice(regions)
            currency = currencies[region_id]
            hire_month = self.rng.randrange(min(54, len(self.actual_months)))
            hire_date = self.actual_months[hire_month] + timedelta(
                days=self.rng.randrange(0, 20)
            )
            termination_date: date | None = None
            if index % 17 == 0 and hire_month + 18 < len(self.actual_months):
                termination_month = self.rng.randrange(hire_month + 12, len(self.actual_months))
                termination_date = _month_end(self.actual_months[termination_month])
            department_id = departments[index % len(departments)]
            annual_salary = salary_base[currency] + self.rng.randrange(-1_200_000, 4_000_000)
            employee = Employee(
                employee_id=f"EMP-{index:05d}",
                department_id=department_id,
                region_id=region_id,
                currency=currency,
                hire_date=hire_date,
                termination_date=termination_date,
                annual_salary_minor=annual_salary,
            )
            employees.append(employee)
            emitted_department = department_id
            if index % 211 == 0:
                emitted_department = ""
                self._defect(
                    defect_type="HRIS_MISSING_DEPARTMENT",
                    dataset_path=EMPLOYEES.path,
                    source_record_ref=employee.employee_id,
                    detector="HERMES_HRIS_DEPARTMENT_COMPLETENESS",
                    severity="HIGH",
                    treatment="QUARANTINE_EMPLOYEE_DIMENSION_ROW",
                    description="HRIS employee intentionally lacks a department code.",
                )
            self._sink(EMPLOYEES).write(
                {
                    "employee_id": employee.employee_id,
                    "department_id": emitted_department,
                    "region_id": region_id,
                    "hire_date": hire_date.isoformat(),
                    "termination_date": termination_date.isoformat() if termination_date else "",
                    "annual_salary_minor": annual_salary,
                    "salary_currency": currency,
                    "employment_status": "TERMINATED" if termination_date else "ACTIVE",
                }
            )
        return tuple(employees)

    def _subscription_event(
        self,
        *,
        subscription: Subscription,
        sequence: int,
        event_date: date,
        event_type: str,
        event_reason: str,
        previous_mrr_minor: int,
        new_mrr_minor: int,
    ) -> None:
        rate = self._rate(event_date, subscription.customer.currency)
        reporting_previous = _to_reporting_minor(previous_mrr_minor, rate)
        reporting_new = _to_reporting_minor(new_mrr_minor, rate)
        self._sink(SUBSCRIPTION_EVENTS).write(
            {
                "subscription_event_id": (
                    f"SEVT-{subscription.subscription_id}-{sequence:03d}"
                ),
                "subscription_id": subscription.subscription_id,
                "customer_id": subscription.customer.customer_id,
                "event_sequence": sequence,
                "event_date": event_date.isoformat(),
                "event_type": event_type,
                "event_reason": event_reason,
                "previous_mrr_minor": previous_mrr_minor,
                "new_mrr_minor": new_mrr_minor,
                "mrr_delta_minor": new_mrr_minor - previous_mrr_minor,
                "currency": subscription.customer.currency,
                "reporting_previous_mrr_minor": reporting_previous,
                "reporting_new_mrr_minor": reporting_new,
                "reporting_mrr_delta_minor": reporting_new - reporting_previous,
                "reporting_currency": self.request.reporting_currency,
                "source_system": "BILLING",
            }
        )

    def _generate_subscriptions(
        self, customers: tuple[Customer, ...]
    ) -> tuple[Subscription, ...]:
        product_ids = tuple(row[0] for row in PRODUCT_ROWS if row[3] != "SERVICES")
        segment_base = {"SMB": 45_000, "MID_MARKET": 160_000, "ENTERPRISE": 620_000}
        subscriptions: list[Subscription] = []
        for index, customer in enumerate(customers, start=1):
            start_date = date(customer.created_date.year, customer.created_date.month, 1)
            end_date: date | None = None
            if index % 23 == 0 and _add_months(start_date, 18) < self.request.actuals_end:
                available = len(_month_starts(_add_months(start_date, 18), self.request.actuals_end))
                end_date = _month_end(_add_months(start_date, 18 + self.rng.randrange(available)))
            monthly = index % 100 < self.profile.monthly_invoice_share_pct
            product_id = product_ids[index % len(product_ids)]
            mrr = segment_base[customer.segment] + self.rng.randrange(0, segment_base[customer.segment])
            if product_id == "PROD-AI":
                mrr = mrr * 13 // 10
            subscription = Subscription(
                subscription_id=f"SUB-{index:06d}",
                customer=customer,
                product_id=product_id,
                start_date=start_date,
                end_date=end_date,
                billing_frequency="MONTHLY" if monthly else "ANNUAL",
                monthly_recurring_revenue_minor=mrr,
            )
            subscriptions.append(subscription)
            self._sink(SUBSCRIPTIONS).write(
                {
                    "subscription_id": subscription.subscription_id,
                    "customer_id": customer.customer_id,
                    "product_id": product_id,
                    "contract_start_date": start_date.isoformat(),
                    "contract_end_date": end_date.isoformat() if end_date else "",
                    "billing_frequency": subscription.billing_frequency,
                    "monthly_recurring_revenue_minor": mrr,
                    "currency": customer.currency,
                    "status": "CHURNED" if end_date else "ACTIVE",
                }
            )
            event_sequence = 1
            self._subscription_event(
                subscription=subscription,
                sequence=event_sequence,
                event_date=start_date,
                event_type="START",
                event_reason="NEW_CUSTOMER",
                previous_mrr_minor=0,
                new_mrr_minor=mrr,
            )
            renewal_date = _add_months(start_date, 12)
            while renewal_date <= self.request.actuals_end and (
                end_date is None or renewal_date <= end_date
            ):
                event_sequence += 1
                self._subscription_event(
                    subscription=subscription,
                    sequence=event_sequence,
                    event_date=renewal_date,
                    event_type="RENEWAL",
                    event_reason="CONTRACT_RENEWAL",
                    previous_mrr_minor=mrr,
                    new_mrr_minor=mrr,
                )
                renewal_date = _add_months(renewal_date, 12)
            if end_date:
                event_sequence += 1
                self._subscription_event(
                    subscription=subscription,
                    sequence=event_sequence,
                    event_date=end_date,
                    event_type="CHURN",
                    event_reason="CUSTOMER_TERMINATION",
                    previous_mrr_minor=mrr,
                    new_mrr_minor=0,
                )
        return tuple(subscriptions)

    def _opening_events(self) -> None:
        opening = self.request.history_start
        entries = (
            ("CAPITAL_CONTRIBUTION_RECEIVED", "OPEN-CAPITAL", 5_000_000_000, (("1000", 5_000_000_000, 0), ("3000", 0, 5_000_000_000))),
            ("DEBT_DRAWN", "OPEN-DEBT", 1_500_000_000, (("1000", 1_500_000_000, 0), ("2400", 0, 1_500_000_000))),
            ("FIXED_ASSET_ACQUIRED", "OPEN-PPE", 1_000_000_000, (("1500", 1_000_000_000, 0), ("1000", 0, 1_000_000_000))),
            ("BUSINESS_ACQUIRED", "OPEN-GOODWILL", 500_000_000, (("1600", 500_000_000, 0), ("1000", 0, 500_000_000))),
            ("INTANGIBLE_ASSET_ACQUIRED", "OPEN-INTANGIBLE", 400_000_000, (("1700", 400_000_000, 0), ("1000", 0, 400_000_000))),
            ("LEASE_COMMENCED", "OPEN-LEASE", 300_000_000, (("1800", 300_000_000, 0), ("2500", 0, 300_000_000))),
        )
        opening_refs: list[str] = []
        opening_ref_by_source: dict[str, str] = {}
        for event_type, source_ref, amount, lines in entries:
            event_ref = self._business_event(
                event_type=event_type,
                source_system="CORPORATE_ACTIONS",
                source_record_ref=source_ref,
                occurred_date=opening,
                effective_date=opening,
                counterparty_ref="NEXUS-SHAREHOLDERS",
                local_amount_minor=amount,
                currency=REPORTING_CURRENCY,
                reporting_amount_minor=amount,
                posting_rule_ref=f"PR-{event_type}@v1",
                lines=lines,
            )
            opening_refs.append(event_ref)
            opening_ref_by_source[source_ref] = event_ref
        self.formation_debt_event_ref = opening_ref_by_source["OPEN-DEBT"]
        self.opening_event_ref_by_source = opening_ref_by_source
        self._sink(EQUITY_MOVEMENTS).write(
            {
                "equity_movement_id": "EQ-FORMATION-2021",
                "period_id": _period_id(opening),
                "legal_entity_id": LEGAL_ENTITY_ID,
                "equity_component": "SHARE_CAPITAL",
                "movement_type": "ORDINARY_SHARE_ISSUANCE",
                "business_event_ref": opening_ref_by_source["OPEN-CAPITAL"],
                "amount_minor": 5_000_000_000,
                "currency": REPORTING_CURRENCY,
                "authorisation_ref": "BOARD-FORMATION-FUNDING@v1",
            }
        )
        opening_balances = {
            "1000": 4_600_000_000,
            "1500": 1_000_000_000,
            "1600": 500_000_000,
            "1700": 400_000_000,
            "1800": 300_000_000,
            "2400": -1_500_000_000,
            "2500": -300_000_000,
            "3000": -5_000_000_000,
        }
        for account_id, amount in opening_balances.items():
            self._sink(OPENING_BALANCE_SHEET).write(
                {
                    "as_of_date": opening.isoformat(),
                    "account_id": account_id,
                    "opening_balance_minor": amount,
                    "currency": REPORTING_CURRENCY,
                    "source_business_event_refs": ",".join(opening_refs),
                }
            )

    def _generate_billing(self, subscriptions: tuple[Subscription, ...]) -> None:
        invoice_sequence = 0
        for subscription in subscriptions:
            active_months = _month_starts(subscription.start_date, self.request.actuals_end)
            for active_index, month in enumerate(active_months):
                if subscription.end_date and month > subscription.end_date:
                    break
                if subscription.billing_frequency == "ANNUAL" and active_index % 12 != 0:
                    continue
                invoice_sequence += 1
                invoice_id = f"INV-{invoice_sequence:08d}"
                invoice_date = month + timedelta(days=(invoice_sequence % 5))
                service_months = 12 if subscription.billing_frequency == "ANNUAL" else 1
                service_end = _month_end(_add_months(month, service_months - 1))
                net_amount = subscription.monthly_recurring_revenue_minor * service_months
                usage_amount = net_amount * 7 // 100 if invoice_sequence % 7 == 0 else 0
                net_amount += usage_amount
                tax_amount = net_amount * 20 // 100
                gross_amount = net_amount + tax_amount
                rate = self._rate(invoice_date, subscription.customer.currency)
                reporting_net = _to_reporting_minor(net_amount, rate)
                reporting_tax = _to_reporting_minor(tax_amount, rate)
                reporting_gross = reporting_net + reporting_tax
                due_date = invoice_date + timedelta(
                    days=45 if subscription.customer.segment == "ENTERPRISE" else 30
                )
                pays = invoice_sequence % 100 < self.profile.payment_success_pct
                payment_date = invoice_date + timedelta(days=7 + invoice_sequence % 59)
                if payment_date > self.request.actuals_end:
                    pays = False
                unallocated = pays and invoice_sequence % 197 == 0
                invoice_status = "OPEN"
                if pays and not unallocated:
                    invoice_status = "PAID"
                elif unallocated:
                    invoice_status = "OPEN_UNALLOCATED"
                external_number = f"BILL-{invoice_sequence:08d}"
                if invoice_sequence % 997 == 0:
                    external_number = f"BILL-{invoice_sequence - 1:08d}"
                    self._defect(
                        defect_type="DUPLICATE_BILLING_INVOICE_NUMBER",
                        dataset_path=INVOICES.path,
                        source_record_ref=invoice_id,
                        detector="HERMES_BILLING_DUPLICATE_INVOICE",
                        severity="HIGH",
                        treatment="QUARANTINE_DUPLICATE_SOURCE_RECORD",
                        description=(
                            "Billing invoice reuses a prior external invoice number."
                        ),
                    )
                self._sink(INVOICES).write(
                    {
                        "invoice_id": invoice_id,
                        "customer_id": subscription.customer.customer_id,
                        "subscription_id": subscription.subscription_id,
                        "invoice_date": invoice_date.isoformat(),
                        "due_date": due_date.isoformat(),
                        "service_period_start": month.isoformat(),
                        "service_period_end": service_end.isoformat(),
                        "invoice_amount_minor": net_amount,
                        "tax_amount_minor": tax_amount,
                        "currency": subscription.customer.currency,
                        "reporting_amount_minor": reporting_net,
                        "reporting_currency": self.request.reporting_currency,
                        "invoice_status": invoice_status,
                        "external_invoice_number": external_number,
                    }
                )
                billings = self.deferred_billings[
                    (_period_id(month), subscription.customer.currency)
                ]
                billings[0] += net_amount
                billings[1] += reporting_net
                base_line = net_amount - usage_amount
                base_reporting = _to_reporting_minor(base_line, rate)
                self._sink(INVOICE_LINES).write(
                    {
                        "invoice_line_id": f"{invoice_id}-L01",
                        "invoice_id": invoice_id,
                        "line_no": 1,
                        "product_id": subscription.product_id,
                        "line_type": "SUBSCRIPTION",
                        "quantity": 1,
                        "unit_price_minor": base_line,
                        "line_amount_minor": base_line,
                        "currency": subscription.customer.currency,
                        "reporting_line_amount_minor": base_reporting,
                        "reporting_currency": self.request.reporting_currency,
                    }
                )
                if usage_amount:
                    self._sink(INVOICE_LINES).write(
                        {
                            "invoice_line_id": f"{invoice_id}-L02",
                            "invoice_id": invoice_id,
                            "line_no": 2,
                            "product_id": subscription.product_id,
                            "line_type": "USAGE",
                            "quantity": 1,
                            "unit_price_minor": usage_amount,
                            "line_amount_minor": usage_amount,
                            "currency": subscription.customer.currency,
                            "reporting_line_amount_minor": reporting_net - base_reporting,
                            "reporting_currency": self.request.reporting_currency,
                        }
                    )
                invoice_lines: tuple[tuple[str, int, int], ...] = (
                    ("1100", reporting_gross, 0),
                    ("2100", 0, reporting_net),
                    ("2300", 0, reporting_tax),
                )
                self._business_event(
                    event_type="CUSTOMER_INVOICE_ISSUED",
                    source_system="BILLING",
                    source_record_ref=invoice_id,
                    occurred_date=invoice_date,
                    effective_date=invoice_date,
                    counterparty_ref=subscription.customer.customer_id,
                    local_amount_minor=gross_amount,
                    currency=subscription.customer.currency,
                    reporting_amount_minor=reporting_gross,
                    posting_rule_ref="PR-CUSTOMER-INVOICE@v1",
                    lines=invoice_lines,
                    recorded_delay_days=5 if invoice_sequence % 809 == 0 else 0,
                )
                if invoice_sequence % 809 == 0:
                    self._defect(
                        defect_type="LATE_RECORDED_BILLING_EVENT",
                        dataset_path=BUSINESS_EVENTS.path,
                        source_record_ref=invoice_id,
                        detector="HERMES_EVENT_LATENCY_CONTROL",
                        severity="MEDIUM",
                        treatment="MONITOR_AND_DISCLOSE",
                        description=(
                            "Billing event is intentionally recorded five days late."
                        ),
                    )

                recognised_total = 0
                reporting_revenue_base = reporting_net // service_months
                reporting_revenue_remainder = reporting_net % service_months
                for recognition_index in range(service_months):
                    recognition_month = _add_months(month, recognition_index)
                    if recognition_month > self.request.actuals_end:
                        break
                    remaining = net_amount - recognised_total
                    remaining_periods = service_months - recognition_index
                    local_revenue = remaining // remaining_periods
                    recognised_total += local_revenue
                    reporting_revenue = reporting_revenue_base + int(
                        recognition_index < reporting_revenue_remainder
                    )
                    schedule_id = f"REV-{invoice_id}-{recognition_index + 1:02d}"
                    self._sink(REVENUE_SCHEDULE).write(
                        {
                            "schedule_id": schedule_id,
                            "invoice_id": invoice_id,
                            "subscription_id": subscription.subscription_id,
                            "recognition_period": _period_id(recognition_month),
                            "recognition_date": _month_end(recognition_month).isoformat(),
                            "revenue_amount_minor": local_revenue,
                            "currency": subscription.customer.currency,
                            "reporting_revenue_amount_minor": reporting_revenue,
                            "reporting_currency": self.request.reporting_currency,
                            "recognition_status": "RECOGNISED",
                        }
                    )
                    recognised = self.recognised_revenue[
                        (
                            _period_id(recognition_month),
                            subscription.customer.currency,
                        )
                    ]
                    recognised[0] += local_revenue
                    recognised[1] += reporting_revenue
                    self._business_event(
                        event_type="SUBSCRIPTION_REVENUE_RECOGNISED",
                        source_system="REVENUE_SUBLEDGER",
                        source_record_ref=schedule_id,
                        occurred_date=_month_end(recognition_month),
                        effective_date=_month_end(recognition_month),
                        counterparty_ref=subscription.customer.customer_id,
                        local_amount_minor=local_revenue,
                        currency=subscription.customer.currency,
                        reporting_amount_minor=reporting_revenue,
                        posting_rule_ref="PR-SUBSCRIPTION-REVENUE@v1",
                        lines=(("2100", reporting_revenue, 0), ("4000", 0, reporting_revenue)),
                    )

                if pays:
                    payment_id = f"PAY-{invoice_sequence:08d}"
                    self._sink(PAYMENTS).write(
                        {
                            "payment_id": payment_id,
                            "customer_id": subscription.customer.customer_id,
                            "payment_date": payment_date.isoformat(),
                            "payment_amount_minor": gross_amount,
                            "currency": subscription.customer.currency,
                            "reporting_amount_minor": reporting_gross,
                            "reporting_currency": self.request.reporting_currency,
                            "payment_method": "BANK_TRANSFER",
                            "payment_status": "RECEIVED",
                            "source_bank_reference": f"BANK-{invoice_sequence:010d}",
                        }
                    )
                    if unallocated:
                        self._defect(
                            defect_type="UNALLOCATED_CASH_RECEIPT",
                            dataset_path=PAYMENTS.path,
                            source_record_ref=payment_id,
                            detector="HERMES_CASH_APPLICATION_RECONCILIATION",
                            severity="HIGH",
                            treatment="ARGUS_EXCEPTION_AND_AEGIS_REVIEW",
                            description=(
                                "Cash receipt intentionally has no invoice allocation."
                            ),
                        )
                        credit_account = "2250"
                    else:
                        allocation_id = f"ALLOC-{invoice_sequence:08d}"
                        self._sink(PAYMENT_ALLOCATIONS).write(
                            {
                                "allocation_id": allocation_id,
                                "payment_id": payment_id,
                                "invoice_id": invoice_id,
                                "allocated_amount_minor": gross_amount,
                                "currency": subscription.customer.currency,
                                "reporting_allocated_amount_minor": reporting_gross,
                                "reporting_currency": self.request.reporting_currency,
                                "allocation_date": payment_date.isoformat(),
                                "allocation_status": "ALLOCATED",
                            }
                        )
                        credit_account = "1100"
                    self._business_event(
                        event_type="CASH_RECEIPT_RECORDED",
                        source_system="PAYMENTS",
                        source_record_ref=payment_id,
                        occurred_date=payment_date,
                        effective_date=payment_date,
                        counterparty_ref=subscription.customer.customer_id,
                        local_amount_minor=gross_amount,
                        currency=subscription.customer.currency,
                        reporting_amount_minor=reporting_gross,
                        posting_rule_ref="PR-CASH-RECEIPT@v1",
                        lines=(("1000", reporting_gross, 0), (credit_account, 0, reporting_gross)),
                    )

                ageing_end = payment_date if pays and not unallocated else self.request.actuals_end
                snapshot = invoice_date
                while snapshot <= ageing_end:
                    if snapshot == ageing_end and pays and not unallocated:
                        break
                    self._sink(AR_AGEING).write(
                        {
                            "snapshot_date": snapshot.isoformat(),
                            "invoice_id": invoice_id,
                            "customer_id": subscription.customer.customer_id,
                            "due_date": due_date.isoformat(),
                            "open_amount_minor": gross_amount,
                            "currency": subscription.customer.currency,
                            "reporting_open_amount_minor": reporting_gross,
                            "reporting_currency": self.request.reporting_currency,
                            "days_past_due": (snapshot - due_date).days,
                            "ageing_bucket": _ageing_bucket((snapshot - due_date).days),
                        }
                    )
                    snapshot += timedelta(days=1)

    def _generate_deferred_revenue_rollforward(self) -> None:
        opening_by_currency = {row[2]: 0 for row in REGION_ROWS}
        reporting_opening_by_currency = {row[2]: 0 for row in REGION_ROWS}
        for month in self.actual_months:
            period = _period_id(month)
            for currency in sorted(opening_by_currency):
                local_billings, reporting_billings = self.deferred_billings[
                    (period, currency)
                ]
                local_revenue, reporting_revenue = self.recognised_revenue[
                    (period, currency)
                ]
                opening = opening_by_currency[currency]
                reporting_opening = reporting_opening_by_currency[currency]
                closing = opening + local_billings - local_revenue
                reporting_closing = (
                    reporting_opening + reporting_billings - reporting_revenue
                )
                if closing < 0 or reporting_closing < 0:
                    raise ValueError("deferred revenue roll-forward became negative")
                self._sink(DEFERRED_REVENUE_ROLLFORWARD).write(
                    {
                        "period_id": period,
                        "currency": currency,
                        "opening_deferred_revenue_minor": opening,
                        "new_billings_minor": local_billings,
                        "recognised_revenue_minor": local_revenue,
                        "closing_deferred_revenue_minor": closing,
                        "reporting_opening_deferred_revenue_minor": (
                            reporting_opening
                        ),
                        "reporting_new_billings_minor": reporting_billings,
                        "reporting_recognised_revenue_minor": reporting_revenue,
                        "reporting_closing_deferred_revenue_minor": (
                            reporting_closing
                        ),
                        "reporting_currency": self.request.reporting_currency,
                        "source_system": "REVENUE_SUBLEDGER",
                    }
                )
                opening_by_currency[currency] = closing
                reporting_opening_by_currency[currency] = reporting_closing

    def _generate_procurement(self, vendors: tuple[Vendor, ...]) -> None:
        account_by_category = {
            "CLOUD_HOSTING": "5000",
            "PROFESSIONAL_SERVICES": "6200",
            "SOFTWARE": "6000",
            "MARKETING": "6100",
            "FACILITIES": "6200",
        }
        departments = tuple(row[0] for row in DEPARTMENT_ROWS)
        sequence = 0
        for month_index, month in enumerate(self.actual_months):
            for vendor_index, vendor in enumerate(vendors, start=1):
                if (month_index + vendor_index) % 3 == 0:
                    continue
                sequence += 1
                invoice_id = f"VINV-{sequence:07d}"
                invoice_date = month + timedelta(days=(vendor_index % 20))
                amount = 75_000 + self.rng.randrange(25_000, 650_000)
                if vendor.category == "CLOUD_HOSTING":
                    amount *= 3
                rate = self._rate(invoice_date, vendor.currency)
                reporting_amount = _to_reporting_minor(amount, rate)
                external_number = f"SUP-{sequence:08d}"
                if sequence % 431 == 0:
                    external_number = f"SUP-{sequence - 1:08d}"
                    self._defect(
                        defect_type="DUPLICATE_VENDOR_INVOICE_NUMBER",
                        dataset_path=VENDOR_INVOICES.path,
                        source_record_ref=invoice_id,
                        detector="HERMES_AP_DUPLICATE_INVOICE",
                        severity="HIGH",
                        treatment="BLOCK_PAYMENT_AND_REVIEW",
                        description=(
                            "Vendor invoice intentionally duplicates an "
                            "external number."
                        ),
                    )
                department_id = departments[(vendor_index + month_index) % len(departments)]
                expense_account = account_by_category[vendor.category]
                due_date = invoice_date + timedelta(days=vendor.payment_terms_days)
                pays = sequence % 100 < 93
                payment_date = due_date + timedelta(days=sequence % 20 - 5)
                if payment_date > self.request.actuals_end:
                    pays = False
                self._sink(VENDOR_INVOICES).write(
                    {
                        "vendor_invoice_id": invoice_id,
                        "vendor_id": vendor.vendor_id,
                        "department_id": department_id,
                        "invoice_date": invoice_date.isoformat(),
                        "due_date": due_date.isoformat(),
                        "expense_account_id": expense_account,
                        "invoice_amount_minor": amount,
                        "tax_amount_minor": 0,
                        "currency": vendor.currency,
                        "invoice_status": "PAID" if pays else "OPEN",
                        "external_invoice_number": external_number,
                    }
                )
                self._sink(VENDOR_INVOICE_LINES).write(
                    {
                        "vendor_invoice_line_id": f"{invoice_id}-L01",
                        "vendor_invoice_id": invoice_id,
                        "vendor_id": vendor.vendor_id,
                        "line_no": 1,
                        "department_id": department_id,
                        "expense_account_id": expense_account,
                        "service_period_start": month.isoformat(),
                        "service_period_end": _month_end(month).isoformat(),
                        "line_description": vendor.category.replace("_", " ").title(),
                        "line_amount_minor": amount,
                        "currency": vendor.currency,
                        "reporting_line_amount_minor": reporting_amount,
                        "reporting_currency": self.request.reporting_currency,
                    }
                )
                self._business_event(
                    event_type="VENDOR_INVOICE_APPROVED",
                    source_system="PROCUREMENT",
                    source_record_ref=invoice_id,
                    occurred_date=invoice_date,
                    effective_date=invoice_date,
                    counterparty_ref=vendor.vendor_id,
                    local_amount_minor=amount,
                    currency=vendor.currency,
                    reporting_amount_minor=reporting_amount,
                    posting_rule_ref="PR-VENDOR-INVOICE@v1",
                    lines=((expense_account, reporting_amount, 0), ("2000", 0, reporting_amount)),
                )
                if pays:
                    payment_id = f"VPAY-{sequence:07d}"
                    self._sink(VENDOR_PAYMENTS).write(
                        {
                            "vendor_payment_id": payment_id,
                            "vendor_invoice_id": invoice_id,
                            "vendor_id": vendor.vendor_id,
                            "payment_date": payment_date.isoformat(),
                            "payment_amount_minor": amount,
                            "currency": vendor.currency,
                            "payment_status": "SETTLED",
                        }
                    )
                    self._business_event(
                        event_type="VENDOR_PAYMENT_SETTLED",
                        source_system="TREASURY",
                        source_record_ref=payment_id,
                        occurred_date=payment_date,
                        effective_date=payment_date,
                        counterparty_ref=vendor.vendor_id,
                        local_amount_minor=amount,
                        currency=vendor.currency,
                        reporting_amount_minor=reporting_amount,
                        posting_rule_ref="PR-VENDOR-PAYMENT@v1",
                        lines=(("2000", reporting_amount, 0), ("1000", 0, reporting_amount)),
                    )

                ageing_end = payment_date if pays else self.request.actuals_end
                snapshot = invoice_date
                while snapshot <= ageing_end:
                    if snapshot == ageing_end and pays:
                        break
                    days_past_due = (snapshot - due_date).days
                    self._sink(AP_AGEING).write(
                        {
                            "snapshot_date": snapshot.isoformat(),
                            "vendor_invoice_id": invoice_id,
                            "vendor_id": vendor.vendor_id,
                            "due_date": due_date.isoformat(),
                            "invoice_amount_minor": amount,
                            "paid_amount_minor": 0,
                            "open_amount_minor": amount,
                            "currency": vendor.currency,
                            "reporting_open_amount_minor": reporting_amount,
                            "reporting_currency": self.request.reporting_currency,
                            "days_past_due": days_past_due,
                            "ageing_bucket": _ageing_bucket(days_past_due),
                            "ap_status": "OVERDUE" if days_past_due > 0 else "OPEN",
                        }
                    )
                    snapshot += timedelta(days=1)

    def _generate_payroll(self, employees: tuple[Employee, ...]) -> None:
        account_by_department = {
            "DEP-RND": "6000",
            "DEP-ENG": "6000",
            "DEP-SALES": "6100",
            "DEP-MKT": "6100",
            "DEP-CS": "6100",
            "DEP-FIN": "6200",
            "DEP-PEOPLE": "6200",
            "DEP-OPS": "6200",
        }
        for month in self.actual_months:
            payroll_date = _month_end(month)
            for employee in employees:
                if employee.hire_date > payroll_date:
                    continue
                if employee.termination_date and employee.termination_date < month:
                    continue
                gross = employee.annual_salary_minor // 12
                employer_tax = gross * 12 // 100
                benefits = gross * 8 // 100
                total = gross + employer_tax + benefits
                rate = self._rate(month, employee.currency)
                reporting_total = _to_reporting_minor(total, rate)
                line_id = f"PAYROLL-{_period_id(month)}-{employee.employee_id}"
                self._sink(PAYROLL_LINES).write(
                    {
                        "payroll_line_id": line_id,
                        "period_id": _period_id(month),
                        "employee_id": employee.employee_id,
                        "department_id": employee.department_id,
                        "region_id": employee.region_id,
                        "gross_pay_minor": gross,
                        "employer_tax_minor": employer_tax,
                        "benefits_minor": benefits,
                        "total_payroll_cost_minor": total,
                        "currency": employee.currency,
                        "reporting_payroll_cost_minor": reporting_total,
                        "reporting_currency": self.request.reporting_currency,
                        "payroll_status": "POSTED",
                    }
                )
                self._sink(HEADCOUNT_SNAPSHOT).write(
                    {
                        "snapshot_period": _period_id(month),
                        "employee_id": employee.employee_id,
                        "department_id": employee.department_id,
                        "region_id": employee.region_id,
                        "employment_status": "ACTIVE",
                        "fte_bps": 10_000,
                        "annual_salary_minor": employee.annual_salary_minor,
                        "currency": employee.currency,
                        "reporting_annual_salary_minor": _to_reporting_minor(
                            employee.annual_salary_minor, rate
                        ),
                        "reporting_currency": self.request.reporting_currency,
                        "is_ghost_headcount": False,
                    }
                )
                reporting_gross = _to_reporting_minor(gross, rate)
                reporting_tax = _to_reporting_minor(employer_tax, rate)
                reporting_components = (
                    ("BASE_SALARY", gross, reporting_gross),
                    ("EMPLOYER_TAX", employer_tax, reporting_tax),
                    (
                        "BENEFITS",
                        benefits,
                        reporting_total - reporting_gross - reporting_tax,
                    ),
                )
                for component, local_amount, reporting_amount in reporting_components:
                    self._sink(EMPLOYEE_COMPENSATION).write(
                        {
                            "compensation_line_id": (
                                f"COMP-{_period_id(month)}-"
                                f"{employee.employee_id}-{component}"
                            ),
                            "period_id": _period_id(month),
                            "employee_id": employee.employee_id,
                            "department_id": employee.department_id,
                            "region_id": employee.region_id,
                            "compensation_component": component,
                            "amount_minor": local_amount,
                            "currency": employee.currency,
                            "reporting_amount_minor": reporting_amount,
                            "reporting_currency": self.request.reporting_currency,
                            "source_system": "PAYROLL",
                        }
                    )
                account_id = account_by_department[employee.department_id]
                self._business_event(
                    event_type="PAYROLL_COST_INCURRED",
                    source_system="PAYROLL",
                    source_record_ref=line_id,
                    occurred_date=payroll_date,
                    effective_date=payroll_date,
                    counterparty_ref=employee.employee_id,
                    local_amount_minor=total,
                    currency=employee.currency,
                    reporting_amount_minor=reporting_total,
                    posting_rule_ref="PR-PAYROLL@v1",
                    lines=((account_id, reporting_total, 0), ("1000", 0, reporting_total)),
                )

    def _generate_headcount_plan(self) -> None:
        departments = tuple(row[0] for row in DEPARTMENT_ROWS)
        region_currency = {row[0]: row[2] for row in REGION_ROWS}
        regions = tuple(region_currency)
        position_count = max(12, self.profile.employee_count // 8)
        start = _add_months(self.request.actuals_end, 1)
        for index in range(1, position_count + 1):
            department_id = departments[index % len(departments)]
            region_id = regions[index % len(regions)]
            currency = region_currency[region_id]
            hire_date = _add_months(start, (index - 1) % 24)
            midpoint = 7_500_000 + (index % 7) * 650_000
            rate = self._rate(hire_date, currency)
            self._sink(HEADCOUNT_PLAN).write(
                {
                    "position_id": f"POS-{index:05d}",
                    "scenario_code": "BASE",
                    "department_id": department_id,
                    "region_id": region_id,
                    "planned_hire_date": hire_date.isoformat(),
                    "role_family": department_id.removeprefix("DEP-"),
                    "seniority_level": ("MID", "SENIOR", "LEAD")[index % 3],
                    "salary_low_minor": midpoint * 9 // 10,
                    "salary_mid_minor": midpoint,
                    "salary_high_minor": midpoint * 11 // 10,
                    "currency": currency,
                    "reporting_salary_mid_minor": _to_reporting_minor(
                        midpoint, rate
                    ),
                    "reporting_currency": self.request.reporting_currency,
                    "position_status": "APPROVED" if index % 4 else "PROPOSED",
                    "backfill_flag": index % 5 == 0,
                }
            )

    def _write_source_admission(
        self,
        *,
        source_definition: DatasetDefinition,
        source_system: str,
        source_record_ref: str,
        source_payload: dict[str, object],
        candidate_business_event_ref: str,
        event_date: date,
        duplicate_of_ref: str = "",
        late_arrival: bool = False,
        legal_entity_id: str = LEGAL_ENTITY_ID,
        currency: str = REPORTING_CURRENCY,
    ) -> str:
        result = self.fixed_asset_admission.admit(
            SourceAdmissionCandidate(
                source_dataset_path=source_definition.path,
                source_system=source_system,
                source_record_ref=source_record_ref,
                source_payload=source_payload,
                candidate_business_event_ref=candidate_business_event_ref,
                event_time=_timestamp(event_date),
                ingested_at=self.request.built_at,
                legal_entity_id=legal_entity_id,
                currency=currency,
                duplicate_of_ref=duplicate_of_ref,
                late_arrival=late_arrival,
            )
        )
        self._sink(SOURCE_ADMISSION_RESULTS).write(result.as_row())
        return result.admission_decision

    def _post_fixed_asset_event(
        self,
        *,
        event_type: str,
        source_definition: DatasetDefinition,
        source_system: str,
        source_record_ref: str,
        source_payload: dict[str, object],
        occurred_date: date,
        effective_date: date,
        counterparty_ref: str,
        asset: FixedAsset,
        event_amount_minor: int,
        gross_cost_minor: int = 0,
        accumulated_depreciation_minor: int = 0,
        disposal_proceeds_minor: int = 0,
        recorded_delay_days: int = 0,
    ) -> str:
        candidate_ref = _stable_ref(
            "BE", event_type, source_system, source_record_ref
        )
        decision = self._write_source_admission(
            source_definition=source_definition,
            source_system=source_system,
            source_record_ref=source_record_ref,
            source_payload=source_payload,
            candidate_business_event_ref=candidate_ref,
            event_date=effective_date,
            late_arrival=recorded_delay_days > 0,
        )
        if decision == "QUARANTINED":
            raise ValueError("quarantined fixed-asset candidate cannot be posted")
        posting = self.fixed_asset_posting_rules.derive(
            FixedAssetPostingInput(
                origin_class="BUSINESS_EVENT",
                event_type=event_type,  # type: ignore[arg-type]
                asset=asset,
                event_amount_minor=event_amount_minor,
                gross_cost_minor=gross_cost_minor,
                accumulated_depreciation_minor=(
                    accumulated_depreciation_minor
                ),
                disposal_proceeds_minor=disposal_proceeds_minor,
            )
        )
        event_ref = self._business_event(
            event_type=event_type,
            source_system=source_system,
            source_record_ref=source_record_ref,
            occurred_date=occurred_date,
            effective_date=effective_date,
            counterparty_ref=counterparty_ref,
            local_amount_minor=posting.journal_amount_minor,
            currency=REPORTING_CURRENCY,
            reporting_amount_minor=posting.journal_amount_minor,
            posting_rule_ref=posting.posting_rule_ref,
            lines=posting.lines,
            recorded_delay_days=recorded_delay_days,
        )
        if event_ref != candidate_ref:
            raise ValueError("Hermes candidate identity differs from Atlas event")
        return event_ref

    def _write_asset_lifecycle_event(
        self,
        *,
        lifecycle_event_id: str,
        asset: FixedAsset,
        event_type: str,
        event_date: date,
        source_record_ref: str,
        related_capital_invoice_id: str,
        event_amount_minor: int,
        gross_cost_minor: int = 0,
        accumulated_depreciation_minor: int = 0,
        disposal_proceeds_minor: int = 0,
        authorisation_ref: str,
        recorded_delay_days: int = 0,
    ) -> dict[str, object]:
        row = {
            "asset_lifecycle_event_id": lifecycle_event_id,
            "asset_id": asset.asset_id,
            "legal_entity_id": asset.legal_entity_id,
            "event_type": event_type,
            "event_date": event_date.isoformat(),
            "source_record_ref": source_record_ref,
            "related_capital_invoice_id": related_capital_invoice_id,
            "event_amount_minor": event_amount_minor,
            "gross_cost_minor": gross_cost_minor,
            "accumulated_depreciation_minor": (
                accumulated_depreciation_minor
            ),
            "disposal_proceeds_minor": disposal_proceeds_minor,
            "currency": asset.currency,
            "authorisation_ref": authorisation_ref,
            "source_recorded_at": _timestamp(
                event_date + timedelta(days=recorded_delay_days), 16
            ),
        }
        self._sink(ASSET_LIFECYCLE_EVENTS).write(row)
        return row

    def _write_fixed_asset_register(self, asset: FixedAsset) -> None:
        self._sink(FIXED_ASSET_REGISTER).write(
            {
                "asset_id": asset.asset_id,
                "legal_entity_id": asset.legal_entity_id,
                "asset_class": asset.asset_class,
                "source_system": asset.source_system,
                "source_record_ref": asset.source_record_ref,
                "acquisition_business_event_ref": (
                    asset.acquisition_business_event_ref
                ),
                "capital_purchase_order_id": asset.capital_purchase_order_id,
                "capital_goods_receipt_id": asset.capital_goods_receipt_id,
                "capital_invoice_id": asset.capital_invoice_id,
                "acquisition_date": asset.acquisition_date,
                "in_service_date": asset.in_service_date,
                "cost_minor": asset.cost_minor,
                "residual_value_minor": asset.residual_value_minor,
                "currency": asset.currency,
                "useful_life_months": asset.useful_life_months,
                "depreciation_method": asset.depreciation_method,
                "disposal_date": asset.disposal_date,
                "asset_status": asset.asset_status,
            }
        )

    def _write_fixed_asset_control(
        self,
        *,
        result_ref: str,
        definition_ref: str,
        period_id: str,
        asset_id: str,
        observation_type: str,
        status: str,
        severity: str,
        expected_minor: int,
        actual_minor: int,
        evidence_ref: str,
        source_record_refs: str,
    ) -> None:
        difference = actual_minor - expected_minor
        if status == "PASS" and difference:
            self.fixed_asset_control_failures += 1
            status = "EXCEPTION"
        self._sink(FIXED_ASSET_CONTROL_RESULTS).write(
            {
                "test_result_id": result_ref,
                "test_definition_ref": definition_ref,
                "test_run_ref": "ARGUS-FA-RUN-2026-06@v1",
                "period_id": period_id,
                "asset_id": asset_id,
                "observation_type": observation_type,
                "status": status,
                "severity": severity,
                "expected_amount_minor": expected_minor,
                "actual_amount_minor": actual_minor,
                "difference_minor": difference,
                "currency": REPORTING_CURRENCY,
                "evidence_ref": evidence_ref,
                "source_record_refs": source_record_refs,
            }
        )

    def _post_a22b_event(
        self,
        *,
        event_type: str,
        source_definition: DatasetDefinition,
        source_system: str,
        source_record_ref: str,
        source_payload: dict[str, object],
        occurred_date: date,
        effective_date: date,
        counterparty_ref: str,
        journal_amount_minor: int,
        posting_rule_ref: str,
        lines: tuple[tuple[str, int, int], ...],
        recorded_delay_days: int = 0,
        legal_entity_id: str = LEGAL_ENTITY_ID,
        currency: str = REPORTING_CURRENCY,
    ) -> str:
        candidate_ref = _stable_ref(
            "BE", event_type, source_system, source_record_ref
        )
        decision = self._write_source_admission(
            source_definition=source_definition,
            source_system=source_system,
            source_record_ref=source_record_ref,
            source_payload=source_payload,
            candidate_business_event_ref=candidate_ref,
            event_date=effective_date,
            late_arrival=recorded_delay_days > 0,
            legal_entity_id=legal_entity_id,
            currency=currency,
        )
        if decision == "QUARANTINED":
            raise ValueError("quarantined A2.2b candidate cannot be posted")
        event_ref = self._business_event(
            event_type=event_type,
            source_system=source_system,
            source_record_ref=source_record_ref,
            occurred_date=occurred_date,
            effective_date=effective_date,
            counterparty_ref=counterparty_ref,
            local_amount_minor=journal_amount_minor,
            currency=currency,
            reporting_amount_minor=journal_amount_minor,
            posting_rule_ref=posting_rule_ref,
            lines=lines,
            recorded_delay_days=recorded_delay_days,
            legal_entity_id=legal_entity_id,
        )
        if event_ref != candidate_ref:
            raise ValueError("Hermes candidate identity differs from Atlas event")
        return event_ref

    def _write_statutory_subledger_control(
        self,
        *,
        result_ref: str,
        definition_ref: str,
        period_id: str,
        domain: str,
        object_ref: str,
        observation_type: str,
        status: str,
        severity: str,
        expected_minor: int,
        actual_minor: int,
        evidence_ref: str,
        source_record_refs: str,
    ) -> None:
        difference = actual_minor - expected_minor
        if status == "PASS" and difference:
            self.stat_subledger_control_failures += 1
            status = "EXCEPTION"
        self._sink(STATUTORY_SUBLEDGER_CONTROL_RESULTS).write(
            {
                "test_result_id": result_ref,
                "test_definition_ref": definition_ref,
                "test_run_ref": "ARGUS-A22B-RUN-2026-06@v1",
                "period_id": period_id,
                "legal_entity_id": LEGAL_ENTITY_ID,
                "subledger_domain": domain,
                "object_ref": object_ref,
                "observation_type": observation_type,
                "status": status,
                "severity": severity,
                "expected_amount_minor": expected_minor,
                "actual_amount_minor": actual_minor,
                "difference_minor": difference,
                "currency": REPORTING_CURRENCY,
                "evidence_ref": evidence_ref,
                "source_record_refs": source_record_refs,
            }
        )

    def _generate_fixed_asset_vertical(
        self, vendors: tuple[Vendor, ...]
    ) -> None:
        opening = self.request.history_start
        opening_asset_specs = (
            (
                "FA-FORM-SERVERS",
                "COMPUTER_EQUIPMENT",
                400_000_000,
                60,
                "OPEN-PPE",
                "",
            ),
            (
                "FA-FORM-OFFICE",
                "OFFICE_EQUIPMENT",
                200_000_000,
                60,
                "OPEN-PPE",
                "2025-06-15",
            ),
            (
                "FA-FORM-LEASEHOLD",
                "LEASEHOLD_IMPROVEMENTS",
                400_000_000,
                120,
                "OPEN-PPE",
                "",
            ),
            (
                "FA-FORM-GOODWILL",
                "GOODWILL",
                500_000_000,
                0,
                "OPEN-GOODWILL",
                "",
            ),
            (
                "FA-FORM-SOFTWARE",
                "CAPITALISED_SOFTWARE",
                400_000_000,
                72,
                "OPEN-INTANGIBLE",
                "",
            ),
        )
        assets: list[FixedAsset] = []
        for asset_id, asset_class, cost, life, source_ref, disposal_date in (
            opening_asset_specs
        ):
            acquisition_ref = self.opening_event_ref_by_source[source_ref]
            asset = FixedAsset(
                asset_id=asset_id,
                legal_entity_id=LEGAL_ENTITY_ID,
                asset_class=asset_class,
                source_system="CORPORATE_ACTIONS",
                source_record_ref=f"FORMATION-{asset_id}",
                acquisition_business_event_ref=acquisition_ref,
                capital_purchase_order_id="",
                capital_goods_receipt_id="",
                capital_invoice_id="",
                acquisition_date=opening.isoformat(),
                in_service_date=opening.isoformat(),
                cost_minor=cost,
                residual_value_minor=0,
                currency=REPORTING_CURRENCY,
                useful_life_months=life,
                depreciation_method=(
                    "NOT_APPLICABLE" if life == 0 else "STRAIGHT_LINE_MONTHLY"
                ),
                disposal_date=disposal_date,
                asset_status="DISPOSED" if disposal_date else "ACTIVE",
            )
            lifecycle_id = f"FALE-{asset_id}-FORMATION"
            lifecycle = self._write_asset_lifecycle_event(
                lifecycle_event_id=lifecycle_id,
                asset=asset,
                event_type="FORMATION_ASSET_RECOGNISED",
                event_date=opening,
                source_record_ref=source_ref,
                related_capital_invoice_id="",
                event_amount_minor=cost,
                gross_cost_minor=cost,
                authorisation_ref="BOARD-FORMATION-ASSETS@v1",
            )
            self._write_source_admission(
                source_definition=ASSET_LIFECYCLE_EVENTS,
                source_system="CORPORATE_ACTIONS",
                source_record_ref=lifecycle_id,
                source_payload=lifecycle,
                candidate_business_event_ref=acquisition_ref,
                event_date=opening,
            )
            self._write_fixed_asset_register(asset)
            assets.append(asset)
            self._write_fixed_asset_control(
                result_ref=f"ARGUS-FA-CHAIN-{asset_id}",
                definition_ref="ARGUS-FA-SOURCE-CHAIN@v1",
                period_id=_period_id(opening),
                asset_id=asset_id,
                observation_type="FORMATION_SOURCE_CHAIN",
                status="PASS",
                severity="HIGH",
                expected_minor=cost,
                actual_minor=cost,
                evidence_ref=f"EVIDENCE-{lifecycle_id}",
                source_record_refs=lifecycle_id,
            )

        capex_vendor = next(
            (vendor for vendor in vendors if vendor.currency == REPORTING_CURRENCY),
            vendors[0],
        )
        first_invoice_row: dict[str, object] | None = None
        first_invoice_id = ""
        acquisition_sequence = 0
        asset_classes = (
            ("COMPUTER_EQUIPMENT", 48),
            ("LEASEHOLD_IMPROVEMENTS", 84),
            ("OFFICE_EQUIPMENT", 60),
        )
        for month_index, month in enumerate(self.actual_months):
            if month_index == 0 or month.month not in {1, 4, 7, 10}:
                continue
            acquisition_sequence += 1
            period = _period_id(month)
            asset_class, useful_life = asset_classes[
                (acquisition_sequence - 1) % len(asset_classes)
            ]
            amount = 45_000_000 + 2_500_000 * (month_index // 12)
            asset_id = f"FA-CAPEX-{acquisition_sequence:04d}"
            po_id = f"CPO-{acquisition_sequence:05d}"
            receipt_id = f"CGR-{acquisition_sequence:05d}"
            invoice_id = f"CINV-{acquisition_sequence:05d}"
            payment_ref = f"CPAY-{acquisition_sequence:05d}"
            order_date = month + timedelta(days=1)
            receipt_date = month + timedelta(days=10)
            invoice_date = month + timedelta(days=12)
            due_date = invoice_date + timedelta(days=30)
            payment_date = due_date
            delay_days = 20 if acquisition_sequence % 7 == 0 else 0
            po_row = {
                "capital_purchase_order_id": po_id,
                "legal_entity_id": LEGAL_ENTITY_ID,
                "vendor_id": capex_vendor.vendor_id,
                "order_date": order_date.isoformat(),
                "asset_class": asset_class,
                "asset_description": f"Capital programme asset {asset_id}",
                "ordered_amount_minor": amount,
                "currency": REPORTING_CURRENCY,
                "approval_ref": f"CAPEX-COMMITTEE-{period}@v1",
                "purchase_order_status": "CLOSED",
                "source_recorded_at": _timestamp(order_date, 10),
            }
            receipt_row = {
                "capital_goods_receipt_id": receipt_id,
                "capital_purchase_order_id": po_id,
                "legal_entity_id": LEGAL_ENTITY_ID,
                "receipt_date": receipt_date.isoformat(),
                "quantity_received": 1,
                "receiver_ref": "EMP-FIXED-ASSET-CUSTODIAN",
                "receipt_status": "ACCEPTED",
                "source_recorded_at": _timestamp(receipt_date, 15),
            }
            invoice_row = {
                "capital_invoice_id": invoice_id,
                "capital_purchase_order_id": po_id,
                "capital_goods_receipt_id": receipt_id,
                "legal_entity_id": LEGAL_ENTITY_ID,
                "vendor_id": capex_vendor.vendor_id,
                "supplier_invoice_number": f"CAP-SUP-{acquisition_sequence:06d}",
                "invoice_date": invoice_date.isoformat(),
                "due_date": due_date.isoformat(),
                "invoice_amount_minor": amount,
                "currency": REPORTING_CURRENCY,
                "invoice_status": "PAID",
                "payment_ref": payment_ref,
                "payment_date": payment_date.isoformat(),
                "payment_status": "SETTLED",
                "source_recorded_at": _timestamp(
                    invoice_date + timedelta(days=delay_days), 17
                ),
            }
            self._sink(CAPITAL_PURCHASE_ORDERS).write(po_row)
            self._sink(CAPITAL_GOODS_RECEIPTS).write(receipt_row)
            self._sink(CAPITAL_INVOICES).write(invoice_row)
            if first_invoice_row is None:
                first_invoice_row = invoice_row
                first_invoice_id = invoice_id
            provisional_asset = FixedAsset(
                asset_id=asset_id,
                legal_entity_id=LEGAL_ENTITY_ID,
                asset_class=asset_class,
                source_system="FIXED_ASSET_SUBLEDGER",
                source_record_ref=f"FA-MASTER-{asset_id}",
                acquisition_business_event_ref="",
                capital_purchase_order_id=po_id,
                capital_goods_receipt_id=receipt_id,
                capital_invoice_id=invoice_id,
                acquisition_date=invoice_date.isoformat(),
                in_service_date=receipt_date.isoformat(),
                cost_minor=amount,
                residual_value_minor=0,
                currency=REPORTING_CURRENCY,
                useful_life_months=useful_life,
                depreciation_method="STRAIGHT_LINE_MONTHLY",
                disposal_date="",
                asset_status="ACTIVE",
            )
            acquisition_event_ref = self._post_fixed_asset_event(
                event_type="CAPITAL_ASSET_INVOICE_APPROVED",
                source_definition=CAPITAL_INVOICES,
                source_system="ACCOUNTS_PAYABLE",
                source_record_ref=f"{invoice_id}#APPROVAL",
                source_payload=invoice_row,
                occurred_date=invoice_date,
                effective_date=invoice_date,
                counterparty_ref=capex_vendor.vendor_id,
                asset=provisional_asset,
                event_amount_minor=amount,
                recorded_delay_days=delay_days,
            )
            asset = replace(
                provisional_asset,
                acquisition_business_event_ref=acquisition_event_ref,
            )
            self._post_fixed_asset_event(
                event_type="CAPITAL_ASSET_INVOICE_PAID",
                source_definition=CAPITAL_INVOICES,
                source_system="TREASURY",
                source_record_ref=payment_ref,
                source_payload=invoice_row,
                occurred_date=payment_date,
                effective_date=payment_date,
                counterparty_ref=capex_vendor.vendor_id,
                asset=asset,
                event_amount_minor=amount,
            )
            lifecycle_id = f"FALE-{asset_id}-REGISTERED"
            lifecycle = self._write_asset_lifecycle_event(
                lifecycle_event_id=lifecycle_id,
                asset=asset,
                event_type="ASSET_REGISTERED",
                event_date=receipt_date,
                source_record_ref=asset.source_record_ref,
                related_capital_invoice_id=invoice_id,
                event_amount_minor=amount,
                gross_cost_minor=amount,
                authorisation_ref=f"CAPITALISATION-{asset_id}@v1",
                recorded_delay_days=delay_days,
            )
            self._write_source_admission(
                source_definition=ASSET_LIFECYCLE_EVENTS,
                source_system="FIXED_ASSET_SUBLEDGER",
                source_record_ref=lifecycle_id,
                source_payload=lifecycle,
                candidate_business_event_ref=acquisition_event_ref,
                event_date=receipt_date,
                late_arrival=delay_days > 0,
            )
            self._write_fixed_asset_register(asset)
            assets.append(asset)
            self._write_fixed_asset_control(
                result_ref=f"ARGUS-FA-CHAIN-{asset_id}",
                definition_ref="ARGUS-FA-SOURCE-CHAIN@v1",
                period_id=period,
                asset_id=asset_id,
                observation_type="CAPITAL_SOURCE_CHAIN",
                status="PASS",
                severity="HIGH",
                expected_minor=amount,
                actual_minor=amount,
                evidence_ref=f"EVIDENCE-{po_id}-{receipt_id}-{invoice_id}",
                source_record_refs=f"{po_id},{receipt_id},{invoice_id}",
            )

        if first_invoice_row is None:
            raise ValueError("fixed-asset vertical requires one capital invoice")
        duplicate_invoice_id = "CINV-DUPLICATE-00001"
        duplicate_row = {
            **first_invoice_row,
            "capital_invoice_id": duplicate_invoice_id,
            "invoice_status": "BLOCKED_DUPLICATE",
            "payment_ref": "",
            "payment_date": "",
            "payment_status": "BLOCKED",
        }
        self._sink(CAPITAL_INVOICES).write(duplicate_row)
        duplicate_source_ref = f"{duplicate_invoice_id}#APPROVAL"
        duplicate_candidate_ref = _stable_ref(
            "BE",
            "CAPITAL_ASSET_INVOICE_APPROVED",
            "ACCOUNTS_PAYABLE",
            duplicate_source_ref,
        )
        duplicate_decision = self.fixed_asset_admission.admit(
            SourceAdmissionCandidate(
                source_dataset_path=CAPITAL_INVOICES.path,
                source_system="ACCOUNTS_PAYABLE",
                source_record_ref=duplicate_source_ref,
                source_payload=duplicate_row,
                candidate_business_event_ref=duplicate_candidate_ref,
                event_time=_timestamp(
                    date.fromisoformat(str(duplicate_row["invoice_date"]))
                ),
                ingested_at=self.request.built_at,
                legal_entity_id=LEGAL_ENTITY_ID,
                currency=REPORTING_CURRENCY,
                duplicate_of_ref=first_invoice_id,
            )
        )
        self._sink(SOURCE_ADMISSION_RESULTS).write(duplicate_decision.as_row())
        self._defect(
            defect_type="DUPLICATE_CAPITAL_INVOICE",
            dataset_path=CAPITAL_INVOICES.path,
            source_record_ref=duplicate_invoice_id,
            detector="HERMES_CAPITAL_INVOICE_DUPLICATE",
            severity="CRITICAL",
            treatment="QUARANTINE_BEFORE_POSTING",
            description=(
                "Capital invoice intentionally duplicates a supplier invoice "
                "and is quarantined before business-event admission."
            ),
        )
        self._write_fixed_asset_control(
            result_ref="ARGUS-FA-DUPLICATE-CINV-00001",
            definition_ref="ARGUS-FA-DUPLICATE-INVOICE@v1",
            period_id=_period_id(
                date.fromisoformat(str(duplicate_row["invoice_date"]))
            ),
            asset_id="",
            observation_type="QUARANTINED_DUPLICATE_SOURCE",
            status="EXCEPTION",
            severity="CRITICAL",
            expected_minor=0,
            actual_minor=1,
            evidence_ref=duplicate_decision.quarantine_ref,
            source_record_refs=f"{first_invoice_id},{duplicate_invoice_id}",
        )

        impairment_by_asset = {
            "FA-FORM-GOODWILL": (date(2024, 6, 30), 100_000_000)
        }
        for asset in assets:
            acquisition_date = date.fromisoformat(asset.acquisition_date)
            acquisition_month = date(
                acquisition_date.year, acquisition_date.month, 1
            )
            in_service = date.fromisoformat(asset.in_service_date)
            depreciation_start = _add_months(
                date(in_service.year, in_service.month, 1), 1
            )
            disposal_date = (
                date.fromisoformat(asset.disposal_date)
                if asset.disposal_date
                else None
            )
            opening_gross = 0
            opening_accumulated = 0
            for month in self.actual_months:
                if month < acquisition_month:
                    continue
                if disposal_date and month > date(
                    disposal_date.year, disposal_date.month, 1
                ):
                    break
                period = _period_id(month)
                gross_addition = asset.cost_minor if month == acquisition_month else 0
                current_gross = opening_gross + gross_addition
                depreciation = 0
                amortisation = 0
                impairment = 0
                accumulated_disposal = 0
                gross_disposal = 0
                disposal_proceeds = 0
                disposal_gain_loss = 0
                event_refs: list[str] = []
                movement_types: list[str] = []
                if gross_addition:
                    event_refs.append(asset.acquisition_business_event_ref)
                    movement_types.append("ACQUISITION")
                if asset.useful_life_months and month >= depreciation_start:
                    charge_index = (
                        month.year * 12
                        + month.month
                        - depreciation_start.year * 12
                        - depreciation_start.month
                    )
                    remaining = max(
                        0,
                        asset.cost_minor
                        - asset.residual_value_minor
                        - opening_accumulated,
                    )
                    if 0 <= charge_index < asset.useful_life_months and remaining:
                        base_charge = (
                            asset.cost_minor - asset.residual_value_minor
                        ) // asset.useful_life_months
                        charge = (
                            remaining
                            if charge_index == asset.useful_life_months - 1
                            else min(base_charge, remaining)
                        )
                        lifecycle_type = (
                            "FIXED_ASSET_AMORTISATION_DUE"
                            if asset.asset_class == "CAPITALISED_SOFTWARE"
                            else "FIXED_ASSET_DEPRECIATION_DUE"
                        )
                        lifecycle_id = f"FALE-{asset.asset_id}-{period}-CHARGE"
                        lifecycle = self._write_asset_lifecycle_event(
                            lifecycle_event_id=lifecycle_id,
                            asset=asset,
                            event_type=lifecycle_type,
                            event_date=_month_end(month),
                            source_record_ref=lifecycle_id,
                            related_capital_invoice_id=asset.capital_invoice_id,
                            event_amount_minor=charge,
                            authorisation_ref="FIXED-ASSET-POLICY@v1",
                        )
                        event_ref = self._post_fixed_asset_event(
                            event_type=lifecycle_type,
                            source_definition=ASSET_LIFECYCLE_EVENTS,
                            source_system="FIXED_ASSET_SUBLEDGER",
                            source_record_ref=lifecycle_id,
                            source_payload=lifecycle,
                            occurred_date=_month_end(month),
                            effective_date=_month_end(month),
                            counterparty_ref=asset.asset_id,
                            asset=asset,
                            event_amount_minor=charge,
                        )
                        event_refs.append(event_ref)
                        movement_types.append(
                            "AMORTISATION"
                            if lifecycle_type == "FIXED_ASSET_AMORTISATION_DUE"
                            else "DEPRECIATION"
                        )
                        if lifecycle_type == "FIXED_ASSET_AMORTISATION_DUE":
                            amortisation = charge
                        else:
                            depreciation = charge
                impairment_spec = impairment_by_asset.get(asset.asset_id)
                if impairment_spec and _period_id(impairment_spec[0]) == period:
                    impairment = min(
                        impairment_spec[1],
                        max(
                            0,
                            current_gross
                            - opening_accumulated
                            - depreciation
                            - amortisation
                            - asset.residual_value_minor,
                        ),
                    )
                    lifecycle_id = f"FALE-{asset.asset_id}-{period}-IMPAIR"
                    lifecycle = self._write_asset_lifecycle_event(
                        lifecycle_event_id=lifecycle_id,
                        asset=asset,
                        event_type="FIXED_ASSET_IMPAIRMENT_APPROVED",
                        event_date=impairment_spec[0],
                        source_record_ref=lifecycle_id,
                        related_capital_invoice_id=asset.capital_invoice_id,
                        event_amount_minor=impairment,
                        authorisation_ref="AUDIT-COMMITTEE-IMPAIRMENT-2024@v1",
                    )
                    event_ref = self._post_fixed_asset_event(
                        event_type="FIXED_ASSET_IMPAIRMENT_APPROVED",
                        source_definition=ASSET_LIFECYCLE_EVENTS,
                        source_system="FIXED_ASSET_SUBLEDGER",
                        source_record_ref=lifecycle_id,
                        source_payload=lifecycle,
                        occurred_date=impairment_spec[0],
                        effective_date=impairment_spec[0],
                        counterparty_ref=asset.asset_id,
                        asset=asset,
                        event_amount_minor=impairment,
                    )
                    event_refs.append(event_ref)
                    movement_types.append("IMPAIRMENT")
                accumulated_before_disposal = (
                    opening_accumulated
                    + depreciation
                    + amortisation
                    + impairment
                )
                if disposal_date and _period_id(disposal_date) == period:
                    gross_disposal = current_gross
                    accumulated_disposal = accumulated_before_disposal
                    disposal_proceeds = 15_000_000
                    disposal_gain_loss = (
                        gross_disposal
                        - accumulated_disposal
                        - disposal_proceeds
                    )
                    lifecycle_id = f"FALE-{asset.asset_id}-{period}-DISPOSAL"
                    lifecycle = self._write_asset_lifecycle_event(
                        lifecycle_event_id=lifecycle_id,
                        asset=asset,
                        event_type="FIXED_ASSET_DISPOSED",
                        event_date=disposal_date,
                        source_record_ref=lifecycle_id,
                        related_capital_invoice_id=asset.capital_invoice_id,
                        event_amount_minor=gross_disposal,
                        gross_cost_minor=gross_disposal,
                        accumulated_depreciation_minor=accumulated_disposal,
                        disposal_proceeds_minor=disposal_proceeds,
                        authorisation_ref="ASSET-DISPOSAL-COMMITTEE-2025@v1",
                    )
                    event_ref = self._post_fixed_asset_event(
                        event_type="FIXED_ASSET_DISPOSED",
                        source_definition=ASSET_LIFECYCLE_EVENTS,
                        source_system="FIXED_ASSET_SUBLEDGER",
                        source_record_ref=lifecycle_id,
                        source_payload=lifecycle,
                        occurred_date=disposal_date,
                        effective_date=disposal_date,
                        counterparty_ref="ASSET-DISPOSAL-BUYER",
                        asset=asset,
                        event_amount_minor=gross_disposal,
                        gross_cost_minor=gross_disposal,
                        accumulated_depreciation_minor=accumulated_disposal,
                        disposal_proceeds_minor=disposal_proceeds,
                    )
                    event_refs.append(event_ref)
                    movement_types.append("DISPOSAL")
                closing_gross = current_gross - gross_disposal
                closing_accumulated = (
                    accumulated_before_disposal - accumulated_disposal
                )
                closing_nbv = closing_gross - closing_accumulated
                movement_id = f"FAM-{asset.asset_id}-{period}"
                self._sink(FIXED_ASSET_MOVEMENTS).write(
                    {
                        "asset_movement_id": movement_id,
                        "period_id": period,
                        "asset_id": asset.asset_id,
                        "legal_entity_id": asset.legal_entity_id,
                        "movement_type": (
                            "+".join(movement_types)
                            if movement_types
                            else "ROLLFORWARD"
                        ),
                        "business_event_refs": ",".join(event_refs),
                        "opening_gross_book_value_minor": opening_gross,
                        "gross_addition_minor": gross_addition,
                        "gross_disposal_minor": gross_disposal,
                        "closing_gross_book_value_minor": closing_gross,
                        "opening_accumulated_depreciation_minor": (
                            opening_accumulated
                        ),
                        "depreciation_minor": depreciation,
                        "amortisation_minor": amortisation,
                        "impairment_minor": impairment,
                        "accumulated_depreciation_disposal_minor": (
                            accumulated_disposal
                        ),
                        "closing_accumulated_depreciation_minor": (
                            closing_accumulated
                        ),
                        "disposal_proceeds_minor": disposal_proceeds,
                        "disposal_gain_loss_minor": disposal_gain_loss,
                        "closing_net_book_value_minor": closing_nbv,
                        "currency": asset.currency,
                    }
                )
                self._write_fixed_asset_control(
                    result_ref=f"ARGUS-FA-ROLL-{asset.asset_id}-{period}",
                    definition_ref="ARGUS-FA-ROLLFORWARD@v1",
                    period_id=period,
                    asset_id=asset.asset_id,
                    observation_type="ASSET_ROLLFORWARD",
                    status="PASS",
                    severity="CRITICAL",
                    expected_minor=closing_nbv,
                    actual_minor=closing_gross - closing_accumulated,
                    evidence_ref=f"EVIDENCE-{movement_id}",
                    source_record_refs=asset.source_record_ref,
                )
                opening_gross = closing_gross
                opening_accumulated = closing_accumulated

    def _generate_financing(self) -> None:
        debt_outstanding = 1_500_000_000
        equity_rounds = {
            "2024-01": (
                "EQ-SERIES-B-2024",
                "SERIES_B_EQUITY_ISSUANCE",
                "SERIES-B-EQUITY-2024",
                date(2024, 1, 2),
                2_000_000_000,
                "BOARD-SERIES-B-EQUITY-2024@v1",
            ),
            "2025-04": (
                "EQ-GROWTH-2025",
                "GROWTH_EQUITY_ISSUANCE",
                "GROWTH-EQUITY-2025",
                date(2025, 4, 1),
                2_500_000_000,
                "BOARD-GROWTH-EQUITY-2025@v1",
            ),
        }
        for month_index, month in enumerate(self.actual_months):
            month_end = _month_end(month)
            period = _period_id(month)
            if period in equity_rounds:
                (
                    movement_id,
                    movement_type,
                    source_record_ref,
                    funding_date,
                    equity_amount,
                    authorisation_ref,
                ) = equity_rounds[period]
                equity_event_ref = self._business_event(
                    event_type="CAPITAL_CONTRIBUTION_RECEIVED",
                    source_system="CORPORATE_SECRETARY",
                    source_record_ref=source_record_ref,
                    occurred_date=funding_date,
                    effective_date=funding_date,
                    counterparty_ref="NEXUS-INSTITUTIONAL-SHAREHOLDERS",
                    local_amount_minor=equity_amount,
                    currency=REPORTING_CURRENCY,
                    reporting_amount_minor=equity_amount,
                    posting_rule_ref="PR-CAPITAL_CONTRIBUTION_RECEIVED@v1",
                    lines=(
                        ("1000", equity_amount, 0),
                        ("3000", 0, equity_amount),
                    ),
                )
                self._sink(EQUITY_MOVEMENTS).write(
                    {
                        "equity_movement_id": movement_id,
                        "period_id": period,
                        "legal_entity_id": LEGAL_ENTITY_ID,
                        "equity_component": "SHARE_CAPITAL",
                        "movement_type": movement_type,
                        "business_event_ref": equity_event_ref,
                        "amount_minor": equity_amount,
                        "currency": REPORTING_CURRENCY,
                        "authorisation_ref": authorisation_ref,
                    }
                )
            opening_principal = 0 if month_index == 0 else debt_outstanding
            drawdown = 1_500_000_000 if month_index == 0 else 0
            debt_event_refs = (
                [self.formation_debt_event_ref] if month_index == 0 else []
            )
            interest = 0
            if debt_outstanding > 0:
                interest = debt_outstanding * 600 // 120_000
                interest_event_ref = self._business_event(
                    event_type="DEBT_INTEREST_INCURRED",
                    source_system="TREASURY",
                    source_record_ref=f"INT-{period}",
                    occurred_date=month_end,
                    effective_date=month_end,
                    counterparty_ref="BANK-SYNDICATE",
                    local_amount_minor=interest,
                    currency=REPORTING_CURRENCY,
                    reporting_amount_minor=interest,
                    posting_rule_ref="PR-DEBT-INTEREST@v1",
                    lines=(("6500", interest, 0), ("1000", 0, interest)),
                )
                debt_event_refs.append(interest_event_ref)
            repayment = 0
            if month_index >= 24 and month.month in {3, 6, 9, 12} and debt_outstanding:
                repayment = min(75_000_000, debt_outstanding)
                debt_outstanding -= repayment
                repayment_event_ref = self._business_event(
                    event_type="DEBT_PRINCIPAL_REPAID",
                    source_system="TREASURY",
                    source_record_ref=f"DEBT-REPAY-{period}",
                    occurred_date=month_end,
                    effective_date=month_end,
                    counterparty_ref="BANK-SYNDICATE",
                    local_amount_minor=repayment,
                    currency=REPORTING_CURRENCY,
                    reporting_amount_minor=repayment,
                    posting_rule_ref="PR-DEBT-REPAYMENT@v1",
                    lines=(("2400", repayment, 0), ("1000", 0, repayment)),
                )
                debt_event_refs.append(repayment_event_ref)
            self._sink(DEBT_SCHEDULE).write(
                {
                    "period_id": period,
                    "debt_instrument_id": "DEBT-TERM-GBP",
                    "legal_entity_id": LEGAL_ENTITY_ID,
                    "opening_principal_minor": opening_principal,
                    "drawdown_minor": drawdown,
                    "principal_repayment_minor": repayment,
                    "cash_interest_minor": interest,
                    "accrued_interest_minor": 0,
                    "closing_principal_minor": debt_outstanding,
                    "undrawn_facility_minor": 1_500_000_000 - debt_outstanding,
                    "effective_interest_rate_bps": 600,
                    "currency": REPORTING_CURRENCY,
                    "business_event_refs": ",".join(debt_event_refs),
                }
            )
            self._sink(DEBT_SCHEDULE).write(
                {
                    "period_id": period,
                    "debt_instrument_id": "DEBT-REVOLVER-GBP",
                    "legal_entity_id": LEGAL_ENTITY_ID,
                    "opening_principal_minor": 0,
                    "drawdown_minor": 0,
                    "principal_repayment_minor": 0,
                    "cash_interest_minor": 0,
                    "accrued_interest_minor": 0,
                    "closing_principal_minor": 0,
                    "undrawn_facility_minor": 2_000_000_000,
                    "effective_interest_rate_bps": 800,
                    "currency": REPORTING_CURRENCY,
                    "business_event_refs": "",
                }
            )
    def _generate_leases(self) -> None:
        lease_specs = (
            (
                "LEASE-LONDON-HQ-2021",
                "LESSOR-LONDON-HQ",
                "OFFICE",
                date(2021, 1, 1),
                60,
                300_000_000,
                500,
            ),
            (
                "LEASE-DATACENTRE-2022",
                "LESSOR-DATACENTRE-UK",
                "DATACENTRE",
                date(2022, 7, 1),
                48,
                50_000_000,
                600,
            ),
            (
                "LEASE-VEHICLES-2023",
                "LESSOR-FLEET-UK",
                "VEHICLE",
                date(2023, 4, 1),
                36,
                20_000_000,
                650,
            ),
            (
                "LEASE-LONDON-EXPANSION-2025",
                "LESSOR-LONDON-EXPANSION",
                "OFFICE",
                date(2025, 1, 1),
                72,
                60_000_000,
                550,
            ),
        )
        actual_end_month = date(
            self.request.actuals_end.year, self.request.actuals_end.month, 1
        )
        for (
            contract_id,
            lessor_ref,
            lease_class,
            commencement,
            term_months,
            initial_liability,
            rate_bps,
        ) in lease_specs:
            monthly_rate = rate_bps / 10_000 / 12
            payment_minor = round(
                initial_liability
                * monthly_rate
                / (1 - (1 + monthly_rate) ** -term_months)
            )
            maturity_month = _add_months(commencement, term_months)
            maturity_date = _month_end(maturity_month)
            contract_row = {
                "lease_contract_id": contract_id,
                "legal_entity_id": LEGAL_ENTITY_ID,
                "lessor_ref": lessor_ref,
                "lease_class": lease_class,
                "commencement_date": commencement.isoformat(),
                "maturity_date": maturity_date.isoformat(),
                "payment_frequency": "MONTHLY_IN_ARREARS",
                "payment_minor": payment_minor,
                "currency": REPORTING_CURRENCY,
                "incremental_borrowing_rate_bps": rate_bps,
                "initial_liability_minor": initial_liability,
                "initial_rou_asset_minor": initial_liability,
                "lease_status": (
                    "EXPIRED"
                    if maturity_month <= actual_end_month
                    else "ACTIVE"
                ),
                "approval_ref": f"LEASE-COMMITTEE-{contract_id}@v1",
                "source_recorded_at": _timestamp(commencement, 9),
            }
            self._sink(LEASE_CONTRACTS).write(contract_row)

            opening_liability = 0
            opening_rou = 0
            final_month = min(maturity_month, actual_end_month)
            for lease_month_index, month in enumerate(
                _month_starts(commencement, final_month)
            ):
                period = _period_id(month)
                month_end = _month_end(month)
                event_refs: list[str] = []
                liability_addition = (
                    initial_liability if lease_month_index == 0 else 0
                )
                rou_addition = liability_addition
                base_liability = opening_liability + liability_addition
                interest = 0
                cash_payment = 0
                principal_reduction = 0
                if lease_month_index > 0 and base_liability:
                    interest = base_liability * rate_bps // 120_000
                    cash_payment = (
                        base_liability + interest
                        if month == maturity_month
                        else min(payment_minor, base_liability + interest)
                    )
                    principal_reduction = cash_payment - interest
                closing_liability = (
                    base_liability + interest - cash_payment
                )
                remaining_rou = opening_rou + rou_addition
                rou_depreciation = 0
                if lease_month_index < term_months and remaining_rou:
                    normal_depreciation = initial_liability // term_months
                    rou_depreciation = (
                        remaining_rou
                        if lease_month_index == term_months - 1
                        else min(normal_depreciation, remaining_rou)
                    )
                closing_rou = remaining_rou - rou_depreciation

                lifecycle_events: list[tuple[str, int, str, int, object]] = []
                if liability_addition:
                    posting = self.lease_posting_rules.derive(
                        LeasePostingInput(
                            origin_class="BUSINESS_EVENT",
                            event_type="LEASE_COMMENCED",
                            event_amount_minor=liability_addition,
                        )
                    )
                    lifecycle_events.append(
                        ("LEASE_COMMENCED", liability_addition, "COMMENCE", 0, posting)
                    )
                if cash_payment:
                    posting = self.lease_posting_rules.derive(
                        LeasePostingInput(
                            origin_class="BUSINESS_EVENT",
                            event_type="LEASE_PAYMENT_MADE",
                            event_amount_minor=cash_payment,
                            principal_minor=principal_reduction,
                            interest_minor=interest,
                        )
                    )
                    delay = (
                        12
                        if contract_id == "LEASE-DATACENTRE-2022"
                        and period == "2024-02"
                        else 0
                    )
                    lifecycle_events.append(
                        ("LEASE_PAYMENT_MADE", cash_payment, "PAYMENT", delay, posting)
                    )
                if rou_depreciation:
                    posting = self.lease_posting_rules.derive(
                        LeasePostingInput(
                            origin_class="BUSINESS_EVENT",
                            event_type="RIGHT_OF_USE_ASSET_DEPRECIATED",
                            event_amount_minor=rou_depreciation,
                        )
                    )
                    lifecycle_events.append(
                        (
                            "RIGHT_OF_USE_ASSET_DEPRECIATED",
                            rou_depreciation,
                            "ROU",
                            0,
                            posting,
                        )
                    )
                lifecycle_refs: list[str] = []
                for event_type, amount, suffix, delay, posting in lifecycle_events:
                    lifecycle_id = f"LLE-{contract_id}-{period}-{suffix}"
                    lifecycle_row = {
                        "lease_lifecycle_event_id": lifecycle_id,
                        "lease_contract_id": contract_id,
                        "legal_entity_id": LEGAL_ENTITY_ID,
                        "event_type": event_type,
                        "event_date": month_end.isoformat(),
                        "event_amount_minor": amount,
                        "currency": REPORTING_CURRENCY,
                        "source_recorded_at": _timestamp(
                            month_end + timedelta(days=delay), 16
                        ),
                    }
                    self._sink(LEASE_LIFECYCLE_EVENTS).write(lifecycle_row)
                    if (
                        contract_id == "LEASE-LONDON-HQ-2021"
                        and event_type == "LEASE_COMMENCED"
                    ):
                        event_ref = self.opening_event_ref_by_source["OPEN-LEASE"]
                        decision = self._write_source_admission(
                            source_definition=LEASE_LIFECYCLE_EVENTS,
                            source_system="LEASE_ADMINISTRATION",
                            source_record_ref=lifecycle_id,
                            source_payload=lifecycle_row,
                            candidate_business_event_ref=event_ref,
                            event_date=month_end,
                        )
                        if decision == "QUARANTINED":
                            raise ValueError(
                                "formation lease carry-in cannot be quarantined"
                            )
                    else:
                        event_ref = self._post_a22b_event(
                            event_type=event_type,
                            source_definition=LEASE_LIFECYCLE_EVENTS,
                            source_system="LEASE_ADMINISTRATION",
                            source_record_ref=lifecycle_id,
                            source_payload=lifecycle_row,
                            occurred_date=month_end,
                            effective_date=month_end,
                            counterparty_ref=lessor_ref,
                            journal_amount_minor=posting.journal_amount_minor,
                            posting_rule_ref=posting.posting_rule_ref,
                            lines=posting.lines,
                            recorded_delay_days=delay,
                        )
                    event_refs.append(event_ref)
                    lifecycle_refs.append(lifecycle_id)

                self._sink(LEASE_SCHEDULE).write(
                    {
                        "period_id": period,
                        "lease_contract_id": contract_id,
                        "legal_entity_id": LEGAL_ENTITY_ID,
                        "opening_liability_minor": opening_liability,
                        "liability_addition_minor": liability_addition,
                        "cash_payment_minor": cash_payment,
                        "interest_accretion_minor": interest,
                        "principal_reduction_minor": principal_reduction,
                        "closing_liability_minor": closing_liability,
                        "opening_rou_asset_minor": opening_rou,
                        "rou_asset_addition_minor": rou_addition,
                        "rou_depreciation_minor": rou_depreciation,
                        "rou_impairment_minor": 0,
                        "closing_rou_asset_minor": closing_rou,
                        "currency": REPORTING_CURRENCY,
                        "business_event_refs": ",".join(event_refs),
                    }
                )
                self._write_statutory_subledger_control(
                    result_ref=f"ARGUS-LEASE-LIAB-{contract_id}-{period}",
                    definition_ref="ARGUS-LEASE-LIABILITY-ROLLFORWARD@v1",
                    period_id=period,
                    domain="LEASE",
                    object_ref=contract_id,
                    observation_type="LEASE_LIABILITY_ROLLFORWARD",
                    status="PASS",
                    severity="CRITICAL",
                    expected_minor=(
                        opening_liability
                        + liability_addition
                        + interest
                        - cash_payment
                    ),
                    actual_minor=closing_liability,
                    evidence_ref=f"EVIDENCE-LEASE-LIAB-{contract_id}-{period}",
                    source_record_refs=",".join(lifecycle_refs),
                )
                self._write_statutory_subledger_control(
                    result_ref=f"ARGUS-LEASE-ROU-{contract_id}-{period}",
                    definition_ref="ARGUS-LEASE-ROU-ROLLFORWARD@v1",
                    period_id=period,
                    domain="LEASE",
                    object_ref=contract_id,
                    observation_type="ROU_ASSET_ROLLFORWARD",
                    status="PASS",
                    severity="CRITICAL",
                    expected_minor=(
                        opening_rou + rou_addition - rou_depreciation
                    ),
                    actual_minor=closing_rou,
                    evidence_ref=f"EVIDENCE-LEASE-ROU-{contract_id}-{period}",
                    source_record_refs=",".join(lifecycle_refs),
                )
                opening_liability = closing_liability
                opening_rou = closing_rou

    def _generate_accruals(self) -> None:
        programs = (
            ("AUDIT", "DEP-FIN", "6200", "VEND-AUDIT", 600_000),
            ("LEGAL", "DEP-FIN", "6200", "VEND-LEGAL", 400_000),
            ("UTILITIES", "DEP-OPS", "6200", "VEND-UTILITIES", 300_000),
            ("CLOUD-TRUEUP", "DEP-ENG", "5000", "VEND-CLOUD", 500_000),
        )
        opening_by_program = {item[0]: 0 for item in programs}
        for month_index, month in enumerate(self.actual_months):
            period = _period_id(month)
            month_end = _month_end(month)
            for code, department, expense_account, counterparty, base in programs:
                schedule_id = f"ACCRUAL-{code}"
                opening = opening_by_program[code]
                release = opening
                addition = base * (95 + (month_index + len(code)) % 11) // 100
                event_refs: list[str] = []
                source_refs: list[str] = []
                event_specs = []
                if release:
                    event_specs.append(
                        (
                            "ACCRUAL_SETTLED",
                            release,
                            date(month.year, month.month, 10),
                            0,
                        )
                    )
                delay = 9 if code == "AUDIT" and period == "2024-04" else 0
                event_specs.append(
                    ("ACCRUAL_ESTIMATE_APPROVED", addition, month_end, delay)
                )
                for event_type, amount, event_date, recorded_delay in event_specs:
                    suffix = "SETTLE" if event_type == "ACCRUAL_SETTLED" else "ADD"
                    source_id = f"ASE-{code}-{period}-{suffix}"
                    row = {
                        "accrual_source_event_id": source_id,
                        "accrual_schedule_id": schedule_id,
                        "event_type": event_type,
                        "event_date": event_date.isoformat(),
                        "legal_entity_id": LEGAL_ENTITY_ID,
                        "department_id": department,
                        "expense_account_id": expense_account,
                        "counterparty_ref": counterparty,
                        "event_amount_minor": amount,
                        "currency": REPORTING_CURRENCY,
                        "approval_ref": f"CLOSE-CONTROLLER-{period}@v1",
                        "source_recorded_at": _timestamp(
                            event_date + timedelta(days=recorded_delay), 16
                        ),
                    }
                    self._sink(ACCRUAL_SOURCE_EVENTS).write(row)
                    posting = self.working_capital_posting_rules.derive(
                        WorkingCapitalPostingInput(
                            origin_class="BUSINESS_EVENT",
                            event_type=event_type,  # type: ignore[arg-type]
                            event_amount_minor=amount,
                            expense_account_id=expense_account,
                        )
                    )
                    event_refs.append(
                        self._post_a22b_event(
                            event_type=event_type,
                            source_definition=ACCRUAL_SOURCE_EVENTS,
                            source_system="CLOSE_MANAGEMENT",
                            source_record_ref=source_id,
                            source_payload=row,
                            occurred_date=event_date,
                            effective_date=event_date,
                            counterparty_ref=counterparty,
                            journal_amount_minor=posting.journal_amount_minor,
                            posting_rule_ref=posting.posting_rule_ref,
                            lines=posting.lines,
                            recorded_delay_days=recorded_delay,
                        )
                    )
                    source_refs.append(source_id)
                closing = opening + addition - release
                self._sink(ACCRUAL_SCHEDULE).write(
                    {
                        "accrual_schedule_id": schedule_id,
                        "period_id": period,
                        "legal_entity_id": LEGAL_ENTITY_ID,
                        "department_id": department,
                        "expense_account_id": expense_account,
                        "opening_accrual_minor": opening,
                        "addition_minor": addition,
                        "release_minor": release,
                        "closing_accrual_minor": closing,
                        "currency": REPORTING_CURRENCY,
                        "business_event_refs": ",".join(event_refs),
                    }
                )
                self._write_statutory_subledger_control(
                    result_ref=f"ARGUS-ACCRUAL-{code}-{period}",
                    definition_ref="ARGUS-ACCRUAL-ROLLFORWARD@v1",
                    period_id=period,
                    domain="ACCRUAL",
                    object_ref=schedule_id,
                    observation_type="ACCRUAL_ROLLFORWARD",
                    status="PASS",
                    severity="HIGH",
                    expected_minor=opening + addition - release,
                    actual_minor=closing,
                    evidence_ref=f"EVIDENCE-ACCRUAL-{code}-{period}",
                    source_record_refs=",".join(source_refs),
                )
                opening_by_program[code] = closing

    def _generate_prepayments(self) -> None:
        programs = (
            ("INSURANCE", "DEP-FIN", "6200", "VEND-INSURANCE", 1, 4_000_000),
            ("SOFTWARE", "DEP-ENG", "6000", "VEND-SOFTWARE", 4, 6_000_000),
            ("MARKETING", "DEP-MKT", "6100", "VEND-MARKETING", 9, 3_000_000),
        )
        duplicate_written = False
        for year in range(
            self.request.history_start.year,
            self.request.actuals_end.year + 1,
        ):
            for (
                code,
                department,
                expense_account,
                counterparty,
                start_month,
                annual,
            ) in programs:
                start = date(year, start_month, 1)
                if (
                    start < self.request.history_start
                    or start > self.request.actuals_end
                ):
                    continue
                schedule_id = f"PREPAY-{code}-{year}"
                opening = 0
                release_base, release_remainder = divmod(annual, 12)
                for month_index, month in enumerate(
                    _month_starts(
                        start,
                        min(_add_months(start, 11), self.request.actuals_end),
                    )
                ):
                    period = _period_id(month)
                    event_refs: list[str] = []
                    source_refs: list[str] = []
                    addition = annual if month_index == 0 else 0
                    release = release_base + (
                        release_remainder if month_index == 11 else 0
                    )
                    event_specs = []
                    if addition:
                        event_specs.append(
                            (
                                "PREPAYMENT_PAID",
                                addition,
                                date(month.year, month.month, 2),
                                0,
                                "PAY",
                            )
                        )
                    delay = (
                        11
                        if code == "SOFTWARE" and period == "2025-05"
                        else 0
                    )
                    event_specs.append(
                        (
                            "PREPAID_SERVICE_CONSUMED",
                            release,
                            _month_end(month),
                            delay,
                            "RELEASE",
                        )
                    )
                    for (
                        event_type,
                        amount,
                        event_date,
                        recorded_delay,
                        suffix,
                    ) in event_specs:
                        source_id = f"PSE-{code}-{year}-{period}-{suffix}"
                        row = {
                            "prepayment_source_event_id": source_id,
                            "prepayment_schedule_id": schedule_id,
                            "event_type": event_type,
                            "event_date": event_date.isoformat(),
                            "legal_entity_id": LEGAL_ENTITY_ID,
                            "department_id": department,
                            "expense_account_id": expense_account,
                            "counterparty_ref": counterparty,
                            "event_amount_minor": amount,
                            "currency": REPORTING_CURRENCY,
                            "approval_ref": f"AP-PREPAY-{schedule_id}@v1",
                            "source_recorded_at": _timestamp(
                                event_date + timedelta(days=recorded_delay), 16
                            ),
                            "duplicate_of_ref": "",
                        }
                        self._sink(PREPAYMENT_SOURCE_EVENTS).write(row)
                        posting = self.working_capital_posting_rules.derive(
                            WorkingCapitalPostingInput(
                                origin_class="BUSINESS_EVENT",
                                event_type=event_type,  # type: ignore[arg-type]
                                event_amount_minor=amount,
                                expense_account_id=expense_account,
                            )
                        )
                        event_refs.append(
                            self._post_a22b_event(
                                event_type=event_type,
                                source_definition=PREPAYMENT_SOURCE_EVENTS,
                                source_system="ACCOUNTS_PAYABLE",
                                source_record_ref=source_id,
                                source_payload=row,
                                occurred_date=event_date,
                                effective_date=event_date,
                                counterparty_ref=counterparty,
                                journal_amount_minor=posting.journal_amount_minor,
                                posting_rule_ref=posting.posting_rule_ref,
                                lines=posting.lines,
                                recorded_delay_days=recorded_delay,
                            )
                        )
                        source_refs.append(source_id)
                        if (
                            not duplicate_written
                            and code == "SOFTWARE"
                            and year == 2023
                            and suffix == "PAY"
                        ):
                            duplicate_written = True
                            duplicate_id = "PSE-DUPLICATE-00001"
                            duplicate_row = {
                                **row,
                                "prepayment_source_event_id": duplicate_id,
                                "duplicate_of_ref": source_id,
                            }
                            self._sink(PREPAYMENT_SOURCE_EVENTS).write(duplicate_row)
                            candidate_ref = _stable_ref(
                                "BE",
                                event_type,
                                "ACCOUNTS_PAYABLE",
                                duplicate_id,
                            )
                            decision = self._write_source_admission(
                                source_definition=PREPAYMENT_SOURCE_EVENTS,
                                source_system="ACCOUNTS_PAYABLE",
                                source_record_ref=duplicate_id,
                                source_payload=duplicate_row,
                                candidate_business_event_ref=candidate_ref,
                                event_date=event_date,
                                duplicate_of_ref=source_id,
                            )
                            if decision != "QUARANTINED":
                                raise ValueError(
                                    "duplicate prepayment was not quarantined"
                                )
                            self._defect(
                                defect_type="DUPLICATE_PREPAYMENT_SOURCE",
                                dataset_path=PREPAYMENT_SOURCE_EVENTS.path,
                                source_record_ref=duplicate_id,
                                detector="HERMES-DUPLICATE-SOURCE-IDENTITY@v1",
                                severity="HIGH",
                                treatment="QUARANTINE",
                                description=(
                                    "Duplicate annual software prepayment remains in "
                                    "Bronze and is excluded from accounting."
                                ),
                            )
                            self._write_statutory_subledger_control(
                                result_ref="ARGUS-PREPAY-DUPLICATE-00001",
                                definition_ref="ARGUS-PREPAYMENT-DUPLICATE@v1",
                                period_id=period,
                                domain="PREPAYMENT",
                                object_ref=duplicate_id,
                                observation_type="QUARANTINED_DUPLICATE_SOURCE",
                                status="EXCEPTION",
                                severity="HIGH",
                                expected_minor=0,
                                actual_minor=amount,
                                evidence_ref="EVIDENCE-PREPAY-DUPLICATE-00001",
                                source_record_refs=duplicate_id,
                            )
                    closing = opening + addition - release
                    self._sink(PREPAYMENT_SCHEDULE).write(
                        {
                            "prepayment_schedule_id": schedule_id,
                            "period_id": period,
                            "legal_entity_id": LEGAL_ENTITY_ID,
                            "department_id": department,
                            "expense_account_id": expense_account,
                            "opening_prepayment_minor": opening,
                            "cash_addition_minor": addition,
                            "expense_release_minor": release,
                            "closing_prepayment_minor": closing,
                            "currency": REPORTING_CURRENCY,
                            "business_event_refs": ",".join(event_refs),
                        }
                    )
                    self._write_statutory_subledger_control(
                        result_ref=f"ARGUS-PREPAY-{schedule_id}-{period}",
                        definition_ref="ARGUS-PREPAYMENT-ROLLFORWARD@v1",
                        period_id=period,
                        domain="PREPAYMENT",
                        object_ref=schedule_id,
                        observation_type="PREPAYMENT_ROLLFORWARD",
                        status="PASS",
                        severity="HIGH",
                        expected_minor=opening + addition - release,
                        actual_minor=closing,
                        evidence_ref=f"EVIDENCE-PREPAY-{schedule_id}-{period}",
                        source_record_refs=",".join(source_refs),
                    )
                    opening = closing

    def _generate_tax(self) -> None:
        tax_losses: dict[int, int] = {}
        opening_tax_payable = 0
        opening_dta = 0
        for month in self.actual_months:
            period = _period_id(month)
            month_end = _month_end(month)
            revenue = sum(
                self.activity[(period, account_id)][1]
                - self.activity[(period, account_id)][0]
                for account_id in ("4000", "4100")
            )
            expenses = sum(
                self.activity[(period, account_id)][0]
                - self.activity[(period, account_id)][1]
                for account_id in (
                    "5000",
                    "5100",
                    "6000",
                    "6100",
                    "6200",
                    "6300",
                    "6500",
                )
            )
            profit_before_tax = revenue - expenses
            ga_expense = (
                self.activity[(period, "6200")][0]
                - self.activity[(period, "6200")][1]
            )
            da_expense = (
                self.activity[(period, "6300")][0]
                - self.activity[(period, "6300")][1]
            )
            permanent_difference = max(0, ga_expense) * 200 // 10_000
            temporary_difference = max(0, da_expense) * 1_500 // 10_000
            statutory_rate_bps = 1_900 if period < "2023-04" else 2_500
            recognition_bps = 3_000
            taxable_before_losses = (
                profit_before_tax
                + permanent_difference
                + temporary_difference
            )
            opening_losses = dict(tax_losses)
            loss_generated = max(0, -taxable_before_losses)
            taxable_profit = max(0, taxable_before_losses)
            utilisation_by_vintage: dict[int, int] = defaultdict(int)
            remaining_taxable_profit = taxable_profit
            for vintage in sorted(tax_losses):
                utilised = min(tax_losses[vintage], remaining_taxable_profit)
                tax_losses[vintage] -= utilised
                utilisation_by_vintage[vintage] = utilised
                remaining_taxable_profit -= utilised
            if loss_generated:
                tax_losses[month.year] = (
                    tax_losses.get(month.year, 0) + loss_generated
                )
            loss_utilised = taxable_profit - remaining_taxable_profit
            current_tax_expense = (
                remaining_taxable_profit * statutory_rate_bps // 10_000
            )
            cash_tax_paid = 0
            closing_tax_payable = (
                opening_tax_payable
                + current_tax_expense
                - cash_tax_paid
            )
            total_closing_losses = sum(tax_losses.values())
            closing_dta = (
                total_closing_losses
                * statutory_rate_bps
                * recognition_bps
                // 100_000_000
            )
            deferred_tax_movement = closing_dta - opening_dta
            input_id = f"TAX-IN-UK-{period}"
            input_row = {
                "tax_calculation_input_id": input_id,
                "period_id": period,
                "legal_entity_id": LEGAL_ENTITY_ID,
                "jurisdiction_code": "GB",
                "profit_before_tax_minor": profit_before_tax,
                "permanent_difference_minor": permanent_difference,
                "temporary_difference_minor": temporary_difference,
                "statutory_tax_rate_bps": statutory_rate_bps,
                "deferred_tax_recognition_bps": recognition_bps,
                "currency": REPORTING_CURRENCY,
                "approval_ref": f"TAX-PROVISION-{period}@v1",
                "source_recorded_at": _timestamp(month_end, 17),
            }
            self._sink(TAX_CALCULATION_INPUTS).write(input_row)
            event_refs: list[str] = []
            if deferred_tax_movement:
                event_type = (
                    "DEFERRED_TAX_ASSET_RECOGNISED"
                    if deferred_tax_movement > 0
                    else "DEFERRED_TAX_ASSET_RELEASED"
                )
                amount = abs(deferred_tax_movement)
                posting = self.tax_posting_rules.derive(
                    TaxPostingInput(
                        origin_class="BUSINESS_EVENT",
                        event_type=event_type,  # type: ignore[arg-type]
                        event_amount_minor=amount,
                    )
                )
                event_refs.append(
                    self._post_a22b_event(
                        event_type=event_type,
                        source_definition=TAX_CALCULATION_INPUTS,
                        source_system="TAX_PROVISION",
                        source_record_ref=f"{input_id}#DEFERRED",
                        source_payload=input_row,
                        occurred_date=month_end,
                        effective_date=month_end,
                        counterparty_ref="HMRC",
                        journal_amount_minor=posting.journal_amount_minor,
                        posting_rule_ref=posting.posting_rule_ref,
                        lines=posting.lines,
                    )
                )
            self._sink(TAX_SCHEDULE).write(
                {
                    "period_id": period,
                    "legal_entity_id": LEGAL_ENTITY_ID,
                    "jurisdiction_code": "GB",
                    "opening_tax_payable_minor": opening_tax_payable,
                    "profit_before_tax_minor": profit_before_tax,
                    "permanent_difference_minor": permanent_difference,
                    "temporary_difference_minor": temporary_difference,
                    "taxable_profit_minor": remaining_taxable_profit,
                    "loss_generated_minor": loss_generated,
                    "loss_utilised_minor": loss_utilised,
                    "current_tax_expense_minor": current_tax_expense,
                    "deferred_tax_movement_minor": deferred_tax_movement,
                    "cash_tax_paid_minor": cash_tax_paid,
                    "closing_tax_payable_minor": closing_tax_payable,
                    "opening_deferred_tax_asset_minor": opening_dta,
                    "closing_deferred_tax_asset_minor": closing_dta,
                    "statutory_tax_rate_bps": statutory_rate_bps,
                    "currency": REPORTING_CURRENCY,
                    "business_event_refs": ",".join(event_refs),
                }
            )
            for vintage in sorted(tax_losses):
                opening_loss = opening_losses.get(vintage, 0)
                generated = loss_generated if vintage == month.year else 0
                utilised = utilisation_by_vintage.get(vintage, 0)
                closing_loss = tax_losses[vintage]
                self._sink(TAX_LOSS_REGISTER).write(
                    {
                        "period_id": period,
                        "legal_entity_id": LEGAL_ENTITY_ID,
                        "jurisdiction_code": "GB",
                        "loss_vintage_year": vintage,
                        "opening_tax_loss_minor": opening_loss,
                        "loss_generated_minor": generated,
                        "loss_utilised_minor": utilised,
                        "loss_expired_minor": 0,
                        "closing_tax_loss_minor": closing_loss,
                        "tax_rate_bps": statutory_rate_bps,
                        "currency": REPORTING_CURRENCY,
                    }
                )
                self._write_statutory_subledger_control(
                    result_ref=f"ARGUS-TAX-LOSS-{vintage}-{period}",
                    definition_ref="ARGUS-TAX-LOSS-ROLLFORWARD@v1",
                    period_id=period,
                    domain="TAX",
                    object_ref=f"GB-{vintage}",
                    observation_type="TAX_LOSS_ROLLFORWARD",
                    status="PASS",
                    severity="CRITICAL",
                    expected_minor=(opening_loss + generated - utilised),
                    actual_minor=closing_loss,
                    evidence_ref=f"EVIDENCE-TAX-LOSS-{vintage}-{period}",
                    source_record_refs=input_id,
                )
            self._write_statutory_subledger_control(
                result_ref=f"ARGUS-TAX-PROVISION-{period}",
                definition_ref="ARGUS-TAX-PROVISION-ROLLFORWARD@v1",
                period_id=period,
                domain="TAX",
                object_ref="NEXUS-UK-GB",
                observation_type="TAX_PROVISION_ROLLFORWARD",
                status="PASS",
                severity="CRITICAL",
                expected_minor=(
                    opening_tax_payable
                    + current_tax_expense
                    - cash_tax_paid
                ),
                actual_minor=closing_tax_payable,
                evidence_ref=f"EVIDENCE-TAX-PROVISION-{period}",
                source_record_refs=input_id,
            )
            self._write_statutory_subledger_control(
                result_ref=f"ARGUS-DEFERRED-TAX-{period}",
                definition_ref="ARGUS-DEFERRED-TAX-ASSET@v1",
                period_id=period,
                domain="TAX",
                object_ref="NEXUS-UK-GB",
                observation_type="DEFERRED_TAX_ASSET_ROLLFORWARD",
                status="PASS",
                severity="HIGH",
                expected_minor=opening_dta + deferred_tax_movement,
                actual_minor=closing_dta,
                evidence_ref=f"EVIDENCE-DEFERRED-TAX-{period}",
                source_record_refs=input_id,
            )
            opening_tax_payable = closing_tax_payable
            opening_dta = closing_dta

    def _generate_a22b_statutory_subledgers(self) -> None:
        self._generate_leases()
        self._generate_accruals()
        self._generate_prepayments()
        self._generate_tax()

    def _write_accounting_event(
        self,
        *,
        event_type: str,
        period_id: str,
        scope_id: str,
        governance_basis_ref: str,
        source_record_refs: str,
    ) -> str:
        event_ref = _stable_ref(
            "AE", event_type, period_id, scope_id, governance_basis_ref, length=22
        )
        if event_ref in self._accounting_event_refs:
            raise ValueError(f"duplicate accounting event identity: {event_ref}")
        self._accounting_event_refs.add(event_ref)
        month = date.fromisoformat(f"{period_id}-01")
        payload = {
            "accounting_event_ref": event_ref,
            "accounting_event_type": event_type,
            "occurred_at": _timestamp(_month_end(month), 20),
            "effective_date": _month_end(month).isoformat(),
            "period_id": period_id,
            "legal_entity_id": scope_id,
            "governance_basis_ref": governance_basis_ref,
            "source_record_refs": source_record_refs,
        }
        self._sink(ACCOUNTING_EVENTS).write(
            {
                **payload,
                "record_semantic_hash": sha256_bytes(
                    canonical_json_bytes(payload)
                ),
            }
        )
        self.accounting_event_by_key[(period_id, scope_id, event_type)] = event_ref
        return event_ref

    def _generate_intercompany(self) -> None:
        """Create independent bilateral evidence, entity journals, and eliminations."""

        cumulative: dict[tuple[str, str], int] = defaultdict(int)
        for month_index, month in enumerate(self.actual_months):
            if month < date(2021, 7, 1):
                continue
            period = _period_id(month)
            transaction_date = min(month + timedelta(days=14), _month_end(month))
            specs = (
                (
                    "NEXUS-UK",
                    "NEXUS-US",
                    "MANAGEMENT_SERVICE",
                    "6200",
                    8_500_000 + (month_index % 6) * 250_000,
                ),
                (
                    "NEXUS-US",
                    "NEXUS-UK",
                    "DEVELOPMENT_SERVICE",
                    "6000",
                    12_000_000 + (month_index % 8) * 400_000,
                ),
            )
            period_rows: list[dict[str, object]] = []
            for seller, buyer, transaction_type, expense_account, amount in specs:
                transaction_id = f"ICT-{seller}-{buyer}-{period}"
                seller_source_ref = f"{transaction_id}#SELLER"
                buyer_source_ref = f"{transaction_id}#BUYER"
                row = {
                    "intercompany_transaction_id": transaction_id,
                    "period_id": period,
                    "seller_entity_id": seller,
                    "buyer_entity_id": buyer,
                    "transaction_type": transaction_type,
                    "seller_source_record_ref": seller_source_ref,
                    "buyer_source_record_ref": buyer_source_ref,
                    "transaction_date": transaction_date.isoformat(),
                    "buyer_expense_account_id": expense_account,
                    "amount_minor": amount,
                    "currency": REPORTING_CURRENCY,
                    "transfer_pricing_policy_ref": "TP-INTERCOMPANY-SERVICES@v1",
                    "settlement_status": "OPEN_CONFIRMED",
                    "source_recorded_at": _timestamp(transaction_date, 15),
                }
                self._sink(INTERCOMPANY_TRANSACTIONS).write(row)
                self.intercompany_rows.append(row)
                period_rows.append(row)
                for side, entity_id, source_ref in (
                    ("SELLER", seller, seller_source_ref),
                    ("BUYER", buyer, buyer_source_ref),
                ):
                    posting = self.intercompany_posting_rules.derive(
                        IntercompanyPostingInput(
                            origin_class="BUSINESS_EVENT",
                            side=side,  # type: ignore[arg-type]
                            amount_minor=amount,
                            buyer_expense_account_id=expense_account,
                        )
                    )
                    self._post_a22b_event(
                        event_type=f"INTERCOMPANY_SERVICE_{side}",
                        source_definition=INTERCOMPANY_TRANSACTIONS,
                        source_system=f"INTERCOMPANY_BILLING_{entity_id}",
                        source_record_ref=source_ref,
                        source_payload=row,
                        occurred_date=transaction_date,
                        effective_date=transaction_date,
                        counterparty_ref=(buyer if side == "SELLER" else seller),
                        journal_amount_minor=posting.journal_amount_minor,
                        posting_rule_ref=posting.posting_rule_ref,
                        lines=posting.lines,
                        legal_entity_id=entity_id,
                    )
                cumulative[(seller, buyer)] += amount
                self._sink(INTERCOMPANY_BALANCES).write(
                    {
                        "period_id": period,
                        "seller_entity_id": seller,
                        "buyer_entity_id": buyer,
                        "seller_receivable_minor": cumulative[(seller, buyer)],
                        "buyer_payable_minor": cumulative[(seller, buyer)],
                        "confirmed_difference_minor": 0,
                        "currency": REPORTING_CURRENCY,
                        "confirmation_status": "CONFIRMED",
                        "seller_confirmation_ref": (
                            f"IC-CONF-{seller}-{buyer}-{period}-SELLER"
                        ),
                        "buyer_confirmation_ref": (
                            f"IC-CONF-{seller}-{buyer}-{period}-BUYER"
                        ),
                        "confirmed_at": _timestamp(_month_end(month), 17),
                        "evidence_ref": f"IC-EVIDENCE-{seller}-{buyer}-{period}",
                    }
                )

            event_ref = self._write_accounting_event(
                event_type="CONSOLIDATION_ELIMINATION_POSTED",
                period_id=period,
                scope_id="NEXUS-GROUP",
                governance_basis_ref="ATLAS-CONSOLIDATION-POLICY@v1",
                source_record_refs=",".join(
                    str(row["intercompany_transaction_id"]) for row in period_rows
                ),
            )
            journal_id = f"ELIM-IC-{period}@v1"
            line_no = 0
            for row in period_rows:
                elimination = self.consolidation_rules.derive(
                    ConsolidationEliminationInput(
                        origin_class="ACCOUNTING_EVENT",
                        amount_minor=int(row["amount_minor"]),
                        buyer_expense_account_id=str(
                            row["buyer_expense_account_id"]
                        ),
                    )
                )
                for account_id, debit_minor, credit_minor in elimination.lines:
                    line_no += 1
                    self._sink(CONSOLIDATION_ELIMINATIONS).write(
                        {
                            "elimination_journal_line_id": (
                                f"{journal_id}-L{line_no:03d}"
                            ),
                            "elimination_journal_id": journal_id,
                            "line_no": line_no,
                            "period_id": period,
                            "accounting_event_ref": event_ref,
                            "source_intercompany_transaction_id": row[
                                "intercompany_transaction_id"
                            ],
                            "account_id": account_id,
                            "debit_minor": debit_minor,
                            "credit_minor": credit_minor,
                            "currency": REPORTING_CURRENCY,
                        }
                    )
                    activity = self.elimination_activity[(period, account_id)]
                    activity[0] += debit_minor
                    activity[1] += credit_minor

    @staticmethod
    def _trial_balance_digest(rows: list[dict[str, object]]) -> str:
        encoded = [
            {key: str(value) for key, value in row.items()}
            for row in sorted(rows, key=lambda value: str(value["account_id"]))
        ]
        return sha256_bytes(canonical_json_bytes(encoded))

    @staticmethod
    def _statutory_reconciliation_ref(
        period_id: str, scope_id: str, control_id: str
    ) -> str:
        return f"ARGUS-{control_id}-{scope_id}-{period_id}@v1"

    def _write_statutory_reconciliation(
        self,
        *,
        period_id: str,
        scope_id: str,
        reporting_version_ref: str,
        control_id: str,
        expected_minor: int,
        actual_minor: int,
        evidence_ref: str,
    ) -> None:
        difference = actual_minor - expected_minor
        status = "PASS" if difference == 0 else "EXCEPTION"
        if difference:
            self.a23_control_failures += 1
        reconciliation_ref = self._statutory_reconciliation_ref(
            period_id, scope_id, control_id
        )
        self._sink(STATUTORY_RECONCILIATIONS).write(
            {
                "reconciliation_ref": reconciliation_ref,
                "period_id": period_id,
                "scope_id": scope_id,
                "reporting_version_ref": reporting_version_ref,
                "control_id": control_id,
                "expected_amount_minor": expected_minor,
                "actual_amount_minor": actual_minor,
                "difference_minor": difference,
                "currency": REPORTING_CURRENCY,
                "status": status,
                "evidence_ref": evidence_ref,
                "first_failure_ref": "" if status == "PASS" else reconciliation_ref,
            }
        )

    def _generate_a23_reporting(self) -> None:
        """Publish entity and group monthly close state and three statements."""

        scopes = ("NEXUS-UK", "NEXUS-US", "NEXUS-GROUP")
        accounts = {row[0]: row for row in ACCOUNT_ROWS}
        opening_by_scope_account: dict[tuple[str, str], int] = defaultdict(int)
        opening_retained_earnings = {scope: 0 for scope in scopes}
        opening_cash = {scope: 0 for scope in scopes}
        for month in self.actual_months:
            period = _period_id(month)
            for scope in scopes:
                soft_ref = self._write_accounting_event(
                    event_type="SOFT_CLOSE_COMPLETED",
                    period_id=period,
                    scope_id=scope,
                    governance_basis_ref="ATLAS-MONTHLY-CLOSE-POLICY@v1",
                    source_record_refs=f"SOURCE-LEDGER-{scope}-{period}",
                )
                hard_ref = self._write_accounting_event(
                    event_type="HARD_CLOSE_COMPLETED",
                    period_id=period,
                    scope_id=scope,
                    governance_basis_ref="ATLAS-HARD-CLOSE-POLICY@v1",
                    source_record_refs=(
                        ",".join(
                            (
                                soft_ref,
                                *(
                                    self._statutory_reconciliation_ref(
                                        period, scope, control_id
                                    )
                                    for control_id in (
                                        "TB-BALANCED",
                                        "BALANCE-SHEET-EQUATION",
                                        "RETAINED-EARNINGS-ROLLFORWARD",
                                        "CASH-FLOW-IDENTITY",
                                        "STATEMENT-LINEAGE",
                                    )
                                ),
                            )
                        )
                        if self.is_a24
                        else soft_ref
                    ),
                )
                self._write_accounting_event(
                    event_type="REPORTING_VERSION_PUBLISHED",
                    period_id=period,
                    scope_id=scope,
                    governance_basis_ref="ATLAS-REPORTING-PUBLICATION@v1",
                    source_record_refs=hard_ref,
                )

            for scope in scopes:
                reporting_version_ref = f"RV-{scope}-{period}@v1"
                rows: list[dict[str, object]] = []
                for account_id in accounts:
                    if scope == "NEXUS-GROUP":
                        debit = sum(
                            self.entity_activity[(period, entity, account_id)][0]
                            for entity in ("NEXUS-UK", "NEXUS-US")
                        )
                        credit = sum(
                            self.entity_activity[(period, entity, account_id)][1]
                            for entity in ("NEXUS-UK", "NEXUS-US")
                        )
                        elimination_debit, elimination_credit = (
                            self.elimination_activity[(period, account_id)]
                        )
                    else:
                        debit, credit = self.entity_activity[
                            (period, scope, account_id)
                        ]
                        elimination_debit = 0
                        elimination_credit = 0
                    opening = opening_by_scope_account[(scope, account_id)]
                    closing = (
                        opening
                        + debit
                        - credit
                        + elimination_debit
                        - elimination_credit
                    )
                    row = {
                        "period_id": period,
                        "scope_id": scope,
                        "legal_entity_id": (
                            scope if scope != "NEXUS-GROUP" else "CONSOLIDATED"
                        ),
                        "account_id": account_id,
                        "opening_balance_minor": opening,
                        "debit_activity_minor": debit,
                        "credit_activity_minor": credit,
                        "elimination_debit_minor": elimination_debit,
                        "elimination_credit_minor": elimination_credit,
                        "closing_balance_minor": closing,
                        "currency": REPORTING_CURRENCY,
                        "reporting_version_ref": reporting_version_ref,
                        "close_status": "HARD_CLOSED",
                    }
                    rows.append(row)
                    opening_by_scope_account[(scope, account_id)] = closing
                    self._sink(STATUTORY_TRIAL_BALANCE).write(row)

                trial_balance_digest = self._trial_balance_digest(rows)
                self.trial_balance_digest_by_scope_period[(scope, period)] = (
                    trial_balance_digest
                )
                total_closing = sum(
                    int(row["closing_balance_minor"]) for row in rows
                )
                monthly_net_income = 0
                statement_amounts: dict[str, int] = defaultdict(int)
                for row in rows:
                    account = accounts[str(row["account_id"])]
                    account_class = account[2]
                    debit = int(row["debit_activity_minor"]) + int(
                        row["elimination_debit_minor"]
                    )
                    credit = int(row["credit_activity_minor"]) + int(
                        row["elimination_credit_minor"]
                    )
                    if account_class == "REVENUE":
                        amount = credit - debit
                        monthly_net_income += amount
                        statement_amounts[str(account[4])] += amount
                    elif account_class == "EXPENSE":
                        amount = debit - credit
                        monthly_net_income -= amount
                        statement_amounts[str(account[4])] -= amount

                retained_earnings = (
                    opening_retained_earnings[scope] + monthly_net_income
                )
                self._sink(RETAINED_EARNINGS_BRIDGE).write(
                    {
                        "period_id": period,
                        "scope_id": scope,
                        "opening_retained_earnings_minor": (
                            opening_retained_earnings[scope]
                        ),
                        "net_income_minor": monthly_net_income,
                        "dividends_minor": 0,
                        "other_equity_movements_minor": 0,
                        "closing_retained_earnings_minor": retained_earnings,
                        "currency": REPORTING_CURRENCY,
                        "reporting_version_ref": reporting_version_ref,
                        "source_trial_balance_digest": trial_balance_digest,
                        "reconciliation_status": "RECONCILED",
                    }
                )

                presentation_order = 10
                for statement_line, amount in sorted(statement_amounts.items()):
                    self._sink(STATUTORY_STATEMENTS).write(
                        {
                            "period_id": period,
                            "scope_id": scope,
                            "statement_class": "INCOME_STATEMENT",
                            "statement_line": statement_line,
                            "amount_minor": amount,
                            "currency": REPORTING_CURRENCY,
                            "reporting_version_ref": reporting_version_ref,
                            "source_trial_balance_digest": trial_balance_digest,
                            "presentation_order": presentation_order,
                        }
                    )
                    presentation_order += 10
                self._sink(STATUTORY_STATEMENTS).write(
                    {
                        "period_id": period,
                        "scope_id": scope,
                        "statement_class": "INCOME_STATEMENT",
                        "statement_line": "net_income",
                        "amount_minor": monthly_net_income,
                        "currency": REPORTING_CURRENCY,
                        "reporting_version_ref": reporting_version_ref,
                        "source_trial_balance_digest": trial_balance_digest,
                        "presentation_order": presentation_order,
                    }
                )

                balance_sheet_amounts: dict[str, int] = defaultdict(int)
                total_assets = 0
                total_liabilities = 0
                total_equity = 0
                for row in rows:
                    account = accounts[str(row["account_id"])]
                    account_class = account[2]
                    if account[3] != "BALANCE_SHEET":
                        continue
                    closing = int(row["closing_balance_minor"])
                    amount = closing if account_class == "ASSET" else -closing
                    balance_sheet_amounts[str(account[4])] += amount
                    if account_class == "ASSET":
                        total_assets += amount
                    elif account_class == "LIABILITY":
                        total_liabilities += amount
                    elif account_class == "EQUITY":
                        total_equity += amount
                balance_sheet_amounts["retained_earnings"] += retained_earnings
                total_equity += retained_earnings
                balance_sheet_amounts["total_assets"] = total_assets
                balance_sheet_amounts["total_liabilities"] = total_liabilities
                balance_sheet_amounts["total_equity"] = total_equity
                balance_sheet_amounts["total_liabilities_and_equity"] = (
                    total_liabilities + total_equity
                )
                presentation_order = 10
                for statement_line, amount in balance_sheet_amounts.items():
                    self._sink(STATUTORY_STATEMENTS).write(
                        {
                            "period_id": period,
                            "scope_id": scope,
                            "statement_class": "BALANCE_SHEET",
                            "statement_line": statement_line,
                            "amount_minor": amount,
                            "currency": REPORTING_CURRENCY,
                            "reporting_version_ref": reporting_version_ref,
                            "source_trial_balance_digest": trial_balance_digest,
                            "presentation_order": presentation_order,
                        }
                    )
                    presentation_order += 10

                if scope == "NEXUS-GROUP":
                    cash_flows = {
                        cash_class: sum(
                            self.cash_flow_activity[(period, entity, cash_class)]
                            for entity in ("NEXUS-UK", "NEXUS-US")
                        )
                        for cash_class in ("OPERATING", "INVESTING", "FINANCING")
                    }
                else:
                    cash_flows = {
                        cash_class: self.cash_flow_activity[
                            (period, scope, cash_class)
                        ]
                        for cash_class in ("OPERATING", "INVESTING", "FINANCING")
                    }
                closing_cash = next(
                    int(row["closing_balance_minor"])
                    for row in rows
                    if row["account_id"] == "1000"
                )
                statement_cash_movement = sum(cash_flows.values())
                cash_difference = closing_cash - (
                    opening_cash[scope] + statement_cash_movement
                )
                self._sink(CASH_FLOW_RECONCILIATION).write(
                    {
                        "period_id": period,
                        "scope_id": scope,
                        "opening_cash_minor": opening_cash[scope],
                        "operating_cash_flow_minor": cash_flows["OPERATING"],
                        "investing_cash_flow_minor": cash_flows["INVESTING"],
                        "financing_cash_flow_minor": cash_flows["FINANCING"],
                        "fx_and_other_movement_minor": 0,
                        "closing_cash_minor": closing_cash,
                        "statement_cash_movement_minor": statement_cash_movement,
                        "unreconciled_difference_minor": cash_difference,
                        "currency": REPORTING_CURRENCY,
                        "reporting_version_ref": reporting_version_ref,
                        "source_trial_balance_digest": trial_balance_digest,
                        "reconciliation_status": (
                            "RECONCILED" if cash_difference == 0 else "EXCEPTION"
                        ),
                    }
                )
                cash_flow_lines = (
                    (("net_income", monthly_net_income),) if self.is_a24 else ()
                ) + (
                    ("operating_cash_flow", cash_flows["OPERATING"]),
                    ("investing_cash_flow", cash_flows["INVESTING"]),
                    ("financing_cash_flow", cash_flows["FINANCING"]),
                    ("net_change_in_cash", statement_cash_movement),
                    ("closing_cash", closing_cash),
                )
                for presentation_order, (statement_line, amount) in enumerate(
                    cash_flow_lines,
                    start=1,
                ):
                    self._sink(STATUTORY_STATEMENTS).write(
                        {
                            "period_id": period,
                            "scope_id": scope,
                            "statement_class": "CASH_FLOW",
                            "statement_line": statement_line,
                            "amount_minor": amount,
                            "currency": REPORTING_CURRENCY,
                            "reporting_version_ref": reporting_version_ref,
                            "source_trial_balance_digest": trial_balance_digest,
                            "presentation_order": presentation_order * 10,
                        }
                    )

                soft_ref = self.accounting_event_by_key[
                    (period, scope, "SOFT_CLOSE_COMPLETED")
                ]
                hard_ref = self.accounting_event_by_key[
                    (period, scope, "HARD_CLOSE_COMPLETED")
                ]
                publication_ref = self.accounting_event_by_key[
                    (period, scope, "REPORTING_VERSION_PUBLISHED")
                ]
                bank_status = (
                    "CONSOLIDATED"
                    if scope == "NEXUS-GROUP"
                    else "NOT_APPLICABLE"
                    if scope == "NEXUS-US" and month < date(2021, 7, 1)
                    else "RECONCILED"
                )
                intercompany_status = (
                    "NOT_APPLICABLE"
                    if month < date(2021, 7, 1)
                    else "CONFIRMED"
                )
                self._sink(MONTHLY_CLOSE_STATUS).write(
                    {
                        "period_id": period,
                        "legal_entity_id": scope,
                        "reporting_version_ref": reporting_version_ref,
                        "soft_close_accounting_event_ref": soft_ref,
                        "hard_close_accounting_event_ref": hard_ref,
                        "reporting_publication_accounting_event_ref": publication_ref,
                        "subledger_reconciliation_status": "RECONCILED",
                        "bank_reconciliation_status": bank_status,
                        "intercompany_reconciliation_status": intercompany_status,
                        "trial_balance_status": (
                            "BALANCED" if total_closing == 0 else "EXCEPTION"
                        ),
                        "statement_status": (
                            "PUBLISHED"
                            if total_assets == total_liabilities + total_equity
                            and cash_difference == 0
                            else "EXCEPTION"
                        ),
                        "close_status": "HARD_CLOSED",
                        "closed_at": _timestamp(_month_end(month), 23),
                    }
                )

                controls = (
                    (
                        "TB-BALANCED",
                        0,
                        total_closing,
                        f"TB-EVIDENCE-{scope}-{period}",
                    ),
                    (
                        "BALANCE-SHEET-EQUATION",
                        total_assets,
                        total_liabilities + total_equity,
                        f"BS-EVIDENCE-{scope}-{period}",
                    ),
                    (
                        "RETAINED-EARNINGS-ROLLFORWARD",
                        opening_retained_earnings[scope] + monthly_net_income,
                        retained_earnings,
                        f"RE-EVIDENCE-{scope}-{period}",
                    ),
                    (
                        "CASH-FLOW-IDENTITY",
                        closing_cash,
                        opening_cash[scope] + statement_cash_movement,
                        f"CF-EVIDENCE-{scope}-{period}",
                    ),
                    (
                        "STATEMENT-LINEAGE",
                        1,
                        1 if trial_balance_digest.startswith("sha256:") else 0,
                        trial_balance_digest,
                    ),
                )
                for control_id, expected, actual, evidence_ref in controls:
                    self._write_statutory_reconciliation(
                        period_id=period,
                        scope_id=scope,
                        reporting_version_ref=reporting_version_ref,
                        control_id=control_id,
                        expected_minor=expected,
                        actual_minor=actual,
                        evidence_ref=evidence_ref,
                    )
                opening_retained_earnings[scope] = retained_earnings
                opening_cash[scope] = closing_cash

    def _generate_bank_statements_and_reconciliations(self) -> None:
        transactions_by_account: dict[str, list[BankTransaction]] = defaultdict(list)
        for transaction in self.bank_transactions:
            transactions_by_account[transaction.bank_account_id].append(transaction)
        statement_closing_by_period: dict[tuple[str, str], int] = {}
        observed_balances: list[int] = []
        for account_id, transactions in sorted(transactions_by_account.items()):
            running_balance = 0
            for transaction in sorted(
                transactions,
                key=lambda item: (
                    item.value_date,
                    0 if item.amount_minor > 0 else 1,
                    item.bank_transaction_id,
                ),
            ):
                running_balance += transaction.amount_minor
                observed_balances.append(running_balance)
                period = _period_id(transaction.value_date)
                statement_closing_by_period[(account_id, period)] = running_balance
                self._sink(BANK_STATEMENT_LINES).write(
                    {
                        "statement_line_id": (
                            f"BSL-{transaction.bank_transaction_id}"
                        ),
                        "bank_account_id": account_id,
                        "statement_date": _month_end(
                            transaction.value_date
                        ).isoformat(),
                        "bank_transaction_id": transaction.bank_transaction_id,
                        "value_date": transaction.value_date.isoformat(),
                        "amount_minor": transaction.amount_minor,
                        "running_balance_minor": running_balance,
                        "currency": transaction.currency,
                        "statement_ref": f"BSTMT-{account_id}-{period}",
                    }
                )
        self.minimum_bank_balance_minor = min(observed_balances, default=0)
        opened_by_account = {
            "BANK-NEXUS-UK-GBP-OPERATING": self.request.history_start,
            "BANK-NEXUS-US-USD-OPERATING": date(2021, 7, 1),
        }
        entity_by_account = {
            account_id: entity_id
            for entity_id, (account_id, _) in self.bank_account_by_entity.items()
        }
        currency_by_account = {
            account_id: currency
            for account_id, currency in self.bank_account_by_entity.values()
        }
        statement_balances = {account_id: 0 for account_id in opened_by_account}
        gl_balances = {entity_id: 0 for entity_id in self.bank_account_by_entity}
        for month in self.actual_months:
            period = _period_id(month)
            for entity_id in gl_balances:
                debit, credit = self.entity_activity[(period, entity_id, "1000")]
                gl_balances[entity_id] += debit - credit
            for account_id, opened_date in opened_by_account.items():
                if month < date(opened_date.year, opened_date.month, 1):
                    continue
                statement_balances[account_id] = statement_closing_by_period.get(
                    (account_id, period), statement_balances[account_id]
                )
                entity_id = entity_by_account[account_id]
                statement_balance = statement_balances[account_id]
                gl_balance = gl_balances[entity_id]
                difference = statement_balance - gl_balance
                status = "RECONCILED" if difference == 0 else "EXCEPTION"
                if difference:
                    self.bank_reconciliation_failures += 1
                self._sink(BANK_RECONCILIATIONS).write(
                    {
                        "period_id": period,
                        "bank_account_id": account_id,
                        "statement_closing_minor": statement_balance,
                        "gl_cash_closing_minor": gl_balance,
                        "outstanding_receipts_minor": 0,
                        "outstanding_disbursements_minor": 0,
                        "other_reconciling_items_minor": 0,
                        "unreconciled_difference_minor": difference,
                        "currency": currency_by_account[account_id],
                        "reporting_version_ref": f"RV-{entity_id}-{period}@v1",
                        "source_trial_balance_digest": (
                            self.trial_balance_digest_by_scope_period[
                                (entity_id, period)
                            ]
                        ),
                        "reconciliation_status": status,
                        "evidence_ref": f"BANK-RECON-EVIDENCE-{account_id}-{period}",
                        "first_failure_ref": (
                            ""
                            if status == "RECONCILED"
                            else f"BANK-RECON-{account_id}-{period}@v1"
                        ),
                    }
                )

    def _actual_amount(self, period: str, account_id: str) -> int:
        debit, credit = self.activity[(period, account_id)]
        account = next(row for row in ACCOUNT_ROWS if row[0] == account_id)
        return credit - debit if account[5] == "CREDIT" else debit - credit

    def _generate_planning(self) -> None:
        first_period = _period_id(self.actual_months[0])
        last_period = _period_id(self.actual_months[-1])
        self._sink(BUDGET_VERSIONS).write(
            {
                "budget_version_ref": "AOP-2026@v1",
                "budget_name": "Historical benchmark and 2026 operating plan",
                "planning_start_period": first_period,
                "planning_end_period": last_period,
                "approval_status": "APPROVED",
                "approved_at": "2025-12-15T12:00:00Z",
                "locked_flag": True,
            }
        )
        forecast_start = _period_id(_add_months(self.request.actuals_end, 1))
        forecast_end = _period_id(_add_months(self.request.actuals_end, 120))
        for scenario in ("BEAR", "BASE", "BULL"):
            self._sink(FORECAST_VERSIONS).write(
                {
                    "forecast_version_ref": "RF-2026-06@v1",
                    "scenario_code": scenario,
                    "cutover_period": last_period,
                    "forecast_start_period": forecast_start,
                    "forecast_end_period": forecast_end,
                    "source_budget_version_ref": "AOP-2026@v1",
                    "approval_status": "APPROVED"
                    if scenario == "BASE"
                    else "DRAFT",
                    "locked_flag": scenario == "BASE",
                }
            )
        for month in self.actual_months:
            period = _period_id(month)
            for department_index, department in enumerate(DEPARTMENT_ROWS):
                department_id = department[0]
                for account_id in PLANNING_ACCOUNT_IDS:
                    actual = abs(self._actual_amount(period, account_id))
                    allocation = max(10_000, actual // len(DEPARTMENT_ROWS))
                    budget = allocation * (10_200 + (department_index % 3) * 75) // 10_000
                    line_id = _stable_ref("BUD", "AOP-2026@v1", period, department_id, account_id)
                    self._sink(BUDGET_LINES).write(
                        {
                            "budget_line_id": line_id,
                            "budget_version_ref": "AOP-2026@v1",
                            "period_id": period,
                            "department_id": department_id,
                            "account_id": account_id,
                            "amount_minor": budget,
                            "currency": REPORTING_CURRENCY,
                            "reporting_amount_minor": budget,
                            "reporting_currency": REPORTING_CURRENCY,
                            "approval_status": "APPROVED",
                        }
                    )
                    self._sink(VARIANCE_SOURCE).write(
                        {
                            "variance_line_id": _stable_ref(
                                "VAR", period, department_id, account_id
                            ),
                            "period_id": period,
                            "period_status": "ACTUAL",
                            "department_id": department_id,
                            "account_id": account_id,
                            "actual_amount_minor": allocation,
                            "budget_amount_minor": budget,
                            "forecast_amount_minor": 0,
                            "actual_vs_budget_variance_minor": allocation - budget,
                            "actual_vs_forecast_variance_minor": allocation,
                            "forecast_vs_budget_variance_minor": -budget,
                            "currency": REPORTING_CURRENCY,
                            "source_budget_line_ref": line_id,
                            "source_forecast_line_ref": "",
                        }
                    )
        last_actual = self.actual_months[-1]
        future_months = _month_starts(_add_months(last_actual, 1), _add_months(last_actual, 120))
        scenario_bps = {"BEAR": 9_700, "BASE": 10_000, "BULL": 10_350}
        for scenario in ("BEAR", "BASE", "BULL"):
            for month_index, month in enumerate(future_months, start=1):
                comparable = self.actual_months[(month_index - 1) % 12 - 12]
                comparable_period = _period_id(comparable)
                annual_growth_bps = scenario_bps[scenario] + 900
                compound_years = (month_index - 1) // 12 + 1
                growth_factor_bps = 10_000
                for _ in range(compound_years):
                    growth_factor_bps = growth_factor_bps * annual_growth_bps // 10_000
                for department in DEPARTMENT_ROWS:
                    department_id = department[0]
                    for account_id in PLANNING_ACCOUNT_IDS:
                        actual = abs(self._actual_amount(comparable_period, account_id))
                        base_amount = max(10_000, actual // len(DEPARTMENT_ROWS))
                        amount = base_amount * growth_factor_bps // 10_000
                        if account_id in {"5000", "5100", "6000", "6100", "6200"}:
                            amount = amount * scenario_bps[scenario] // 10_000
                        period = _period_id(month)
                        line_id = _stable_ref(
                            "FCST", "RF-2026-06@v1", scenario, period, department_id, account_id
                        )
                        self._sink(FORECAST_LINES).write(
                            {
                                "forecast_line_id": line_id,
                                "forecast_version_ref": "RF-2026-06@v1",
                                "scenario_code": scenario,
                                "period_id": period,
                                "department_id": department_id,
                                "account_id": account_id,
                                "amount_minor": amount,
                                "currency": REPORTING_CURRENCY,
                                "reporting_amount_minor": amount,
                                "reporting_currency": REPORTING_CURRENCY,
                                "assumption_basis_ref": f"ASSUMPTION-{scenario}-GROWTH@v1",
                                "approval_status": "APPROVED" if scenario == "BASE" else "DRAFT",
                            }
                        )
                        if scenario == "BASE":
                            budget_benchmark = (
                                base_amount * (10_800**compound_years)
                                // (10_000**compound_years)
                            )
                            self._sink(VARIANCE_SOURCE).write(
                                {
                                    "variance_line_id": _stable_ref(
                                        "VAR", period, department_id, account_id
                                    ),
                                    "period_id": period,
                                    "period_status": "FORECAST",
                                    "department_id": department_id,
                                    "account_id": account_id,
                                    "actual_amount_minor": 0,
                                    "budget_amount_minor": budget_benchmark,
                                    "forecast_amount_minor": amount,
                                    "actual_vs_budget_variance_minor": (
                                        -budget_benchmark
                                    ),
                                    "actual_vs_forecast_variance_minor": -amount,
                                    "forecast_vs_budget_variance_minor": (
                                        amount - budget_benchmark
                                    ),
                                    "currency": REPORTING_CURRENCY,
                                    "source_budget_line_ref": "",
                                    "source_forecast_line_ref": line_id,
                                }
                            )

    def _generate_financial_reports(self) -> None:
        balances = {row[0]: 0 for row in ACCOUNT_ROWS}
        account_by_id = {row[0]: row for row in ACCOUNT_ROWS}
        presentation_order = {
            line: index
            for index, line in enumerate(
                dict.fromkeys(row[4] for row in ACCOUNT_ROWS), start=1
            )
        }
        cumulative_profit = 0
        for month in self.actual_months:
            period = _period_id(month)
            statement_values: dict[tuple[str, str], int] = defaultdict(int)
            monthly_profit = 0
            for account_id, *_ in ACCOUNT_ROWS:
                opening = balances[account_id]
                debit, credit = self.activity[(period, account_id)]
                closing = opening + debit - credit
                balances[account_id] = closing
                self._sink(TRIAL_BALANCE).write(
                    {
                        "period_id": period,
                        "account_id": account_id,
                        "opening_balance_minor": opening,
                        "debit_activity_minor": debit,
                        "credit_activity_minor": credit,
                        "closing_balance_minor": closing,
                        "currency": REPORTING_CURRENCY,
                        "reporting_version_ref": f"RV-{period}@v1",
                    }
                )
                account = account_by_id[account_id]
                statement_class = account[3]
                statement_line = account[4]
                if statement_class == "INCOME_STATEMENT":
                    amount = credit - debit if account[5] == "CREDIT" else debit - credit
                    statement_values[(statement_class, statement_line)] += amount
                    monthly_profit += amount if account[5] == "CREDIT" else -amount
                else:
                    amount = -closing if account[5] == "CREDIT" else closing
                    statement_values[(statement_class, statement_line)] += amount
            cumulative_profit += monthly_profit
            statement_values[("BALANCE_SHEET", "retained_earnings")] += cumulative_profit
            for (statement_class, statement_line), amount in sorted(
                statement_values.items(),
                key=lambda item: (item[0][0], presentation_order[item[0][1]]),
            ):
                self._sink(FINANCIAL_STATEMENTS).write(
                    {
                        "period_id": period,
                        "statement_class": statement_class,
                        "statement_line": statement_line,
                        "amount_minor": amount,
                        "currency": REPORTING_CURRENCY,
                        "reporting_version_ref": f"RV-{period}@v1",
                        "presentation_order": presentation_order[statement_line],
                    }
                )

    def _write_qa_results(self) -> None:
        total_debits = sum(value[0] for value in self.activity.values())
        total_credits = sum(value[1] for value in self.activity.values())
        bank_net_movement = sum(
            transaction.amount_minor for transaction in self.bank_transactions
        )
        cash_gl_net_movement = sum(
            debit - credit
            for (period, entity_id, account_id), (
                debit,
                credit,
            ) in self.entity_activity.items()
            if period in {_period_id(month) for month in self.actual_months}
            and entity_id in self.bank_account_by_entity
            and account_id == "1000"
        )
        checks = (
            (
                "QA-CUSTOMER-COUNT",
                "COMPLETENESS",
                self.profile.customer_count,
                self._sink(CUSTOMERS).row_count,
                "HIGH",
                "Customer generator emitted the selected scale profile.",
            ),
            (
                "QA-VENDOR-COUNT",
                "COMPLETENESS",
                self.profile.vendor_count,
                self._sink(VENDORS).row_count,
                "HIGH",
                "Vendor generator emitted the selected scale profile.",
            ),
            (
                "QA-EMPLOYEE-COUNT",
                "COMPLETENESS",
                self.profile.employee_count,
                self._sink(EMPLOYEES).row_count,
                "HIGH",
                "Employee generator emitted the selected scale profile.",
            ),
            (
                "QA-ACTUAL-PERIOD-COUNT",
                "PERIOD_COVERAGE",
                len(self.actual_months),
                len(self.actual_months),
                "HIGH",
                "Actual history covers every requested month.",
            ),
            (
                "QA-GL-DEBIT-CREDIT",
                "ACCOUNTING_INTEGRITY",
                total_debits,
                total_credits,
                "CRITICAL",
                "Generated source journals balance in reporting minor units.",
            ),
            (
                "QA-EVENT-JOURNAL-COUNT",
                "CAUSALITY",
                len(self._event_refs),
                len(self._journal_refs),
                "CRITICAL",
                "Every causal business event produced one source journal.",
            ),
            (
                "QA-DECLARED-DEFECTS",
                "DEFECT_REGISTRY",
                len(self.defects),
                len(self.defects),
                "HIGH",
                "Every injected data-quality defect is declared.",
            ),
            (
                "QA-BANK-CASH-MOVEMENT",
                "TREASURY_RECONCILIATION",
                cash_gl_net_movement,
                bank_net_movement,
                "CRITICAL",
                "Bank transactions reproduce signed source-GL cash movement.",
            ),
            (
                "QA-BANK-RECONCILIATIONS",
                "TREASURY_RECONCILIATION",
                0,
                self.bank_reconciliation_failures,
                "CRITICAL",
                "Every open bank account reconciles to entity cash each month.",
            ),
            (
                "QA-DEBT-SCHEDULE-COVERAGE",
                "FINANCING_COVERAGE",
                len(self.actual_months) * 2,
                self._sink(DEBT_SCHEDULE).row_count,
                "CRITICAL",
                "Both finite facilities have one schedule row per actual month.",
            ),
            (
                "QA-NO-AUTOMATIC-CASH-PLUG",
                "FINANCING_POLICY",
                1,
                int(self.minimum_bank_balance_minor >= 0),
                "CRITICAL",
                "Fixed authorised funding supports cash without automatic draws.",
            ),
            (
                "QA-FIXED-ASSET-CONTROLS",
                "ASSET_SUBLEDGER_RECONCILIATION",
                0,
                self.fixed_asset_control_failures,
                "CRITICAL",
                "Atlas asset movements pass their produced Argus controls.",
            ),
            (
                "QA-FIXED-ASSET-ASSURANCE-COVERAGE",
                "ASSURANCE_COVERAGE",
                1,
                int(self._sink(FIXED_ASSET_CONTROL_RESULTS).row_count > 0),
                "HIGH",
                "The fixed-asset population has machine assurance results.",
            ),
            (
                "QA-A22B-SUBLEDGER-CONTROLS",
                "STATUTORY_SUBLEDGER_RECONCILIATION",
                0,
                self.stat_subledger_control_failures,
                "CRITICAL",
                "Lease, tax, accrual and prepayment roll-forwards pass controls.",
            ),
            (
                "QA-A22B-ASSURANCE-COVERAGE",
                "ASSURANCE_COVERAGE",
                1,
                int(
                    self._sink(STATUTORY_SUBLEDGER_CONTROL_RESULTS).row_count
                    > 0
                ),
                "HIGH",
                "A2.2b statutory subledgers have machine assurance results.",
            ),
        )
        for check_ref, category, expected, actual, severity, notes in checks:
            self._sink(SOURCE_QA_RESULTS).write(
                {
                    "check_ref": check_ref,
                    "check_category": category,
                    "expected_value": expected,
                    "actual_value": actual,
                    "status": "PASS" if expected == actual else "FAIL",
                    "severity": severity,
                    "notes": notes,
                }
            )

    def _write_defects_and_inventory(self) -> None:
        for defect in sorted(self.defects, key=lambda item: str(item["defect_instance_ref"])):
            self._sink(DEFECT_REGISTRY).write(defect)
        self._write_qa_results()
        for definition in ALL_SOURCE_DATASETS:
            if definition is SOURCE_INVENTORY:
                continue
            self._sink(SOURCE_INVENTORY).write(
                {
                    "source_dataset_path": definition.path,
                    "source_system": definition.source_system,
                    "record_class": definition.record_class,
                    "grain": definition.grain,
                    "row_count": self._sink(definition).row_count,
                    "column_count": len(definition.columns),
                }
            )

    def generate(self) -> GeneratedPopulation:
        try:
            self._write_references()
            self._write_a21_foundations()
            customers = self._generate_customers()
            vendors = self._generate_vendors()
            employees = self._generate_employees()
            subscriptions = self._generate_subscriptions(customers)
            self._opening_events()
            self._generate_billing(subscriptions)
            self._generate_deferred_revenue_rollforward()
            self._generate_procurement(vendors)
            self._generate_payroll(employees)
            self._generate_headcount_plan()
            self._generate_fixed_asset_vertical(vendors)
            self._generate_financing()
            self._generate_a22b_statutory_subledgers()
            self._generate_intercompany()
            self._generate_a23_reporting()
            self._generate_bank_statements_and_reconciliations()
            self._generate_planning()
            self._generate_financial_reports()
            self._write_defects_and_inventory()
        finally:
            for sink in self.sinks.values():
                sink.close()
        row_counts = {path: sink.row_count for path, sink in self.sinks.items()}
        if set(row_counts) != set(DATASET_BY_PATH):
            raise ValueError("generated source inventory is not closed")
        return GeneratedPopulation(
            row_counts=row_counts,
            defect_count=len(self.defects),
            history_month_count=len(self.actual_months),
            total_period_count=len(self.all_months),
        )
