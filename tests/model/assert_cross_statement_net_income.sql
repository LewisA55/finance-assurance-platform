with statement_income as (
    select period_id, scope_id, reporting_version_ref,
           max(case when statement_class = 'INCOME_STATEMENT' and statement_line = 'net_income' then amount_minor end) as income_statement_minor,
           max(case when statement_class = 'CASH_FLOW' and statement_line = 'net_income' then amount_minor end) as cash_flow_minor
    from {{ ref('fct_statutory_statement_lines') }}
    group by 1, 2, 3
)
select statement.period_id, statement.scope_id, statement.reporting_version_ref
from statement_income as statement
inner join {{ ref('fct_retained_earnings_bridge') }} as retained
    on statement.reporting_version_ref = retained.reporting_version_ref
where statement.income_statement_minor <> statement.cash_flow_minor
   or statement.income_statement_minor <> retained.net_income_minor
