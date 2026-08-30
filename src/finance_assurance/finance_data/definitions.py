"""Closed Atlas source-dataset and finance-reference definitions."""

from __future__ import annotations

from dataclasses import dataclass

from finance_assurance.finance_data.statutory_gate import STATUTORY_SOURCE_BY_ID


@dataclass(frozen=True)
class DatasetDefinition:
    """One closed source, derived, control, or reference package dataset."""

    path: str
    source_system: str
    record_class: str
    grain: str
    columns: tuple[str, ...]


def _dataset(
    path: str,
    source_system: str,
    record_class: str,
    grain: str,
    *columns: str,
) -> DatasetDefinition:
    return DatasetDefinition(path, source_system, record_class, grain, columns)


def _a2_dataset(dataset_id: str, source_system: str) -> DatasetDefinition:
    authority = STATUTORY_SOURCE_BY_ID[dataset_id]
    return DatasetDefinition(
        path=authority.path,
        source_system=source_system,
        record_class=authority.record_class,
        grain=authority.grain,
        columns=authority.columns,
    )


LEGAL_ENTITIES = _a2_dataset("A2-LEGAL-ENTITIES", "CORPORATE_SECRETARY")
BANK_ACCOUNTS = _a2_dataset("A2-BANK-ACCOUNTS", "TREASURY")
BANK_TRANSACTIONS = _a2_dataset("A2-BANK-TRANSACTIONS", "BANK")
BANK_STATEMENT_LINES = _a2_dataset("A2-BANK-STATEMENT-LINES", "BANK")
BANK_RECONCILIATIONS = _a2_dataset("A2-BANK-RECONCILIATIONS", "TREASURY")
DEBT_INSTRUMENTS = _a2_dataset("A2-DEBT-INSTRUMENTS", "TREASURY")
DEBT_SCHEDULE = _a2_dataset("A2-DEBT-SCHEDULE", "TREASURY")
EQUITY_MOVEMENTS = _a2_dataset("A2-EQUITY-MOVEMENTS", "CORPORATE_SECRETARY")
CAPITAL_PURCHASE_ORDERS = _a2_dataset(
    "A2-CAPITAL-PURCHASE-ORDERS", "PROCUREMENT"
)
CAPITAL_GOODS_RECEIPTS = _a2_dataset(
    "A2-CAPITAL-GOODS-RECEIPTS", "WAREHOUSE"
)
CAPITAL_INVOICES = _a2_dataset("A2-CAPITAL-INVOICES", "ACCOUNTS_PAYABLE")
ASSET_LIFECYCLE_EVENTS = _a2_dataset(
    "A2-ASSET-LIFECYCLE-EVENTS", "FIXED_ASSET_SUBLEDGER"
)
FIXED_ASSET_REGISTER = _a2_dataset(
    "A2-FIXED-ASSET-REGISTER", "FIXED_ASSET_SUBLEDGER"
)
FIXED_ASSET_MOVEMENTS = _a2_dataset(
    "A2-FIXED-ASSET-MOVEMENTS", "ATLAS"
)
SOURCE_ADMISSION_RESULTS = _a2_dataset(
    "A2-SOURCE-ADMISSION-RESULTS", "HERMES"
)
FIXED_ASSET_CONTROL_RESULTS = _a2_dataset(
    "A2-FIXED-ASSET-CONTROL-RESULTS", "ARGUS"
)
LEASE_CONTRACTS = _a2_dataset("A2-LEASE-CONTRACTS", "LEASE_ADMINISTRATION")
LEASE_LIFECYCLE_EVENTS = _a2_dataset(
    "A2-LEASE-LIFECYCLE-EVENTS", "LEASE_ADMINISTRATION"
)
LEASE_SCHEDULE = _a2_dataset("A2-LEASE-SCHEDULE", "ATLAS")
TAX_CALCULATION_INPUTS = _a2_dataset(
    "A2-TAX-CALCULATION-INPUTS", "TAX_PROVISION"
)
TAX_SCHEDULE = _a2_dataset("A2-TAX-SCHEDULE", "ATLAS")
TAX_LOSS_REGISTER = _a2_dataset("A2-TAX-LOSS-REGISTER", "ATLAS")
ACCRUAL_SOURCE_EVENTS = _a2_dataset(
    "A2-ACCRUAL-SOURCE-EVENTS", "CLOSE_MANAGEMENT"
)
ACCRUAL_SCHEDULE = _a2_dataset("A2-ACCRUAL-SCHEDULE", "ATLAS")
PREPAYMENT_SOURCE_EVENTS = _a2_dataset(
    "A2-PREPAYMENT-SOURCE-EVENTS", "ACCOUNTS_PAYABLE"
)
PREPAYMENT_SCHEDULE = _a2_dataset("A2-PREPAYMENT-SCHEDULE", "ATLAS")
STATUTORY_SUBLEDGER_CONTROL_RESULTS = _a2_dataset(
    "A2-STATUTORY-SUBLEDGER-CONTROL-RESULTS", "ARGUS"
)
INTERCOMPANY_TRANSACTIONS = _a2_dataset(
    "A2-INTERCOMPANY-TRANSACTIONS", "INTERCOMPANY_BILLING"
)
INTERCOMPANY_BALANCES = _a2_dataset(
    "A2-INTERCOMPANY-BALANCES", "INTERCOMPANY_CONFIRMATION"
)
CONSOLIDATION_ELIMINATIONS = _a2_dataset(
    "A2-CONSOLIDATION-ELIMINATIONS", "ATLAS"
)
ACCOUNTING_EVENTS = _a2_dataset("A2-ACCOUNTING-EVENTS", "ATLAS")
STATUTORY_TRIAL_BALANCE = _a2_dataset(
    "A2-STATUTORY-TRIAL-BALANCE", "ATLAS"
)
STATUTORY_STATEMENTS = _a2_dataset("A2-STATUTORY-STATEMENTS", "ATLAS")
RETAINED_EARNINGS_BRIDGE = _a2_dataset(
    "A2-RETAINED-EARNINGS-BRIDGE", "ATLAS"
)
CASH_FLOW_RECONCILIATION = _a2_dataset(
    "A2-CASH-FLOW-RECONCILIATION", "ATLAS"
)
MONTHLY_CLOSE_STATUS = _a2_dataset("A2-MONTHLY-CLOSE-STATUS", "ATLAS")
STATUTORY_RECONCILIATIONS = _a2_dataset(
    "A2-STATUTORY-RECONCILIATIONS", "ARGUS"
)


