import { getRuntimeManifest, runQuery } from "./client";
import type {
  BalanceSheetRow,
  AssuranceWorkspace,
  CapitalStructureRow,
  CashCapitalWorkspace,
  CashFlowLiquidityRow,
  CommandCentreRow,
  CustomerCollectionsRow,
  FinancialPerformanceRow,
  FinancialPerformanceWorkspace,
  FinanceWorkspace,
  FixedAssetRow,
  MetricReadinessRow,
  PlanningPerformanceRow,
  PlanningValuationWorkspace,
  PackageReconciliationRow,
  PresentedFinancialRow,
  ReadinessControlRow,
  PresentedOperatingMetricRow,
  PythiaExecutionControlRow,
  PythiaAnnualForecastRow,
  PythiaScenarioRow,
  PythiaSensitivityRow,
  PythiaValuationRow,
  RevenueSaasWorkspace,
  RevenueWaterfallRow,
  ReportingScopeRow,
  ReportingVersionRow,
  RuntimePopulation,
  SaasPerformanceRow,
  TaxEquityRow,
  WorkingCapitalDriverRow,
  WorkingCapitalRow,
} from "./contracts";

const D1_RUNTIME_TABLES = [
  "mart_executive_cfo_command_center",
  "mart_cfo_metric_readiness",
  "mart_model_readiness_controls",
];

const D6_RUNTIME_TABLES = [
  "dim_pythia_scenario",
  "fct_pythia_forecast_monthly",
  "mart_pythia_valuation",
  "mart_pythia_dcf_sensitivity",
  "mart_pythia_execution_controls",
];

const D5_RUNTIME_TABLES = [
  "dim_reporting_version",
  "mart_cfo_metric_readiness",
  "mart_model_readiness_controls",
];

const D4_RUNTIME_TABLES = [
  "mart_revenue_waterfall_monthly",
  "mart_saas_performance_monthly",
  "mart_cfo_presented_operating_metrics",
];

const D3_RUNTIME_TABLES = [
  "mart_balance_sheet_monthly",
  "mart_cash_flow_liquidity_monthly",
  "mart_ap_working_capital_monthly",
  "mart_model_working_capital_drivers",
  "mart_o2c_customer_collections_monthly",
  "mart_capital_structure_monthly",
  "mart_fixed_asset_capex_monthly",
  "mart_tax_equity_monthly",
];

const D2_RUNTIME_TABLES = [
  "mart_financial_performance_monthly",
  "mart_cfo_presented_financials",
  "mart_planning_performance_monthly",
  "dim_reporting_scope",
  "dim_reporting_version",
];

const COMMAND_CENTRE_SQL = `
  select
    period_id,
    month_end::varchar as month_end,
    fiscal_year::integer as fiscal_year,
    fiscal_quarter,
    scope_id,
    reporting_version_ref,
    currency,
    revenue_minor::double as revenue_minor,
    gross_profit_minor::double as gross_profit_minor,
    ebitda_minor::double as ebitda_minor,
    net_income_minor::double as net_income_minor,
    gross_margin_bps::double as gross_margin_bps,
    ebitda_margin_bps::double as ebitda_margin_bps,
    total_assets_minor::double as total_assets_minor,
    total_liabilities_minor::double as total_liabilities_minor,
    total_equity_minor::double as total_equity_minor,
    operating_cash_flow_minor::double as operating_cash_flow_minor,
    investing_cash_flow_minor::double as investing_cash_flow_minor,
    financing_cash_flow_minor::double as financing_cash_flow_minor,
    closing_cash_minor::double as closing_cash_minor,
    gross_debt_minor::double as gross_debt_minor,
    net_debt_minor::double as net_debt_minor,
    available_liquidity_minor::double as available_liquidity_minor,
    billings_minor::double as billings_minor,
    collections_minor::double as collections_minor,
    closing_ar_minor::double as closing_ar_minor,
    overdue_ar_minor::double as overdue_ar_minor,
    closing_ap_minor::double as closing_ap_minor,
    closing_deferred_revenue_minor::double as closing_deferred_revenue_minor,
    operating_working_capital_minor::double as operating_working_capital_minor,
    dso_days::double as dso_days,
    dpo_days::double as dpo_days,
    ending_arr_minor::double as ending_arr_minor,
    active_customer_count::integer as active_customer_count,
    net_revenue_retention_bps::double as net_revenue_retention_bps,
    payroll_cost_minor::double as payroll_cost_minor,
    active_headcount_count::integer as active_headcount_count,
    capex_additions_minor::double as capex_additions_minor,
    closing_net_book_value_minor::double as closing_net_book_value_minor,
    not_ready_metric_count::integer as not_ready_metric_count,
    presentation_status,
    value_authority,
    reliability_status,
    reliability_purpose,
    drill_through_relation,
    source_package_digest,
    _source_data_ref
  from mart_executive_cfo_command_center
  order by period_id
`;

