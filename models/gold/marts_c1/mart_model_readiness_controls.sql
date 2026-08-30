{{ config(tags=['slice_c']) }}

with reporting_periods as (
    select period_id
    from {{ ref('dim_reporting_version') }}
    where scope_id = 'NEXUS-GROUP'
      and close_status = 'HARD_CLOSED'
      and reliability_status = 'RELIABLE_FOR_STATUTORY_ACTUALS'
), observations as (
    select 1 as control_order, 'C1-RDY-01' as control_id,
           'Statutory actuals history months' as control_name,
           (select count(*) from reporting_periods)::bigint as actual_value,
           60::bigint as expected_value, 'GREATER_THAN_OR_EQUAL' as comparison_operator,
           case when (select count(*) from reporting_periods) < 60 then 'HISTORY_LT_60_MONTHS' end as first_failure_ref,
           'gold.dim_reporting_version' as evidence_relation
    union all
    select 2, 'C1-RDY-02', 'Group balance-sheet month coverage',
           (select count(*) from {{ ref('mart_balance_sheet_monthly') }} where scope_id = 'NEXUS-GROUP')::bigint,
           (select count(*) from reporting_periods)::bigint, 'EQUAL',
           (select min(period.period_id) from reporting_periods period
            left join {{ ref('mart_balance_sheet_monthly') }} balance
              on period.period_id = balance.period_id and balance.scope_id = 'NEXUS-GROUP'
            where balance.period_id is null),
           'gold.mart_balance_sheet_monthly'
    union all
    select 3, 'C1-RDY-03', 'Balance-sheet equation failures',
           (select count(*) from {{ ref('mart_balance_sheet_monthly') }} where balance_sheet_difference_minor <> 0)::bigint,
           0::bigint, 'EQUAL',
           (select min(reporting_version_ref) from {{ ref('mart_balance_sheet_monthly') }} where balance_sheet_difference_minor <> 0),
           'gold.mart_balance_sheet_monthly'
    union all
    select 4, 'C1-RDY-04', 'Cash-flow reconciliation failures',
           (select count(*) from {{ ref('mart_cash_flow_liquidity_monthly') }}
            where unreconciled_difference_minor <> 0 or reconciliation_status <> 'RECONCILED')::bigint,
           0::bigint, 'EQUAL',
           (select min(reporting_version_ref) from {{ ref('mart_cash_flow_liquidity_monthly') }}
            where unreconciled_difference_minor <> 0 or reconciliation_status <> 'RECONCILED'),
           'gold.mart_cash_flow_liquidity_monthly'
    union all
    select 5, 'C1-RDY-05', 'Model actuals group month coverage',
           (select count(distinct period_id) from {{ ref('mart_model_actuals_feed') }} where scope_id = 'NEXUS-GROUP')::bigint,
           (select count(*) from reporting_periods)::bigint, 'EQUAL',
           null, 'gold.mart_model_actuals_feed'
    union all
    select 6, 'C1-RDY-06', 'Working-capital driver month coverage',
           (select count(distinct period_id) from {{ ref('mart_model_working_capital_drivers') }})::bigint,
           (select count(distinct working.period_id)
            from {{ ref('mart_ap_working_capital_monthly') }} working
            inner join {{ ref('mart_financial_performance_monthly') }} financial
              on working.period_id = financial.period_id
             and working.currency = financial.currency
             and financial.scope_id = 'NEXUS-GROUP')::bigint, 'EQUAL',
           (select min(eligible.period_id)
            from (
                select distinct working.period_id
                from {{ ref('mart_ap_working_capital_monthly') }} working
                inner join {{ ref('mart_financial_performance_monthly') }} financial
                  on working.period_id = financial.period_id
                 and working.currency = financial.currency
                 and financial.scope_id = 'NEXUS-GROUP'
            ) eligible
            left join {{ ref('mart_model_working_capital_drivers') }} served using (period_id)
            where served.period_id is null),
           'gold.mart_model_working_capital_drivers'
    union all
    select 7, 'C1-RDY-07', 'Fixed-asset schedule month coverage',
           (select count(distinct period_id) from {{ ref('mart_model_capital_schedules') }} where schedule_domain = 'FIXED_ASSET')::bigint,
           (select count(distinct period_id) from {{ ref('fct_fixed_asset_movements') }})::bigint, 'EQUAL',
           null, 'gold.mart_model_capital_schedules'
    union all
    select 8, 'C1-RDY-08', 'Debt schedule month coverage',
           (select count(distinct period_id) from {{ ref('mart_model_capital_schedules') }} where schedule_domain = 'DEBT')::bigint,
           (select count(distinct period_id) from {{ ref('fct_debt_schedule') }})::bigint, 'EQUAL',
           null, 'gold.mart_model_capital_schedules'
    union all
    select 9, 'C1-RDY-09', 'Lease schedule month coverage',
           (select count(distinct period_id) from {{ ref('mart_model_capital_schedules') }} where schedule_domain = 'LEASE')::bigint,
           (select count(distinct period_id) from {{ ref('fct_lease_schedule') }})::bigint, 'EQUAL',
           null, 'gold.mart_model_capital_schedules'
    union all
    select 10, 'C1-RDY-10', 'Tax schedule month coverage',
           (select count(distinct period_id) from {{ ref('mart_model_capital_schedules') }} where schedule_domain = 'TAX')::bigint,
           (select count(distinct period_id) from {{ ref('fct_tax_schedule') }})::bigint, 'EQUAL',
           null, 'gold.mart_model_capital_schedules'
    union all
    select 11, 'C1-RDY-11', 'SaaS performance month coverage',
           (select count(distinct period_id) from {{ ref('mart_saas_performance_monthly') }})::bigint,
           (select count(distinct saas.period_id) from {{ ref('fct_saas_monthly_movements') }} saas
            inner join {{ ref('dim_reporting_version') }} version
              on saas.period_id = version.period_id and version.scope_id = 'NEXUS-GROUP')::bigint, 'EQUAL',
           null, 'gold.mart_saas_performance_monthly'
    union all
    select 12, 'C1-RDY-12', 'Scenario actuals-boundary failures',
           (select count(*) from {{ ref('dim_planning_scenario') }} scenario
            left join {{ ref('dim_reporting_version') }} actuals
              on scenario.actuals_reporting_version_ref = actuals.reporting_version_ref
            where actuals.reporting_version_ref is null
               or scenario.cutover_period <> actuals.period_id
               or actuals.scope_id <> 'NEXUS-GROUP'
               or actuals.reliability_status <> 'RELIABLE_FOR_STATUTORY_ACTUALS'
               or scenario.actuals_source_package_digest <> actuals.source_package_digest)::bigint,
           0::bigint, 'EQUAL',
           (select min(scenario.planning_scenario_ref) from {{ ref('dim_planning_scenario') }} scenario
            left join {{ ref('dim_reporting_version') }} actuals
              on scenario.actuals_reporting_version_ref = actuals.reporting_version_ref
            where actuals.reporting_version_ref is null
               or scenario.cutover_period <> actuals.period_id
               or actuals.scope_id <> 'NEXUS-GROUP'
               or actuals.reliability_status <> 'RELIABLE_FOR_STATUTORY_ACTUALS'
               or scenario.actuals_source_package_digest <> actuals.source_package_digest),
           'gold.dim_planning_scenario|gold.dim_reporting_version'
    union all
    select 13, 'C1-RDY-13', 'Approved locked BASE scenario count',
           (select count(*) from {{ ref('dim_planning_scenario') }}
            where scenario_code = 'BASE' and approval_status = 'APPROVED' and locked_flag)::bigint,
           1::bigint, 'EQUAL',
           case when (select count(*) from {{ ref('dim_planning_scenario') }}
                      where scenario_code = 'BASE' and approval_status = 'APPROVED' and locked_flag) <> 1
                then 'BASE_SCENARIO_NOT_UNIQUE_APPROVED_LOCKED' end,
           'gold.dim_planning_scenario'
    union all
    select 14, 'C1-RDY-14', 'Planning truth-class failures',
           (select count(*) from {{ ref('mart_planning_performance_monthly') }}
            where is_statutory_actual or value_authority <> 'MANAGEMENT_SOURCE_REPORT')::bigint,
           0::bigint, 'EQUAL',
           (select min(planning_performance_hk) from {{ ref('mart_planning_performance_monthly') }}
            where is_statutory_actual or value_authority <> 'MANAGEMENT_SOURCE_REPORT'),
           'gold.mart_planning_performance_monthly'
    union all
    select 15, 'C1-RDY-15', 'Executive metric readiness failures',
           (select count(*) from {{ ref('mart_cfo_metric_readiness') }} where readiness_status <> 'READY')::bigint,
           0::bigint, 'EQUAL',
           (select min(metric_id) from {{ ref('mart_cfo_metric_readiness') }} where readiness_status <> 'READY'),
           'gold.mart_cfo_metric_readiness'
)
select
    md5(control_id) as model_readiness_control_hk,
    control_order,
    control_id,
    control_name,
    actual_value,
    expected_value,
    comparison_operator,
    case
        when comparison_operator = 'EQUAL' and actual_value = expected_value then 'PASS'
        when comparison_operator = 'GREATER_THAN_OR_EQUAL' and actual_value >= expected_value then 'PASS'
        else 'FAIL'
    end as result_status,
    first_failure_ref,
    evidence_relation,
    'C1-MODEL-READINESS@v1' as validator_ref,
    '{{ var("finance_model_ref") }}' as evaluated_model_ref,
    'VALIDATOR_PRODUCED' as value_authority,
    'RELIABLE_FOR_MODEL_READINESS_ASSESSMENT' as reliability_status,
    'MODEL_SERVING_READINESS_CONTROLS' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from observations