PERIODS = _dataset(
    "reference/periods.csv",
    "FINANCE_CALENDAR",
    "REFERENCE",
    "ONE_ROW_PER_FISCAL_MONTH",
    "period_id",
    "month_start",
    "month_end",
    "fiscal_year",
    "fiscal_quarter",
    "month_number",
    "is_actual_period",
)
REGIONS = _dataset(
    "reference/regions.csv",
    "CRM",
    "REFERENCE",
    "ONE_ROW_PER_REGION",
    "region_id",
    "region_name",
    "local_currency",
    "reporting_currency",
)
FX_RATES = _dataset(
    "reference/exchange_rates.csv",
    "TREASURY",
    "REFERENCE",
    "ONE_ROW_PER_PERIOD_CURRENCY",
    "period_id",
    "currency",
    "average_rate_to_gbp_ppm",
    "closing_rate_to_gbp_ppm",
    "rate_scale",
)
DEPARTMENTS = _dataset(
    "reference/departments.csv",
    "HRIS",
    "REFERENCE",
    "ONE_ROW_PER_DEPARTMENT",
    "department_id",
    "department_name",
    "business_unit",
    "opex_class",
)
PRODUCTS = _dataset(
    "reference/products.csv",
    "BILLING",
    "REFERENCE",
    "ONE_ROW_PER_PRODUCT",
    "product_id",
    "product_name",
    "product_family",
    "revenue_type",
    "gross_margin_target_bps",
    "active_from",
)
PRODUCT_PRICE_BOOK = _dataset(
    "reference/product_price_book.csv",
    "BILLING",
    "REFERENCE",
    "ONE_ROW_PER_PRODUCT_SEGMENT_REGION_PRICE",
    "price_book_id",
    "product_id",
    "customer_segment",
    "region_id",
    "currency",
    "monthly_list_price_minor",
    "annual_list_price_minor",
    "reporting_monthly_list_price_minor",
    "reporting_currency",
    "effective_start_date",
    "effective_end_date",
    "status",
)
SUBSCRIPTION_EVENTS = _dataset(
    "billing/subscription_events.csv",
    "BILLING",
    "SOURCE_RECORD",
    "ONE_ROW_PER_SUBSCRIPTION_LIFECYCLE_EVENT",
    "subscription_event_id",
    "subscription_id",
    "customer_id",
    "event_sequence",
    "event_date",
    "event_type",
    "event_reason",
    "previous_mrr_minor",
    "new_mrr_minor",
    "mrr_delta_minor",
    "currency",
    "reporting_previous_mrr_minor",
    "reporting_new_mrr_minor",
    "reporting_mrr_delta_minor",
    "reporting_currency",
    "source_system",
)
CHART_OF_ACCOUNTS = _dataset(
    "accounting/chart_of_accounts.csv",
    "ERP",
    "REFERENCE",
    "ONE_ROW_PER_GL_ACCOUNT",
    "account_id",
    "account_name",
    "account_class",
    "statement_class",
    "statement_line",
    "normal_balance",
    "cash_flow_class",
)
CUSTOMERS = _dataset(
    "billing/customers.csv",
    "BILLING",
    "SOURCE_RECORD",
    "ONE_ROW_PER_BILLING_CUSTOMER",
    "customer_id",
    "customer_name",
    "region_id",
    "segment",
    "industry",
    "created_date",
    "credit_terms_days",
    "status",
)
CRM_ACCOUNTS = _dataset(
    "crm/accounts.csv",
    "CRM",
    "SOURCE_RECORD",
    "ONE_ROW_PER_CRM_ACCOUNT",
    "crm_account_id",
    "billing_customer_id",
    "account_name",
    "region_id",
    "segment",
    "owner_ref",
    "status",
)
VENDORS = _dataset(
    "procurement/vendors.csv",
    "PROCUREMENT",
    "SOURCE_RECORD",
    "ONE_ROW_PER_VENDOR",
    "vendor_id",
    "vendor_name",
    "category",
    "region_id",
    "payment_terms_days",
    "status",
)
EMPLOYEES = _dataset(
    "hris/employees.csv",
    "HRIS",
    "SOURCE_RECORD",
    "ONE_ROW_PER_EMPLOYEE",
    "employee_id",
    "department_id",
    "region_id",
    "hire_date",
    "termination_date",
    "annual_salary_minor",
    "salary_currency",
    "employment_status",
)
SUBSCRIPTIONS = _dataset(
    "billing/subscriptions.csv",
    "BILLING",
    "SOURCE_RECORD",
    "ONE_ROW_PER_SUBSCRIPTION",
    "subscription_id",
    "customer_id",
    "product_id",
    "contract_start_date",
    "contract_end_date",
    "billing_frequency",
    "monthly_recurring_revenue_minor",
    "currency",
    "status",
)
INVOICES = _dataset(
    "billing/invoices.csv",
    "BILLING",
    "SOURCE_RECORD",
    "ONE_ROW_PER_CUSTOMER_INVOICE",
    "invoice_id",
    "customer_id",
    "subscription_id",
    "invoice_date",
    "due_date",
    "service_period_start",
    "service_period_end",
    "invoice_amount_minor",
    "tax_amount_minor",
    "currency",
    "reporting_amount_minor",
    "reporting_currency",
    "invoice_status",
    "external_invoice_number",
)
VENDOR_INVOICE_LINES = _dataset(
    "procurement/vendor_invoice_lines.csv",
    "PROCUREMENT",
    "SOURCE_RECORD",
    "ONE_ROW_PER_VENDOR_INVOICE_LINE",
    "vendor_invoice_line_id",
    "vendor_invoice_id",
    "vendor_id",
    "line_no",
    "department_id",
    "expense_account_id",
    "service_period_start",
    "service_period_end",
    "line_description",
    "line_amount_minor",
    "currency",
    "reporting_line_amount_minor",
    "reporting_currency",
)
INVOICE_LINES = _dataset(
    "billing/invoice_lines.csv",
    "BILLING",
    "SOURCE_RECORD",
    "ONE_ROW_PER_CUSTOMER_INVOICE_LINE",
    "invoice_line_id",
    "invoice_id",
    "line_no",
    "product_id",
    "line_type",
    "quantity",
    "unit_price_minor",
    "line_amount_minor",
    "currency",
    "reporting_line_amount_minor",
    "reporting_currency",
)
PAYMENTS = _dataset(
    "billing/payments.csv",
    "PAYMENTS",
    "SOURCE_RECORD",
    "ONE_ROW_PER_CASH_RECEIPT",
    "payment_id",
    "customer_id",
    "payment_date",
    "payment_amount_minor",
    "currency",
    "reporting_amount_minor",
    "reporting_currency",
    "payment_method",
    "payment_status",
    "source_bank_reference",
)
PAYMENT_ALLOCATIONS = _dataset(
    "billing/payment_allocations.csv",
    "BILLING",
    "SOURCE_RECORD",
    "ONE_ROW_PER_PAYMENT_TO_INVOICE_ALLOCATION",
    "allocation_id",
    "payment_id",
    "invoice_id",
    "allocated_amount_minor",
    "currency",
    "reporting_allocated_amount_minor",
    "reporting_currency",
    "allocation_date",
    "allocation_status",
)
AR_AGEING = _dataset(
    "billing/ar_ageing_snapshot.csv",
    "BILLING",
    "SOURCE_RECORD",
    "ONE_ROW_PER_OPEN_INVOICE_PER_DAILY_SNAPSHOT",
    "snapshot_date",
    "invoice_id",
    "customer_id",
    "due_date",
    "open_amount_minor",
    "currency",
    "reporting_open_amount_minor",
    "reporting_currency",
    "days_past_due",
    "ageing_bucket",
)
REVENUE_SCHEDULE = _dataset(
    "revenue/revenue_recognition_schedule.csv",
    "REVENUE_SUBLEDGER",
    "SOURCE_RECORD",
    "ONE_ROW_PER_INVOICE_RECOGNITION_MONTH",
    "schedule_id",
    "invoice_id",
    "subscription_id",
    "recognition_period",
    "recognition_date",
    "revenue_amount_minor",
    "currency",
    "reporting_revenue_amount_minor",
    "reporting_currency",
    "recognition_status",
)
VENDOR_INVOICES = _dataset(
    "procurement/vendor_invoices.csv",
    "PROCUREMENT",
    "SOURCE_RECORD",
    "ONE_ROW_PER_VENDOR_INVOICE",
    "vendor_invoice_id",
    "vendor_id",
    "department_id",
    "invoice_date",
    "due_date",
    "expense_account_id",
    "invoice_amount_minor",
    "tax_amount_minor",
    "currency",
    "invoice_status",
    "external_invoice_number",
)
VENDOR_PAYMENTS = _dataset(
    "procurement/vendor_payments.csv",
    "TREASURY",
    "SOURCE_RECORD",
    "ONE_ROW_PER_VENDOR_PAYMENT",
    "vendor_payment_id",
    "vendor_invoice_id",
    "vendor_id",
    "payment_date",
    "payment_amount_minor",
    "currency",
    "payment_status",
)
AP_AGEING = _dataset(
    "procurement/ap_ageing_snapshot.csv",
    "PROCUREMENT",
    "SOURCE_RECORD",
    "ONE_ROW_PER_OPEN_VENDOR_INVOICE_PER_DAILY_SNAPSHOT",
    "snapshot_date",
    "vendor_invoice_id",
    "vendor_id",
    "due_date",
    "invoice_amount_minor",
    "paid_amount_minor",
    "open_amount_minor",
    "currency",
    "reporting_open_amount_minor",
    "reporting_currency",
    "days_past_due",
    "ageing_bucket",
    "ap_status",
)
PAYROLL_LINES = _dataset(
    "workforce/payroll_expense_lines.csv",
    "PAYROLL",
    "SOURCE_RECORD",
    "ONE_ROW_PER_EMPLOYEE_PER_PAYROLL_MONTH",
    "payroll_line_id",
    "period_id",
    "employee_id",
    "department_id",
    "region_id",
    "gross_pay_minor",
    "employer_tax_minor",
    "benefits_minor",
    "total_payroll_cost_minor",
    "currency",
    "reporting_payroll_cost_minor",
    "reporting_currency",
    "payroll_status",
)
HEADCOUNT_SNAPSHOT = _dataset(
    "hris/headcount_snapshot.csv",
    "HRIS",
    "SOURCE_RECORD",
    "ONE_ROW_PER_EMPLOYEE_PER_MONTH_END",
    "snapshot_period",
    "employee_id",
    "department_id",
    "region_id",
    "employment_status",
    "fte_bps",
    "annual_salary_minor",
    "currency",
    "reporting_annual_salary_minor",
    "reporting_currency",
    "is_ghost_headcount",
)
EMPLOYEE_COMPENSATION = _dataset(
    "workforce/employee_compensation.csv",
    "HRIS",
    "SOURCE_RECORD",
    "ONE_ROW_PER_EMPLOYEE_PERIOD_COMPENSATION_COMPONENT",
    "compensation_line_id",
    "period_id",
    "employee_id",
    "department_id",
    "region_id",
    "compensation_component",
    "amount_minor",
    "currency",
    "reporting_amount_minor",
    "reporting_currency",
    "source_system",
)
HEADCOUNT_PLAN = _dataset(
    "workforce/headcount_plan.csv",
    "PLANNING",
    "PLANNING_INPUT",
    "ONE_ROW_PER_PLANNED_POSITION",
    "position_id",
    "scenario_code",
    "department_id",
    "region_id",
    "planned_hire_date",
    "role_family",
    "seniority_level",
    "salary_low_minor",
    "salary_mid_minor",
    "salary_high_minor",
    "currency",
    "reporting_salary_mid_minor",
    "reporting_currency",
    "position_status",
    "backfill_flag",
)
BUDGET_VERSIONS = _dataset(
    "planning/budget_versions.csv",
    "PLANNING",
    "PLANNING_INPUT",
    "ONE_ROW_PER_BUDGET_VERSION",
    "budget_version_ref",
    "budget_name",
    "planning_start_period",
    "planning_end_period",
    "approval_status",
    "approved_at",
    "locked_flag",
)
BUDGET_LINES = _dataset(
    "planning/budget_lines.csv",
    "PLANNING",
    "PLANNING_INPUT",
    "ONE_ROW_PER_VERSION_PERIOD_DEPARTMENT_ACCOUNT",
    "budget_line_id",
    "budget_version_ref",
    "period_id",
    "department_id",
    "account_id",
    "amount_minor",
    "currency",
    "reporting_amount_minor",
    "reporting_currency",
    "approval_status",
)
FORECAST_VERSIONS = _dataset(
    "planning/forecast_versions.csv",
    "PLANNING",
    "PLANNING_INPUT",
    "ONE_ROW_PER_FORECAST_VERSION_SCENARIO",
    "forecast_version_ref",
    "scenario_code",
    "cutover_period",
    "forecast_start_period",
    "forecast_end_period",
    "source_budget_version_ref",
    "approval_status",
    "locked_flag",
)
VARIANCE_SOURCE = _dataset(
    "planning/variance_source_extract.csv",
    "PLANNING",
    "SOURCE_SYSTEM_REPORT",
    "ONE_ROW_PER_PERIOD_DEPARTMENT_ACCOUNT",
    "variance_line_id",
    "period_id",
    "period_status",
    "department_id",
    "account_id",
    "actual_amount_minor",
    "budget_amount_minor",
    "forecast_amount_minor",
    "actual_vs_budget_variance_minor",
    "actual_vs_forecast_variance_minor",
    "forecast_vs_budget_variance_minor",
    "currency",
    "source_budget_line_ref",
    "source_forecast_line_ref",
)
DEFERRED_REVENUE_ROLLFORWARD = _dataset(
    "revenue/deferred_revenue_rollforward.csv",
    "REVENUE_SUBLEDGER",
    "SOURCE_SYSTEM_REPORT",
    "ONE_ROW_PER_PERIOD_CURRENCY",
    "period_id",
    "currency",
    "opening_deferred_revenue_minor",
    "new_billings_minor",
    "recognised_revenue_minor",
    "closing_deferred_revenue_minor",
    "reporting_opening_deferred_revenue_minor",
    "reporting_new_billings_minor",
    "reporting_recognised_revenue_minor",
    "reporting_closing_deferred_revenue_minor",
    "reporting_currency",
    "source_system",
)
FORECAST_LINES = _dataset(
    "planning/forecast_lines.csv",
    "PLANNING",
    "PLANNING_INPUT",
    "ONE_ROW_PER_SCENARIO_PERIOD_DEPARTMENT_ACCOUNT",
    "forecast_line_id",
    "forecast_version_ref",
    "scenario_code",
    "period_id",
    "department_id",
    "account_id",
    "amount_minor",
    "currency",
    "reporting_amount_minor",
    "reporting_currency",
    "assumption_basis_ref",
    "approval_status",
)
BUSINESS_EVENTS = _dataset(
    "events/business_events.csv",
    "FINANCE_EVENT_GATEWAY",
    "BUSINESS_EVENT",
    "ONE_ROW_PER_CAUSAL_BUSINESS_EVENT",
    "business_event_ref",
    "event_type",
    "source_system",
    "source_record_ref",
    "occurred_at",
    "recorded_at",
    "effective_date",
    "legal_entity_id",
    "counterparty_ref",
    "amount_minor",
    "currency",
    "reporting_amount_minor",
    "reporting_currency",
    "posting_rule_ref",
    "record_semantic_hash",
)
SOURCE_GL_LINES = _dataset(
    "accounting/source_gl_journal_lines.csv",
    "ERP",
    "SOURCE_SYSTEM_ACCOUNTING_RECORD",
    "ONE_ROW_PER_SOURCE_SYSTEM_JOURNAL_LINE",
    "source_journal_line_id",
    "source_journal_id",
    "line_no",
    "business_event_ref",
    "posting_rule_ref",
    "period_id",
    "effective_date",
    "recorded_at",
    "legal_entity_id",
    "account_id",
    "debit_minor",
    "credit_minor",
    "currency",
    "source_record_ref",
)
TRIAL_BALANCE = _dataset(
    "accounting/trial_balance.csv",
    "ERP",
    "SOURCE_SYSTEM_REPORT",
    "ONE_ROW_PER_PERIOD_ACCOUNT",
    "period_id",
    "account_id",
    "opening_balance_minor",
    "debit_activity_minor",
    "credit_activity_minor",
    "closing_balance_minor",
    "currency",
    "reporting_version_ref",
)
FINANCIAL_STATEMENTS = _dataset(
    "accounting/financial_statement_extract.csv",
    "ERP",
    "SOURCE_SYSTEM_REPORT",
    "ONE_ROW_PER_PERIOD_STATEMENT_LINE",
    "period_id",
    "statement_class",
    "statement_line",
    "amount_minor",
    "currency",
    "reporting_version_ref",
    "presentation_order",
)
OPENING_BALANCE_SHEET = _dataset(
    "accounting/opening_balance_sheet.csv",
    "ERP",
    "SOURCE_SYSTEM_REPORT",
    "ONE_ROW_PER_OPENING_BALANCE_SHEET_ACCOUNT",
    "as_of_date",
    "account_id",
    "opening_balance_minor",
    "currency",
    "source_business_event_refs",
)
DEFECT_REGISTRY = _dataset(
    "governance/defect_registry.csv",
    "SYNTHETIC_CONTROL_PLANE",
    "SYNTHETIC_DEFECT_DECLARATION",
    "ONE_ROW_PER_INTENTIONAL_DEFECT_INSTANCE",
    "defect_instance_ref",
    "defect_type",
    "source_dataset_path",
    "source_record_ref",
    "expected_detector",
    "severity",
    "expected_treatment",
    "description",
)
SOURCE_QA_RESULTS = _dataset(
    "governance/source_generation_qa_results.csv",
    "SYNTHETIC_CONTROL_PLANE",
    "SOURCE_QA_RESULT",
    "ONE_ROW_PER_GENERATION_QA_CHECK",
    "check_ref",
    "check_category",
    "expected_value",
    "actual_value",
    "status",
    "severity",
    "notes",
)
SOURCE_INVENTORY = _dataset(
    "governance/source_output_inventory.csv",
    "SYNTHETIC_CONTROL_PLANE",
    "SOURCE_INVENTORY",
    "ONE_ROW_PER_EMITTED_SOURCE_DATASET",
    "source_dataset_path",
    "source_system",
    "record_class",
    "grain",
    "row_count",
    "column_count",
)