export async function loadFinanceWorkspace(): Promise<FinanceWorkspace> {
  const manifest = await getRuntimeManifest();
  const populationSql = manifest.runtimeTables
    .filter((table) => D1_RUNTIME_TABLES.includes(table.tableName))
    .map(
      (table) =>
        `select '${table.tableName}' as table_name, count(*)::integer as actual_rows from ${table.tableName}`,
    )
    .join(" union all ");

  const [commandCentre, metricReadiness, readinessControls, populations] =
    await Promise.all([
      runQuery<CommandCentreRow>(COMMAND_CENTRE_SQL, ["mart_executive_cfo_command_center"]),
      runQuery<MetricReadinessRow>(`
        select
          metric_id,
          metric_label,
          first_period,
          last_period,
          period_count::integer as period_count,
          readiness_status,
          value_authority,
          readiness_authority,
          drill_through_relation
        from mart_cfo_metric_readiness
        order by metric_label
      `, ["mart_cfo_metric_readiness"]),
      runQuery<ReadinessControlRow>(`
        select
          control_order::integer as control_order,
          control_id,
          control_name,
          actual_value::double as actual_value,
          expected_value::double as expected_value,
          comparison_operator,
          result_status,
          evidence_relation,
          validator_ref
        from mart_model_readiness_controls
        order by control_order
      `, ["mart_model_readiness_controls"]),
      runQuery<RuntimePopulation>(populationSql, D1_RUNTIME_TABLES),
    ]);

  return {
    manifest,
    commandCentre,
    metricReadiness,
    readinessControls,
    populations,
  };
}

