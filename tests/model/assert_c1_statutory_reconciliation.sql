{{ config(tags=['slice_c']) }}

with statement as (
    select period_id, scope_id, reporting_version_ref,
           sum(case when statement_class = 'INCOME_STATEMENT'
                         and statement_line in ('subscription_revenue','services_revenue')
                    then amount_minor else 0 end)::bigint as revenue_minor,
           max(case when statement_class = 'INCOME_STATEMENT' and statement_line = 'net_income'
                    then amount_minor end)::bigint as net_income_minor,
           max(case when statement_class = 'BALANCE_SHEET' and statement_line = 'total_assets'
                    then amount_minor end)::bigint as total_assets_minor,
           max(case when statement_class = 'BALANCE_SHEET' and statement_line = 'total_liabilities_and_equity'
                    then amount_minor end)::bigint as total_liabilities_and_equity_minor
    from {{ ref('fct_statutory_statement_lines') }} group by 1, 2, 3
), failures as (
    select financial.reporting_version_ref object_ref
    from {{ ref('mart_financial_performance_monthly') }} financial
    inner join statement using (period_id, scope_id, reporting_version_ref)
    where financial.revenue_minor <> statement.revenue_minor
       or financial.net_income_minor <> statement.net_income_minor
    union all
    select balance.reporting_version_ref
    from {{ ref('mart_balance_sheet_monthly') }} balance
    inner join statement using (period_id, scope_id, reporting_version_ref)
    where balance.total_assets_minor <> statement.total_assets_minor
       or balance.total_liabilities_and_equity_minor <> statement.total_liabilities_and_equity_minor
       or balance.balance_sheet_difference_minor <> 0
    union all
    select reporting_version_ref
    from {{ ref('mart_cash_flow_liquidity_monthly') }}
    where unreconciled_difference_minor <> 0 or reconciliation_status <> 'RECONCILED'
)
select * from failures