ALL_SOURCE_DATASETS = (
    PERIODS,
    LEGAL_ENTITIES,
    REGIONS,
    FX_RATES,
    DEPARTMENTS,
    PRODUCTS,
    PRODUCT_PRICE_BOOK,
    CHART_OF_ACCOUNTS,
    CUSTOMERS,
    CRM_ACCOUNTS,
    VENDORS,
    EMPLOYEES,
    SUBSCRIPTIONS,
    SUBSCRIPTION_EVENTS,
    INVOICES,
    INVOICE_LINES,
    PAYMENTS,
    PAYMENT_ALLOCATIONS,
    AR_AGEING,
    BANK_ACCOUNTS,
    BANK_TRANSACTIONS,
    BANK_STATEMENT_LINES,
    BANK_RECONCILIATIONS,
    REVENUE_SCHEDULE,
    DEFERRED_REVENUE_ROLLFORWARD,
    VENDOR_INVOICES,
    VENDOR_INVOICE_LINES,
    VENDOR_PAYMENTS,
    AP_AGEING,
    CAPITAL_PURCHASE_ORDERS,
    CAPITAL_GOODS_RECEIPTS,
    CAPITAL_INVOICES,
    ASSET_LIFECYCLE_EVENTS,
    FIXED_ASSET_REGISTER,
    FIXED_ASSET_MOVEMENTS,
    DEBT_INSTRUMENTS,
    DEBT_SCHEDULE,
    EQUITY_MOVEMENTS,
    PAYROLL_LINES,
    HEADCOUNT_SNAPSHOT,
    EMPLOYEE_COMPENSATION,
    HEADCOUNT_PLAN,
    BUDGET_VERSIONS,
    BUDGET_LINES,
    FORECAST_VERSIONS,
    FORECAST_LINES,
    VARIANCE_SOURCE,
    BUSINESS_EVENTS,
    SOURCE_GL_LINES,
    TRIAL_BALANCE,
    FINANCIAL_STATEMENTS,
    OPENING_BALANCE_SHEET,
    DEFECT_REGISTRY,
    SOURCE_ADMISSION_RESULTS,
    FIXED_ASSET_CONTROL_RESULTS,
    LEASE_CONTRACTS,
    LEASE_LIFECYCLE_EVENTS,
    LEASE_SCHEDULE,
    TAX_CALCULATION_INPUTS,
    TAX_SCHEDULE,
    TAX_LOSS_REGISTER,
    ACCRUAL_SOURCE_EVENTS,
    ACCRUAL_SCHEDULE,
    PREPAYMENT_SOURCE_EVENTS,
    PREPAYMENT_SCHEDULE,
    STATUTORY_SUBLEDGER_CONTROL_RESULTS,
    INTERCOMPANY_TRANSACTIONS,
    INTERCOMPANY_BALANCES,
    CONSOLIDATION_ELIMINATIONS,
    ACCOUNTING_EVENTS,
    STATUTORY_TRIAL_BALANCE,
    STATUTORY_STATEMENTS,
    RETAINED_EARNINGS_BRIDGE,
    CASH_FLOW_RECONCILIATION,
    MONTHLY_CLOSE_STATUS,
    STATUTORY_RECONCILIATIONS,
    SOURCE_QA_RESULTS,
    SOURCE_INVENTORY,
)