export async function loadPlanningValuationWorkspace(): Promise<PlanningValuationWorkspace> {
  const manifest = await getRuntimeManifest();
  const populationSql = manifest.runtimeTables
    .filter((table) => D6_RUNTIME_TABLES.includes(table.tableName))
    .map(
      (table) =>
        `select '${table.tableName}' as table_name, count(*)::integer as actual_rows from ${table.tableName}`,
    )
    .join(" union all ");

  const [scenarios, annualForecasts, valuations, sensitivities, executionControls, populations] =
    await Promise.all([
      runQuery<PythiaScenarioRow>(`
        select * from dim_pythia_scenario
        order by case scenario_code when 'BASE' then 1 when 'BULL' then 2 else 3 end
      `, ["dim_pythia_scenario"]),
      runQuery<PythiaAnnualForecastRow>(`
        select
          scenario_code,
          substr(period_id, 1, 4) as year,
          any_value(currency) as currency,
          sum(revenue_minor)::double as revenue_minor,
          sum(ebitda_minor)::double as ebitda_minor,
          sum(unlevered_free_cash_flow_minor)::double as unlevered_free_cash_flow_minor,
          sum(capex_minor)::double as capex_minor,
          sum(operating_cash_flow_minor)::double as operating_cash_flow_minor,
          arg_max(closing_cash_minor, period_id)::double as closing_cash_minor,
          arg_max(net_debt_minor, period_id)::double as net_debt_minor,
          arg_max(total_assets_minor, period_id)::double as total_assets_minor,
          arg_max(total_liabilities_minor, period_id)::double as total_liabilities_minor,
          arg_max(total_equity_minor, period_id)::double as total_equity_minor,
          arg_max(cumulative_funding_requirement_minor, period_id)::double as cumulative_funding_requirement_minor,
          arg_max(balance_sheet_difference_minor, period_id)::double as balance_sheet_difference_minor,
          arg_max(cash_rollforward_difference_minor, period_id)::double as cash_rollforward_difference_minor,
          any_value(actuals_reporting_version_ref) as actuals_reporting_version_ref,
          any_value(value_authority) as value_authority,
          any_value(reliability_status) as reliability_status,
          any_value(reliability_purpose) as reliability_purpose,
          any_value(finance_delivery_digest) as finance_delivery_digest,
          any_value(source_data_digest) as source_data_digest
        from fct_pythia_forecast_monthly
        group by scenario_code, year
        order by case scenario_code when 'BASE' then 1 when 'BULL' then 2 else 3 end, year
      `, ["fct_pythia_forecast_monthly"]),
      runQuery<PythiaValuationRow>(`
        select * replace (
          explicit_forecast_months::integer as explicit_forecast_months,
          wacc_bps::double as wacc_bps,
          terminal_growth_bps::double as terminal_growth_bps,
          explicit_period_pv_minor::double as explicit_period_pv_minor,
          terminal_year_fcf_minor::double as terminal_year_fcf_minor,
          terminal_value_minor::double as terminal_value_minor,
          present_value_terminal_minor::double as present_value_terminal_minor,
          enterprise_value_minor::double as enterprise_value_minor,
          opening_net_debt_minor::double as opening_net_debt_minor,
          equity_value_minor::double as equity_value_minor,
          diluted_shares::double as diluted_shares,
          implied_value_per_share_minor::double as implied_value_per_share_minor,
          five_year_revenue_minor::double as five_year_revenue_minor,
          five_year_ebitda_minor::double as five_year_ebitda_minor,
          five_year_unlevered_fcf_minor::double as five_year_unlevered_fcf_minor,
          peak_funding_requirement_minor::double as peak_funding_requirement_minor
        )
        from mart_pythia_valuation
        order by case scenario_code when 'BASE' then 1 when 'BULL' then 2 else 3 end
      `, ["mart_pythia_valuation"]),
      runQuery<PythiaSensitivityRow>(`
        select * replace (
          wacc_bps::double as wacc_bps,
          terminal_growth_bps::double as terminal_growth_bps,
          enterprise_value_minor::double as enterprise_value_minor,
          equity_value_minor::double as equity_value_minor,
          implied_value_per_share_minor::double as implied_value_per_share_minor
        )
        from mart_pythia_dcf_sensitivity
        order by scenario_code, wacc_bps, terminal_growth_bps
      `, ["mart_pythia_dcf_sensitivity"]),
      runQuery<PythiaExecutionControlRow>(`
        select * replace (
          control_order::integer as control_order,
          actual_value::double as actual_value,
          expected_value::double as expected_value
        )
        from mart_pythia_execution_controls
        order by control_order
      `, ["mart_pythia_execution_controls"]),
      runQuery<RuntimePopulation>(populationSql, D6_RUNTIME_TABLES),
    ]);

  return {
    manifest,
    scenarios,
    annualForecasts,
    valuations,
    sensitivities,
    executionControls,
    populations,
  };
}

export async function loadAssuranceWorkspace(): Promise<AssuranceWorkspace> {
  const manifest = await getRuntimeManifest();
  const populationSql = manifest.runtimeTables
    .filter((table) => D5_RUNTIME_TABLES.includes(table.tableName))
    .map(
      (table) =>
        `select '${table.tableName}' as table_name, count(*)::integer as actual_rows from ${table.tableName}`,
    )
    .join(" union all ");

  const packageReconciliationRequest = fetch("/finance-data/metadata/reconciliation.json")
    .then(async (response) => {
      if (!response.ok) throw new Error("C2 package reconciliation catalogue unavailable");
      const payload = (await response.json()) as { rows: PackageReconciliationRow[] };
      return payload.rows;
    });

  const [reportingVersions, metricReadiness, readinessControls, packageReconciliations, populations] =
    await Promise.all([
      runQuery<ReportingVersionRow>(`
        select
          reporting_version_ref, period_id, scope_id, scope_type,
          subledger_reconciliation_status, bank_reconciliation_status,
          intercompany_reconciliation_status, trial_balance_status,
          statement_status, close_status, closed_at::varchar as closed_at,
          reliability_status, reliability_purpose, source_package_digest,
          _source_data_ref
        from dim_reporting_version
        order by scope_id, period_id
      `, ["dim_reporting_version"]),
      runQuery<MetricReadinessRow>(`
        select
          metric_id, metric_label, first_period, last_period,
          period_count::integer as period_count,
          minimum_period_count::integer as minimum_period_count,
          null_value_count::integer as null_value_count,
          acceptable_null_value_count::integer as acceptable_null_value_count,
          readiness_status, first_failure_reason, value_authority,
          readiness_authority, reliability_status, reliability_purpose,
          drill_through_relation, source_package_digest, _source_data_ref
        from mart_cfo_metric_readiness
        order by metric_label
      `, ["mart_cfo_metric_readiness"]),
      runQuery<ReadinessControlRow>(`
        select
          control_order::integer as control_order, control_id, control_name,
          actual_value::double as actual_value,
          expected_value::double as expected_value,
          comparison_operator, result_status, first_failure_ref,
          evidence_relation, validator_ref, evaluated_model_ref,
          value_authority, reliability_status, reliability_purpose,
          source_package_digest, _source_data_ref
        from mart_model_readiness_controls
        order by control_order
      `, ["mart_model_readiness_controls"]),
      packageReconciliationRequest,
      runQuery<RuntimePopulation>(populationSql, D5_RUNTIME_TABLES),
    ]);

  return {
    manifest,
    reportingVersions,
    metricReadiness,
    readinessControls,
    packageReconciliations,
    populations,
  };
}

