export interface RuntimeTableContract {
  tableName: string;
  expectedRows: number;
  logicalDigest: string;
  grain: string;
  reliabilityPurpose: string;
  partitionStrategy: string;
  files: string[];
  fileIntegrity: Array<{ url: string; bytes: number; digest: string }>;
}

export interface PythiaAnnualForecastRow {
  scenario_code: string;
  year: string;
  currency: string;
  revenue_minor: number;
  ebitda_minor: number;
  unlevered_free_cash_flow_minor: number;
  capex_minor: number;
  operating_cash_flow_minor: number;
  closing_cash_minor: number;
  net_debt_minor: number;
  total_assets_minor: number;
  total_liabilities_minor: number;
  total_equity_minor: number;
  cumulative_funding_requirement_minor: number;
  balance_sheet_difference_minor: number;
  cash_rollforward_difference_minor: number;
  actuals_reporting_version_ref: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  finance_delivery_digest: string;
  source_data_digest: string;
}

export interface RevenueWaterfallRow {
  period_id: string;
  currency: string;
  opening_deferred_revenue_minor: number;
  new_billings_minor: number;
  recognised_revenue_minor: number;
  closing_deferred_revenue_minor: number;
  scheduled_revenue_minor: number;
  schedule_line_count: number;
  rollforward_difference_minor: number;
  schedule_difference_minor: number;
  reporting_version_ref: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface SaasPerformanceRow {
  period_id: string;
  product_id: string;
  product_name: string;
  product_family: string;
  region_id: string;
  region_name: string;
  customer_segment: string;
  currency: string;
  beginning_mrr_minor: number;
  new_mrr_minor: number;
  expansion_mrr_minor: number;
  contraction_mrr_minor: number;
  churn_mrr_minor: number;
  fx_remeasurement_mrr_minor: number;
  ending_mrr_minor: number;
  ending_arr_minor: number;
  active_subscription_count: number;
  active_customer_count: number;
  new_subscription_count: number;
  churned_subscription_count: number;
  gross_revenue_retention_bps: number;
  net_revenue_retention_bps: number;
  reporting_version_ref: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface PresentedOperatingMetricRow {
  period_id: string;
  scope_id: string;
  reporting_version_ref: string;
  metric_id: string;
  metric_label: string;
  metric_value_minor: number | null;
  metric_value_count: number | null;
  metric_value_bps: number | null;
  currency: string;
  value_unit: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface FinancialPerformanceRow {
  period_id: string;
  scope_id: string;
  reporting_version_ref: string;
  currency: string;
  subscription_revenue_minor: number;
  services_revenue_minor: number;
  revenue_minor: number;
  cost_of_revenue_minor: number;
  gross_profit_minor: number;
  research_and_development_minor: number;
  sales_and_marketing_minor: number;
  general_and_administrative_minor: number;
  depreciation_and_amortisation_minor: number;
  operating_expense_minor: number;
  operating_profit_minor: number;
  ebitda_minor: number;
  interest_expense_minor: number;
  profit_before_tax_minor: number;
  income_tax_expense_minor: number;
  net_income_minor: number;
  gross_margin_bps: number;
  operating_margin_bps: number;
  ebitda_margin_bps: number;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface BalanceSheetRow {
  period_id: string;
  scope_id: string;
  reporting_version_ref: string;
  currency: string;
  cash_minor: number;
  accounts_receivable_minor: number;
  prepayments_minor: number;
  deferred_tax_asset_minor: number;
  net_property_plant_equipment_minor: number;
  goodwill_minor: number;
  net_intangible_assets_minor: number;
  net_right_of_use_assets_minor: number;
  accounts_payable_minor: number;
  deferred_revenue_minor: number;
  accrued_expenses_minor: number;
  tax_payable_minor: number;
  long_term_debt_minor: number;
  lease_liabilities_minor: number;
  share_capital_minor: number;
  retained_earnings_minor: number;
  total_assets_minor: number;
  total_liabilities_minor: number;
  total_equity_minor: number;
  operating_working_capital_minor: number;
  net_debt_minor: number;
  balance_sheet_difference_minor: number;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface CashFlowLiquidityRow {
  period_id: string;
  scope_id: string;
  reporting_version_ref: string;
  currency: string;
  opening_cash_minor: number;
  operating_cash_flow_minor: number;
  investing_cash_flow_minor: number;
  financing_cash_flow_minor: number;
  fx_and_other_movement_minor: number;
  net_change_in_cash_minor: number;
  closing_cash_minor: number;
  closing_debt_minor: number;
  closing_lease_liability_minor: number;
  undrawn_facility_minor: number;
  cash_interest_minor: number;
  lease_cash_payment_minor: number;
  net_debt_minor: number;
  available_liquidity_minor: number;
  unreconciled_difference_minor: number;
  reconciliation_status: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface WorkingCapitalRow {
  period_id: string;
  currency: string;
  closing_ar_minor: number;
  overdue_ar_minor: number;
  closing_trade_ap_minor: number;
  closing_capital_ap_minor: number;
  closing_ap_minor: number;
  overdue_ap_minor: number;
  billings_minor: number;
  collections_minor: number;
  purchases_minor: number;
  supplier_payments_minor: number;
  closing_deferred_revenue_minor: number;
  trade_working_capital_minor: number;
  operating_working_capital_minor: number;
  dso_days: number;
  dpo_days: number;
  overdue_ap_bps: number;
  reporting_version_ref: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface WorkingCapitalDriverRow extends WorkingCapitalRow {
  month_end: string;
  revenue_minor: number;
  prior_month_revenue_minor: number;
  revenue_change_minor: number;
  prior_operating_working_capital_minor: number;
  change_in_operating_working_capital_minor: number;
}

export interface CustomerCollectionsRow {
  period_id: string;
  region_id: string;
  region_name: string;
  customer_segment: string;
  currency: string;
  billings_minor: number;
  collections_minor: number;
  closing_ar_minor: number;
  overdue_ar_minor: number;
  invoice_count: number;
  payment_count: number;
  billed_customer_count: number;
  paying_customer_count: number;
  overdue_invoice_count: number;
  collection_efficiency_bps: number;
  dso_days: number;
  reporting_version_ref: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface CapitalStructureRow {
  period_id: string;
  scope_id: string;
  currency: string;
  opening_debt_minor: number;
  debt_drawdown_minor: number;
  debt_repayment_minor: number;
  debt_cash_interest_minor: number;
  debt_accrued_interest_minor: number;
  closing_debt_minor: number;
  undrawn_facility_minor: number;
  debt_instrument_count: number;
  opening_lease_liability_minor: number;
  lease_addition_minor: number;
  lease_cash_payment_minor: number;
  lease_interest_minor: number;
  lease_principal_reduction_minor: number;
  closing_lease_liability_minor: number;
  lease_contract_count: number;
  cash_minor: number;
  gross_debt_minor: number;
  net_debt_minor: number;
  available_liquidity_minor: number;
  reporting_version_ref: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface FixedAssetRow {
  period_id: string;
  legal_entity_id: string;
  legal_entity_name: string;
  asset_class: string;
  currency: string;
  opening_gross_book_value_minor: number;
  capex_additions_minor: number;
  gross_disposals_minor: number;
  closing_gross_book_value_minor: number;
  opening_accumulated_depreciation_minor: number;
  depreciation_minor: number;
  amortisation_minor: number;
  impairment_minor: number;
  closing_accumulated_depreciation_minor: number;
  disposal_proceeds_minor: number;
  disposal_gain_loss_minor: number;
  closing_net_book_value_minor: number;
  asset_count: number;
  resolved_business_event_count: number;
  reporting_version_ref: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface TaxEquityRow {
  period_id: string;
  scope_id: string;
  currency: string;
  profit_before_tax_minor: number;
  loss_generated_minor: number;
  loss_utilised_minor: number;
  current_tax_expense_minor: number;
  deferred_tax_movement_minor: number;
  cash_tax_paid_minor: number;
  closing_tax_payable_minor: number;
  closing_deferred_tax_asset_minor: number;
  external_equity_movement_minor: number;
  net_income_minor: number;
  dividends_minor: number;
  closing_retained_earnings_minor: number;
  reconciliation_status: string;
  reporting_version_ref: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface PresentedFinancialRow {
  period_id: string;
  month_end: string;
  fiscal_year: number;
  fiscal_quarter: string;
  scope_id: string;
  reporting_version_ref: string;
  statement_class: string;
  metric_id: string;
  metric_label: string;
  display_order: number;
  presented_amount_minor: number;
  currency: string;
  sign_convention: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  evidence_digest: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface PlanningPerformanceRow {
  period_id: string;
  period_status: string;
  department_id: string;
  department_name: string;
  business_unit: string;
  opex_class: string;
  account_id: string;
  account_name: string;
  statement_class: string;
  statement_line: string;
  currency: string;
  actual_amount_minor: number;
  budget_amount_minor: number;
  forecast_amount_minor: number;
  actual_vs_budget_variance_minor: number;
  actual_vs_forecast_variance_minor: number;
  forecast_vs_budget_variance_minor: number;
  budget_version_ref: string | null;
  forecast_version_ref: string | null;
  scenario_code: string | null;
  planning_scenario_ref: string | null;
  is_statutory_actual: boolean;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface ReportingScopeRow {
  scope_id: string;
  scope_name: string;
  scope_type: string;
  legal_entity_id: string | null;
  reporting_currency: string;
  _source_data_ref: string;
}

export interface ReportingVersionRow {
  reporting_version_ref: string;
  period_id: string;
  scope_id: string;
  scope_type: string;
  subledger_reconciliation_status: string;
  bank_reconciliation_status: string;
  intercompany_reconciliation_status: string;
  trial_balance_status: string;
  statement_status: string;
  close_status: string;
  closed_at: string;
  reliability_status: string;
  reliability_purpose: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface FinanceRuntimeManifest {
  contractVersion: string;
  deliveryRef: string;
  deliveryDigest: string;
  builtAt: string;
  sourceDataRef: string;
  sourceDataDigest: string;
  financeModelRef: string;
  financeModelDigest: string;
  semanticDigest: string;
  deliveredTableCount: number;
  deliveredRowCount: number;
  martCount: number;
  conformedDimensionCount: number;
  packageControlCount: number;
  pythiaRef?: string;
  pythiaDigest?: string;
  pythiaModelRunRef?: string;
  actualsReportingVersionRef?: string;
  pythiaControlCount?: number;
  duckdbWasm: {
    variant: "eh";
    sourceBytes: number;
    sourceDigest: string;
    parts: Array<{ url: string; bytes: number; digest: string }>;
  };
  runtimeTables: RuntimeTableContract[];
}

export interface CommandCentreRow {
  period_id: string;
  month_end: string;
  fiscal_year: number;
  fiscal_quarter: string;
  scope_id: string;
  reporting_version_ref: string;
  currency: string;
  revenue_minor: number;
  gross_profit_minor: number;
  ebitda_minor: number;
  net_income_minor: number;
  gross_margin_bps: number;
  ebitda_margin_bps: number;
  total_assets_minor: number;
  total_liabilities_minor: number;
  total_equity_minor: number;
  operating_cash_flow_minor: number;
  investing_cash_flow_minor: number;
  financing_cash_flow_minor: number;
  closing_cash_minor: number;
  gross_debt_minor: number;
  net_debt_minor: number;
  available_liquidity_minor: number;
  billings_minor: number;
  collections_minor: number;
  closing_ar_minor: number;
  overdue_ar_minor: number;
  closing_ap_minor: number;
  closing_deferred_revenue_minor: number;
  operating_working_capital_minor: number;
  dso_days: number;
  dpo_days: number;
  ending_arr_minor: number;
  active_customer_count: number;
  net_revenue_retention_bps: number | null;
  payroll_cost_minor: number;
  active_headcount_count: number;
  capex_additions_minor: number;
  closing_net_book_value_minor: number;
  not_ready_metric_count: number;
  presentation_status: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  drill_through_relation: string;
  source_package_digest: string;
  _source_data_ref: string;
}

export interface MetricReadinessRow {
  metric_id: string;
  metric_label: string;
  first_period: string;
  last_period: string;
  period_count: number;
  minimum_period_count?: number;
  null_value_count?: number;
  acceptable_null_value_count?: number;
  readiness_status: string;
  first_failure_reason?: string | null;
  value_authority: string;
  readiness_authority: string;
  reliability_status?: string;
  reliability_purpose?: string;
  drill_through_relation: string;
  source_package_digest?: string;
  _source_data_ref?: string;
}

export interface ReadinessControlRow {
  control_order: number;
  control_id: string;
  control_name: string;
  actual_value: number;
  expected_value: number;
  comparison_operator: string;
  result_status: string;
  first_failure_ref?: string | null;
  evidence_relation: string;
  validator_ref: string;
  evaluated_model_ref?: string;
  value_authority?: string;
  reliability_status?: string;
  reliability_purpose?: string;
  source_package_digest?: string;
  _source_data_ref?: string;
}

export interface RuntimePopulation {
  table_name: string;
  actual_rows: number;
}

export interface FinanceWorkspace {
  manifest: FinanceRuntimeManifest;
  commandCentre: CommandCentreRow[];
  metricReadiness: MetricReadinessRow[];
  readinessControls: ReadinessControlRow[];
  populations: RuntimePopulation[];
}

export interface RevenueSaasWarmSnapshot {
  revenueWaterfalls: RevenueWaterfallRow[];
  saasPerformance: SaasPerformanceRow[];
  operatingMetrics: PresentedOperatingMetricRow[];
}

export interface RevenueSaasWorkspace extends RevenueSaasWarmSnapshot {
  manifest: FinanceRuntimeManifest;
  populations: RuntimePopulation[];
}

export interface PackageReconciliationRow {
  control_id: string;
  table_name: string;
  actual_value: number;
  expected_value: number;
  difference: number;
  status: string;
  evidence: string;
}

export interface AssuranceWarmSnapshot {
  reportingVersions: ReportingVersionRow[];
  metricReadiness: MetricReadinessRow[];
  readinessControls: ReadinessControlRow[];
  packageReconciliations: PackageReconciliationRow[];
}

export interface AssuranceWorkspace extends AssuranceWarmSnapshot {
  manifest: FinanceRuntimeManifest;
  populations: RuntimePopulation[];
}

export interface PythiaScenarioRow {
  model_run_ref: string;
  planning_scenario_ref: string;
  scenario_code: string;
  scenario_approval_status: string;
  scenario_locked_flag: boolean;
  pythia_result_status: string;
  actuals_reporting_version_ref: string;
  cutover_period: string;
  forecast_start_period: string;
  forecast_end_period: string;
  is_governed_pythia_snapshot: boolean;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  finance_delivery_digest: string;
  source_data_digest: string;
}

export interface PythiaForecastRow {
  model_run_ref: string;
  planning_scenario_ref: string;
  scenario_code: string;
  scenario_approval_status: string;
  pythia_result_status: string;
  period_id: string;
  forecast_month_number: number;
  currency: string;
  revenue_minor: number;
  cost_of_revenue_minor: number;
  gross_profit_minor: number;
  research_and_development_minor: number;
  sales_and_marketing_minor: number;
  general_and_administrative_minor: number;
  ebitda_minor: number;
  depreciation_and_amortisation_minor: number;
  ebit_minor: number;
  interest_expense_minor: number;
  profit_before_tax_minor: number;
  income_tax_expense_minor: number;
  net_income_minor: number;
  capex_minor: number;
  change_in_operating_working_capital_minor: number;
  unlevered_free_cash_flow_minor: number;
  operating_cash_flow_minor: number;
  investing_cash_flow_minor: number;
  financing_cash_flow_minor: number;
  opening_cash_minor: number;
  closing_cash_minor: number;
  accounts_receivable_minor: number;
  net_property_plant_equipment_minor: number;
  accounts_payable_minor: number;
  deferred_revenue_minor: number;
  term_debt_minor: number;
  revolver_debt_minor: number;
  lease_liabilities_minor: number;
  net_debt_minor: number;
  available_liquidity_minor: number;
  monthly_funding_gap_minor: number;
  cumulative_funding_requirement_minor: number;
  total_assets_minor: number;
  total_liabilities_minor: number;
  total_equity_minor: number;
  balance_sheet_difference_minor: number;
  cash_rollforward_difference_minor: number;
  gross_margin_bps: number | null;
  ebitda_margin_bps: number | null;
  actuals_reporting_version_ref: string;
  assumption_set_ref: string;
  value_authority: string;
  reliability_status: string;
  reliability_purpose: string;
  finance_delivery_digest: string;
  source_data_digest: string;
}

export interface PythiaValuationRow {
  model_run_ref: string;
  scenario_code: string;
  scenario_approval_status: string;
  pythia_result_status: string;
  valuation_status: string;
  explicit_forecast_months: number;
  wacc_bps: number;
  terminal_growth_bps: number;
  explicit_period_pv_minor: number;
  terminal_year_fcf_minor: number;
  terminal_value_minor: number | null;
  present_value_terminal_minor: number | null;
  enterprise_value_minor: number;
  opening_net_debt_minor: number;
  equity_value_minor: number;
  diluted_shares: number;
  implied_value_per_share_minor: number;
  five_year_revenue_minor: number;
  five_year_ebitda_minor: number;
  five_year_unlevered_fcf_minor: number;
  first_funding_gap_period: string | null;
  peak_funding_requirement_minor: number;
  decision_status: string;
  actuals_reporting_version_ref: string;
  assumption_set_ref: string;
  value_authority: string;
  reliability_status: string;
  finance_delivery_digest: string;
  source_data_digest: string;
}

export interface PythiaSensitivityRow {
  model_run_ref: string;
  scenario_code: string;
  wacc_bps: number;
  terminal_growth_bps: number;
  valuation_status: string;
  enterprise_value_minor: number | null;
  equity_value_minor: number | null;
  implied_value_per_share_minor: number | null;
  actuals_reporting_version_ref: string;
  value_authority: string;
  finance_delivery_digest: string;
}

export interface PythiaExecutionControlRow {
  control_order: number;
  control_id: string;
  control_name: string;
  actual_value: number;
  expected_value: number;
  result_status: string;
  first_failure_ref: string | null;
  model_run_ref: string;
  value_authority: string;
}

export interface PlanningValuationWarmSnapshot {
  scenarios: PythiaScenarioRow[];
  annualForecasts: PythiaAnnualForecastRow[];
  valuations: PythiaValuationRow[];
  sensitivities: PythiaSensitivityRow[];
  executionControls: PythiaExecutionControlRow[];
}

export interface PlanningValuationWorkspace extends PlanningValuationWarmSnapshot {
  manifest: FinanceRuntimeManifest;
  populations: RuntimePopulation[];
}

export interface CashCapitalWarmSnapshot {
  balanceSheets: BalanceSheetRow[];
  cashFlows: CashFlowLiquidityRow[];
  workingCapital: WorkingCapitalRow[];
  capitalStructure: CapitalStructureRow[];
}

export interface CashCapitalWorkspace extends CashCapitalWarmSnapshot {
  manifest: FinanceRuntimeManifest;
  workingCapitalDrivers: WorkingCapitalDriverRow[];
  customerCollections: CustomerCollectionsRow[];
  fixedAssets: FixedAssetRow[];
  taxEquity: TaxEquityRow[];
  populations: RuntimePopulation[];
}

export interface FinancialPerformanceWorkspace {
  manifest: FinanceRuntimeManifest;
  financialPerformance: FinancialPerformanceRow[];
  presentedFinancials: PresentedFinancialRow[];
  planningPerformance: PlanningPerformanceRow[];
  reportingScopes: ReportingScopeRow[];
  reportingVersions: ReportingVersionRow[];
  populations: RuntimePopulation[];
}