A21_SOURCE_DATASETS = (
    LEGAL_ENTITIES,
    BANK_ACCOUNTS,
    BANK_TRANSACTIONS,
    BANK_STATEMENT_LINES,
    BANK_RECONCILIATIONS,
    DEBT_INSTRUMENTS,
    DEBT_SCHEDULE,
    EQUITY_MOVEMENTS,
)
A22_FIXED_ASSET_DATASETS = (
    CAPITAL_PURCHASE_ORDERS,
    CAPITAL_GOODS_RECEIPTS,
    CAPITAL_INVOICES,
    ASSET_LIFECYCLE_EVENTS,
    FIXED_ASSET_REGISTER,
    FIXED_ASSET_MOVEMENTS,
    SOURCE_ADMISSION_RESULTS,
    FIXED_ASSET_CONTROL_RESULTS,
)
A22B_STATUTORY_SUBLEDGER_DATASETS = (
    LEASE_CONTRACTS,
    LEASE_LIFECYCLE_EVENTS,
    LEASE_SCHEDULE,
    TAX_CALCULATION_INPUTS,
    TAX_SCHEDULE,
    TAX_LOSS_REGISTER,
    ACCRUAL_SOURCE_EVENTS,
    ACCRUAL_SCHEDULE,
    PREPAYMENT_SOURCE_EVENTS,
    PREPAYMENT_SCHEDULE,
    STATUTORY_SUBLEDGER_CONTROL_RESULTS,
)
A23_MULTI_ENTITY_CLOSE_DATASETS = (
    INTERCOMPANY_TRANSACTIONS,
    INTERCOMPANY_BALANCES,
    CONSOLIDATION_ELIMINATIONS,
    ACCOUNTING_EVENTS,
    STATUTORY_TRIAL_BALANCE,
    STATUTORY_STATEMENTS,
    RETAINED_EARNINGS_BRIDGE,
    CASH_FLOW_RECONCILIATION,
    MONTHLY_CLOSE_STATUS,
    STATUTORY_RECONCILIATIONS,
)
A2_SOURCE_DATASETS = (
    *A21_SOURCE_DATASETS,
    *A22_FIXED_ASSET_DATASETS,
    *A22B_STATUTORY_SUBLEDGER_DATASETS,
    *A23_MULTI_ENTITY_CLOSE_DATASETS,
)
A1_SOURCE_DATASETS = tuple(
    item for item in ALL_SOURCE_DATASETS if item not in A2_SOURCE_DATASETS
)
A21_PACKAGE_DATASETS = tuple(
    item
    for item in ALL_SOURCE_DATASETS
    if item not in A22_FIXED_ASSET_DATASETS
    and item not in A22B_STATUTORY_SUBLEDGER_DATASETS
    and item not in A23_MULTI_ENTITY_CLOSE_DATASETS
)
A22_PACKAGE_DATASETS = tuple(
    item
    for item in ALL_SOURCE_DATASETS
    if item not in A22B_STATUTORY_SUBLEDGER_DATASETS
    and item not in A23_MULTI_ENTITY_CLOSE_DATASETS
)
A22B_PACKAGE_DATASETS = tuple(
    item
    for item in ALL_SOURCE_DATASETS
    if item not in A23_MULTI_ENTITY_CLOSE_DATASETS
)