export async function loadRevenueSaasWorkspace(): Promise<RevenueSaasWorkspace> {
  const manifest = await getRuntimeManifest();
  const populationSql = manifest.runtimeTables
    .filter((table) => D4_RUNTIME_TABLES.includes(table.tableName))
    .map(
      (table) =>
        `select '${table.tableName}' as table_name, count(*)::integer as actual_rows from ${table.tableName}`,
    )
    .join(" union all ");

  const [revenueWaterfalls, saasPerformance, operatingMetrics, populations] =
    await Promise.all([
      runQuery<RevenueWaterfallRow>(`
        select
          period_id, currency,
          opening_deferred_revenue_minor::double as opening_deferred_revenue_minor,
          new_billings_minor::double as new_billings_minor,
          recognised_revenue_minor::double as recognised_revenue_minor,
          closing_deferred_revenue_minor::double as closing_deferred_revenue_minor,
          scheduled_revenue_minor::double as scheduled_revenue_minor,
          schedule_line_count::integer as schedule_line_count,
          rollforward_difference_minor::double as rollforward_difference_minor,
          schedule_difference_minor::double as schedule_difference_minor,
          reporting_version_ref, value_authority, reliability_status,
          reliability_purpose, drill_through_relation, source_package_digest,
          _source_data_ref
        from mart_revenue_waterfall_monthly
        order by period_id
      `, ["mart_revenue_waterfall_monthly"]),
      runQuery<SaasPerformanceRow>(`
        select
          period_id, product_id, product_name, product_family,
          region_id, region_name, customer_segment, currency,
          beginning_mrr_minor::double as beginning_mrr_minor,
          new_mrr_minor::double as new_mrr_minor,
          expansion_mrr_minor::double as expansion_mrr_minor,
          contraction_mrr_minor::double as contraction_mrr_minor,
          churn_mrr_minor::double as churn_mrr_minor,
          fx_remeasurement_mrr_minor::double as fx_remeasurement_mrr_minor,
          ending_mrr_minor::double as ending_mrr_minor,
          ending_arr_minor::double as ending_arr_minor,
          active_subscription_count::integer as active_subscription_count,
          active_customer_count::integer as active_customer_count,
          new_subscription_count::integer as new_subscription_count,
          churned_subscription_count::integer as churned_subscription_count,
          gross_revenue_retention_bps::double as gross_revenue_retention_bps,
          net_revenue_retention_bps::double as net_revenue_retention_bps,
          reporting_version_ref, value_authority, reliability_status,
          reliability_purpose, drill_through_relation, source_package_digest,
          _source_data_ref
        from mart_saas_performance_monthly
        order by period_id, product_name, region_name, customer_segment
      `, ["mart_saas_performance_monthly"]),
      runQuery<PresentedOperatingMetricRow>(`
        select
          period_id, scope_id, reporting_version_ref, metric_id, metric_label,
          metric_value_minor::double as metric_value_minor,
          metric_value_count::integer as metric_value_count,
          metric_value_bps::double as metric_value_bps,
          currency, value_unit, value_authority, reliability_status,
          reliability_purpose, drill_through_relation, source_package_digest,
          _source_data_ref
        from mart_cfo_presented_operating_metrics
        order by period_id, metric_id
      `, ["mart_cfo_presented_operating_metrics"]),
      runQuery<RuntimePopulation>(populationSql, D4_RUNTIME_TABLES),
    ]);

  return {
    manifest,
    revenueWaterfalls,
    saasPerformance,
    operatingMetrics,
    populations,
  };
}

export async function loadCashCapitalWorkspace(): Promise<CashCapitalWorkspace> {
  const manifest = await getRuntimeManifest();
  const populationSql = manifest.runtimeTables
    .filter((table) => D3_RUNTIME_TABLES.includes(table.tableName))
    .map(
      (table) =>
        `select '${table.tableName}' as table_name, count(*)::integer as actual_rows from ${table.tableName}`,
    )
    .join(" union all ");

  const [
    balanceSheets,
    cashFlows,
    workingCapitalRows,
    workingCapitalDrivers,
    customerCollections,
    capitalStructure,
    fixedAssets,
    taxEquity,
    populations,
  ] = await Promise.all([
    runQuery<BalanceSheetRow>(`
      select
        period_id, scope_id, reporting_version_ref, currency,
        cash_minor::double as cash_minor,
        accounts_receivable_minor::double as accounts_receivable_minor,
        prepayments_minor::double as prepayments_minor,
        deferred_tax_asset_minor::double as deferred_tax_asset_minor,
        net_property_plant_equipment_minor::double as net_property_plant_equipment_minor,
        goodwill_minor::double as goodwill_minor,
        net_intangible_assets_minor::double as net_intangible_assets_minor,
        net_right_of_use_assets_minor::double as net_right_of_use_assets_minor,
        accounts_payable_minor::double as accounts_payable_minor,
        deferred_revenue_minor::double as deferred_revenue_minor,
        accrued_expenses_minor::double as accrued_expenses_minor,
        tax_payable_minor::double as tax_payable_minor,
        long_term_debt_minor::double as long_term_debt_minor,
        lease_liabilities_minor::double as lease_liabilities_minor,
        share_capital_minor::double as share_capital_minor,
        retained_earnings_minor::double as retained_earnings_minor,
        total_assets_minor::double as total_assets_minor,
        total_liabilities_minor::double as total_liabilities_minor,
        total_equity_minor::double as total_equity_minor,
        operating_working_capital_minor::double as operating_working_capital_minor,
        net_debt_minor::double as net_debt_minor,
        balance_sheet_difference_minor::double as balance_sheet_difference_minor,
        value_authority, reliability_status, reliability_purpose,
        drill_through_relation, source_package_digest, _source_data_ref
      from mart_balance_sheet_monthly
      order by scope_id, period_id
    `, ["mart_balance_sheet_monthly"]),
    runQuery<CashFlowLiquidityRow>(`
      select
        period_id, scope_id, reporting_version_ref, currency,
        opening_cash_minor::double as opening_cash_minor,
        operating_cash_flow_minor::double as operating_cash_flow_minor,
        investing_cash_flow_minor::double as investing_cash_flow_minor,
        financing_cash_flow_minor::double as financing_cash_flow_minor,
        fx_and_other_movement_minor::double as fx_and_other_movement_minor,
        net_change_in_cash_minor::double as net_change_in_cash_minor,
        closing_cash_minor::double as closing_cash_minor,
        closing_debt_minor::double as closing_debt_minor,
        closing_lease_liability_minor::double as closing_lease_liability_minor,
        undrawn_facility_minor::double as undrawn_facility_minor,
        cash_interest_minor::double as cash_interest_minor,
        lease_cash_payment_minor::double as lease_cash_payment_minor,
        net_debt_minor::double as net_debt_minor,
        available_liquidity_minor::double as available_liquidity_minor,
        unreconciled_difference_minor::double as unreconciled_difference_minor,
        reconciliation_status, value_authority, reliability_status,
        reliability_purpose, drill_through_relation, source_package_digest,
        _source_data_ref
      from mart_cash_flow_liquidity_monthly
      order by scope_id, period_id
    `, ["mart_cash_flow_liquidity_monthly"]),
    runQuery<WorkingCapitalRow>(`
      select
        period_id, currency,
        closing_ar_minor::double as closing_ar_minor,
        overdue_ar_minor::double as overdue_ar_minor,
        closing_trade_ap_minor::double as closing_trade_ap_minor,
        closing_capital_ap_minor::double as closing_capital_ap_minor,
        closing_ap_minor::double as closing_ap_minor,
        overdue_ap_minor::double as overdue_ap_minor,
        billings_minor::double as billings_minor,
        collections_minor::double as collections_minor,
        purchases_minor::double as purchases_minor,
        supplier_payments_minor::double as supplier_payments_minor,
        closing_deferred_revenue_minor::double as closing_deferred_revenue_minor,
        trade_working_capital_minor::double as trade_working_capital_minor,
        operating_working_capital_minor::double as operating_working_capital_minor,
        dso_days::double as dso_days, dpo_days::double as dpo_days,
        overdue_ap_bps::double as overdue_ap_bps,
        reporting_version_ref, value_authority, reliability_status,
        reliability_purpose, drill_through_relation, source_package_digest,
        _source_data_ref
      from mart_ap_working_capital_monthly
      order by period_id
    `, ["mart_ap_working_capital_monthly"]),
    runQuery<WorkingCapitalDriverRow>(`
      select
        period_id, month_end::varchar as month_end, currency,
        revenue_minor::double as revenue_minor,
        prior_month_revenue_minor::double as prior_month_revenue_minor,
        revenue_change_minor::double as revenue_change_minor,
        billings_minor::double as billings_minor,
        collections_minor::double as collections_minor,
        closing_ar_minor::double as closing_ar_minor,
        overdue_ar_minor::double as overdue_ar_minor,
        purchases_minor::double as purchases_minor,
        supplier_payments_minor::double as supplier_payments_minor,
        closing_trade_ap_minor::double as closing_trade_ap_minor,
        closing_capital_ap_minor::double as closing_capital_ap_minor,
        closing_ap_minor::double as closing_ap_minor,
        overdue_ap_minor::double as overdue_ap_minor,
        closing_deferred_revenue_minor::double as closing_deferred_revenue_minor,
        trade_working_capital_minor::double as trade_working_capital_minor,
        operating_working_capital_minor::double as operating_working_capital_minor,
        prior_operating_working_capital_minor::double as prior_operating_working_capital_minor,
        change_in_operating_working_capital_minor::double as change_in_operating_working_capital_minor,
        dso_days::double as dso_days, dpo_days::double as dpo_days,
        0::double as overdue_ap_bps,
        reporting_version_ref, value_authority, reliability_status,
        reliability_purpose, drill_through_relation, source_package_digest,
        _source_data_ref
      from mart_model_working_capital_drivers
      order by period_id
    `, ["mart_model_working_capital_drivers"]),
    runQuery<CustomerCollectionsRow>(`
      select
        period_id, region_id, region_name, customer_segment, currency,
        billings_minor::double as billings_minor,
        collections_minor::double as collections_minor,
        closing_ar_minor::double as closing_ar_minor,
        overdue_ar_minor::double as overdue_ar_minor,
        invoice_count::integer as invoice_count,
        payment_count::integer as payment_count,
        billed_customer_count::integer as billed_customer_count,
        paying_customer_count::integer as paying_customer_count,
        overdue_invoice_count::integer as overdue_invoice_count,
        collection_efficiency_bps::double as collection_efficiency_bps,
        dso_days::double as dso_days,
        reporting_version_ref, value_authority, reliability_status,
        reliability_purpose, drill_through_relation, source_package_digest,
        _source_data_ref
      from mart_o2c_customer_collections_monthly
      order by period_id, region_name, customer_segment
    `, ["mart_o2c_customer_collections_monthly"]),
    runQuery<CapitalStructureRow>(`
      select
        period_id, scope_id, currency,
        opening_debt_minor::double as opening_debt_minor,
        debt_drawdown_minor::double as debt_drawdown_minor,
        debt_repayment_minor::double as debt_repayment_minor,
        debt_cash_interest_minor::double as debt_cash_interest_minor,
        debt_accrued_interest_minor::double as debt_accrued_interest_minor,
        closing_debt_minor::double as closing_debt_minor,
        undrawn_facility_minor::double as undrawn_facility_minor,
        debt_instrument_count::integer as debt_instrument_count,
        opening_lease_liability_minor::double as opening_lease_liability_minor,
        lease_addition_minor::double as lease_addition_minor,
        lease_cash_payment_minor::double as lease_cash_payment_minor,
        lease_interest_minor::double as lease_interest_minor,
        lease_principal_reduction_minor::double as lease_principal_reduction_minor,
        closing_lease_liability_minor::double as closing_lease_liability_minor,
        lease_contract_count::integer as lease_contract_count,
        cash_minor::double as cash_minor,
        gross_debt_minor::double as gross_debt_minor,
        net_debt_minor::double as net_debt_minor,
        available_liquidity_minor::double as available_liquidity_minor,
        reporting_version_ref, value_authority, reliability_status,
        reliability_purpose, drill_through_relation, source_package_digest,
        _source_data_ref
      from mart_capital_structure_monthly
      order by scope_id, period_id
    `, ["mart_capital_structure_monthly"]),
    runQuery<FixedAssetRow>(`
      select
        period_id, legal_entity_id, legal_entity_name, asset_class, currency,
        opening_gross_book_value_minor::double as opening_gross_book_value_minor,
        capex_additions_minor::double as capex_additions_minor,
        gross_disposals_minor::double as gross_disposals_minor,
        closing_gross_book_value_minor::double as closing_gross_book_value_minor,
        opening_accumulated_depreciation_minor::double as opening_accumulated_depreciation_minor,
        depreciation_minor::double as depreciation_minor,
        amortisation_minor::double as amortisation_minor,
        impairment_minor::double as impairment_minor,
        closing_accumulated_depreciation_minor::double as closing_accumulated_depreciation_minor,
        disposal_proceeds_minor::double as disposal_proceeds_minor,
        disposal_gain_loss_minor::double as disposal_gain_loss_minor,
        closing_net_book_value_minor::double as closing_net_book_value_minor,
        asset_count::integer as asset_count,
        resolved_business_event_count::integer as resolved_business_event_count,
        reporting_version_ref, value_authority, reliability_status,
        reliability_purpose, drill_through_relation, source_package_digest,
        _source_data_ref
      from mart_fixed_asset_capex_monthly
      order by period_id, legal_entity_id, asset_class
    `, ["mart_fixed_asset_capex_monthly"]),
    runQuery<TaxEquityRow>(`
      select
        period_id, scope_id, currency,
        profit_before_tax_minor::double as profit_before_tax_minor,
        loss_generated_minor::double as loss_generated_minor,
        loss_utilised_minor::double as loss_utilised_minor,
        current_tax_expense_minor::double as current_tax_expense_minor,
        deferred_tax_movement_minor::double as deferred_tax_movement_minor,
        cash_tax_paid_minor::double as cash_tax_paid_minor,
        closing_tax_payable_minor::double as closing_tax_payable_minor,
        closing_deferred_tax_asset_minor::double as closing_deferred_tax_asset_minor,
        external_equity_movement_minor::double as external_equity_movement_minor,
        net_income_minor::double as net_income_minor,
        dividends_minor::double as dividends_minor,
        closing_retained_earnings_minor::double as closing_retained_earnings_minor,
        reconciliation_status, reporting_version_ref, value_authority,
        reliability_status, reliability_purpose, drill_through_relation,
        source_package_digest, _source_data_ref
      from mart_tax_equity_monthly
      order by scope_id, period_id
    `, ["mart_tax_equity_monthly"]),
    runQuery<RuntimePopulation>(populationSql, D3_RUNTIME_TABLES),
  ]);

  return {
    manifest,
    balanceSheets,
    cashFlows,
    workingCapital: workingCapitalRows,
    workingCapitalDrivers,
    customerCollections,
    capitalStructure,
    fixedAssets,
    taxEquity,
    populations,
  };
}