DATASET_BY_PATH = {item.path: item for item in ALL_SOURCE_DATASETS}

REGION_ROWS = (
    ("UK", "United Kingdom", "GBP"),
    ("US", "United States", "USD"),
    ("DE", "Germany", "EUR"),
    ("SG", "Singapore", "SGD"),
)
DEPARTMENT_ROWS = (
    ("DEP-RND", "Research and Development", "Product", "R_AND_D"),
    ("DEP-ENG", "Engineering", "Product", "R_AND_D"),
    ("DEP-SALES", "Sales", "Commercial", "SALES_AND_MARKETING"),
    ("DEP-MKT", "Marketing", "Commercial", "SALES_AND_MARKETING"),
    ("DEP-CS", "Customer Success", "Commercial", "SALES_AND_MARKETING"),
    ("DEP-FIN", "Finance", "Corporate", "GENERAL_AND_ADMINISTRATIVE"),
    ("DEP-PEOPLE", "People", "Corporate", "GENERAL_AND_ADMINISTRATIVE"),
    ("DEP-OPS", "Operations", "Corporate", "GENERAL_AND_ADMINISTRATIVE"),
)
PRODUCT_ROWS = (
    ("PROD-CORE-ESS", "Core Essentials", "CORE", "SUBSCRIPTION", 8_200),
    ("PROD-CORE-ENT", "Core Enterprise", "CORE", "SUBSCRIPTION", 8_400),
    ("PROD-ANALYTICS", "Analytics Advanced", "ANALYTICS", "SUBSCRIPTION", 8_800),
    ("PROD-AI", "AI Copilot", "AI", "USAGE_SUBSCRIPTION", 6_500),
    ("PROD-SERVICES", "Implementation Services", "SERVICES", "SERVICES", 3_500),
    ("PROD-LEGACY", "DataPulse Legacy", "LEGACY", "SUBSCRIPTION", 7_800),
)