const FINANCIAL_PERFORMANCE_SQL = `
  select
    period_id,
    scope_id,
    reporting_version_ref,
    currency,
    subscription_revenue_minor::double as subscription_revenue_minor,
    services_revenue_minor::double as services_revenue_minor,
    revenue_minor::double as revenue_minor,
    cost_of_revenue_minor::double as cost_of_revenue_minor,
    gross_profit_minor::double as gross_profit_minor,
    research_and_development_minor::double as research_and_development_minor,
    sales_and_marketing_minor::double as sales_and_marketing_minor,
    general_and_administrative_minor::double as general_and_administrative_minor,
    depreciation_and_amortisation_minor::double as depreciation_and_amortisation_minor,
    operating_expense_minor::double as operating_expense_minor,
    operating_profit_minor::double as operating_profit_minor,
    ebitda_minor::double as ebitda_minor,
    interest_expense_minor::double as interest_expense_minor,
    profit_before_tax_minor::double as profit_before_tax_minor,
    income_tax_expense_minor::double as income_tax_expense_minor,
    net_income_minor::double as net_income_minor,
    gross_margin_bps::double as gross_margin_bps,
    operating_margin_bps::double as operating_margin_bps,
    ebitda_margin_bps::double as ebitda_margin_bps,
    value_authority,
    reliability_status,
    reliability_purpose,
    drill_through_relation,
    source_package_digest,
    _source_data_ref
  from mart_financial_performance_monthly
  order by scope_id, period_id
`;