# account_id, name, class, statement class, line, normal balance, cash flow class
ACCOUNT_ROWS = (
    ("1000", "Cash and cash equivalents", "ASSET", "BALANCE_SHEET", "cash", "DEBIT", "CASH"),
    ("1100", "Accounts receivable", "ASSET", "BALANCE_SHEET", "accounts_receivable", "DEBIT", "WORKING_CAPITAL"),
    (
        "1150",
        "Intercompany receivables",
        "ASSET",
        "BALANCE_SHEET",
        "intercompany_receivables",
        "DEBIT",
        "NON_CASH",
    ),
    ("1200", "Prepayments", "ASSET", "BALANCE_SHEET", "prepayments", "DEBIT", "WORKING_CAPITAL"),
    (
        "1250",
        "Deferred tax asset",
        "ASSET",
        "BALANCE_SHEET",
        "deferred_tax_asset",
        "DEBIT",
        "NON_CASH",
    ),
    ("1300", "Inventory", "ASSET", "BALANCE_SHEET", "inventory", "DEBIT", "WORKING_CAPITAL"),
    ("1500", "Property plant and equipment", "ASSET", "BALANCE_SHEET", "property_plant_equipment", "DEBIT", "INVESTING"),
    ("1510", "Accumulated depreciation", "ASSET", "BALANCE_SHEET", "accumulated_depreciation", "CREDIT", "NON_CASH"),
    ("1600", "Goodwill", "ASSET", "BALANCE_SHEET", "goodwill", "DEBIT", "INVESTING"),
    (
        "1610",
        "Accumulated goodwill impairment",
        "ASSET",
        "BALANCE_SHEET",
        "goodwill",
        "CREDIT",
        "NON_CASH",
    ),
    ("1700", "Intangible assets", "ASSET", "BALANCE_SHEET", "intangible_assets", "DEBIT", "INVESTING"),
    ("1710", "Accumulated amortisation", "ASSET", "BALANCE_SHEET", "accumulated_amortisation", "CREDIT", "NON_CASH"),
    ("1800", "Right of use assets", "ASSET", "BALANCE_SHEET", "right_of_use_assets", "DEBIT", "NON_CASH"),
    (
        "1810",
        "Accumulated right of use depreciation",
        "ASSET",
        "BALANCE_SHEET",
        "accumulated_right_of_use_depreciation",
        "CREDIT",
        "NON_CASH",
    ),
    ("2000", "Accounts payable", "LIABILITY", "BALANCE_SHEET", "accounts_payable", "CREDIT", "WORKING_CAPITAL"),
    (
        "2050",
        "Intercompany payables",
        "LIABILITY",
        "BALANCE_SHEET",
        "intercompany_payables",
        "CREDIT",
        "NON_CASH",
    ),
    ("2100", "Deferred revenue", "LIABILITY", "BALANCE_SHEET", "deferred_revenue", "CREDIT", "WORKING_CAPITAL"),
    ("2200", "Accrued expenses", "LIABILITY", "BALANCE_SHEET", "accrued_expenses", "CREDIT", "WORKING_CAPITAL"),
    ("2250", "Unapplied cash", "LIABILITY", "BALANCE_SHEET", "unapplied_cash", "CREDIT", "WORKING_CAPITAL"),
    ("2300", "Tax payable", "LIABILITY", "BALANCE_SHEET", "tax_payable", "CREDIT", "OPERATING"),
    ("2400", "Long term debt", "LIABILITY", "BALANCE_SHEET", "long_term_debt", "CREDIT", "FINANCING"),
    ("2500", "Lease liabilities", "LIABILITY", "BALANCE_SHEET", "lease_liabilities", "CREDIT", "FINANCING"),
    ("3000", "Share capital", "EQUITY", "BALANCE_SHEET", "share_capital", "CREDIT", "FINANCING"),
    ("3100", "Retained earnings", "EQUITY", "BALANCE_SHEET", "retained_earnings", "CREDIT", "OPERATING"),
    ("4000", "Subscription revenue", "REVENUE", "INCOME_STATEMENT", "subscription_revenue", "CREDIT", "OPERATING"),
    ("4100", "Services revenue", "REVENUE", "INCOME_STATEMENT", "services_revenue", "CREDIT", "OPERATING"),
    ("5000", "Hosting cost of revenue", "EXPENSE", "INCOME_STATEMENT", "cost_of_revenue", "DEBIT", "OPERATING"),
    ("5100", "Services cost of revenue", "EXPENSE", "INCOME_STATEMENT", "cost_of_revenue", "DEBIT", "OPERATING"),
    ("6000", "Research and development", "EXPENSE", "INCOME_STATEMENT", "research_and_development", "DEBIT", "OPERATING"),
    ("6100", "Sales and marketing", "EXPENSE", "INCOME_STATEMENT", "sales_and_marketing", "DEBIT", "OPERATING"),
    ("6200", "General and administrative", "EXPENSE", "INCOME_STATEMENT", "general_and_administrative", "DEBIT", "OPERATING"),
    ("6300", "Depreciation and amortisation", "EXPENSE", "INCOME_STATEMENT", "depreciation_and_amortisation", "DEBIT", "NON_CASH"),
    ("6500", "Interest expense", "EXPENSE", "INCOME_STATEMENT", "interest_expense", "DEBIT", "FINANCING"),
    ("6600", "Income tax expense", "EXPENSE", "INCOME_STATEMENT", "income_tax_expense", "DEBIT", "OPERATING"),
)

PLANNING_ACCOUNT_IDS = ("4000", "4100", "5000", "5100", "6000", "6100", "6200")