export async function loadFinancialPerformanceWorkspace(): Promise<FinancialPerformanceWorkspace> {
  const manifest = await getRuntimeManifest();
  const populationSql = manifest.runtimeTables
    .filter((table) => D2_RUNTIME_TABLES.includes(table.tableName))
    .map(
      (table) =>
        `select '${table.tableName}' as table_name, count(*)::integer as actual_rows from ${table.tableName}`,
    )
    .join(" union all ");

  const [
    financialPerformance,
    presentedFinancials,
    planningPerformance,
    reportingScopes,
    reportingVersions,
    populations,
  ] = await Promise.all([
    runQuery<FinancialPerformanceRow>(FINANCIAL_PERFORMANCE_SQL, [
      "mart_financial_performance_monthly",
    ]),
    runQuery<PresentedFinancialRow>(`
      select
        period_id,
        month_end::varchar as month_end,
        fiscal_year::integer as fiscal_year,
        fiscal_quarter,
        scope_id,
        reporting_version_ref,
        statement_class,
        metric_id,
        metric_label,
        display_order::integer as display_order,
        presented_amount_minor::double as presented_amount_minor,
        currency,
        sign_convention,
        value_authority,
        reliability_status,
        reliability_purpose,
        drill_through_relation,
        evidence_digest,
        source_package_digest,
        _source_data_ref
      from mart_cfo_presented_financials
      order by scope_id, period_id, statement_class, display_order
    `, ["mart_cfo_presented_financials"]),
    runQuery<PlanningPerformanceRow>(`
      select
        period_id,
        period_status,
        department_id,
        department_name,
        business_unit,
        opex_class,
        account_id,
        account_name,
        statement_class,
        statement_line,
        currency,
        actual_amount_minor::double as actual_amount_minor,
        budget_amount_minor::double as budget_amount_minor,
        forecast_amount_minor::double as forecast_amount_minor,
        actual_vs_budget_variance_minor::double as actual_vs_budget_variance_minor,
        actual_vs_forecast_variance_minor::double as actual_vs_forecast_variance_minor,
        forecast_vs_budget_variance_minor::double as forecast_vs_budget_variance_minor,
        budget_version_ref,
        forecast_version_ref,
        scenario_code,
        planning_scenario_ref,
        is_statutory_actual,
        value_authority,
        reliability_status,
        reliability_purpose,
        drill_through_relation,
        source_package_digest,
        _source_data_ref
      from mart_planning_performance_monthly
      order by period_id, statement_line, department_id, account_id
    `, ["mart_planning_performance_monthly"]),
    runQuery<ReportingScopeRow>(`
      select
        scope_id,
        scope_name,
        scope_type,
        legal_entity_id,
        reporting_currency,
        _source_data_ref
      from dim_reporting_scope
      order by case when scope_type = 'CONSOLIDATED_GROUP' then 0 else 1 end, scope_name
    `, ["dim_reporting_scope"]),
    runQuery<ReportingVersionRow>(`
      select
        reporting_version_ref,
        period_id,
        scope_id,
        scope_type,
        subledger_reconciliation_status,
        bank_reconciliation_status,
        intercompany_reconciliation_status,
        trial_balance_status,
        statement_status,
        close_status,
        closed_at::varchar as closed_at,
        reliability_status,
        reliability_purpose,
        source_package_digest,
        _source_data_ref
      from dim_reporting_version
      order by scope_id, period_id
    `, ["dim_reporting_version"]),
    runQuery<RuntimePopulation>(populationSql, D2_RUNTIME_TABLES),
  ]);

  return {
    manifest,
    financialPerformance,
    presentedFinancials,
    planningPerformance,
    reportingScopes,
    reportingVersions,
    populations,
  };
}
