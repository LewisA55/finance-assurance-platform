{{ config(tags=['slice_c']) }}

select
    md5(concat_ws('|', statement.reporting_version_ref, statement.statement_class, statement.statement_line)) as cfo_presented_financial_hk,
    statement.period_id,
    period.month_end,
    period.fiscal_year,
    period.fiscal_quarter,
    statement.scope_id,
    statement.reporting_version_ref,
    statement.statement_class,
    statement.statement_line as metric_id,
    replace(statement.statement_line, '_', ' ') as metric_label,
    statement.presentation_order as display_order,
    statement.amount_minor as presented_amount_minor,
    statement.currency,
    case
        when statement.statement_class = 'INCOME_STATEMENT' then 'POSITIVE_REVENUE_NEGATIVE_EXPENSE'
        when statement.statement_class = 'BALANCE_SHEET' then 'POSITIVE_PRESENTED_BALANCE'
        else 'POSITIVE_INFLOW_NEGATIVE_OUTFLOW'
    end as sign_convention,
    'STATUTORY_STATEMENT' as value_authority,
    statement.reliability_status,
    'CFO_PRESENTED_FINANCIALS' as reliability_purpose,
    'gold.fct_statutory_statement_lines' as drill_through_relation,
    statement.source_trial_balance_digest as evidence_digest,
    statement.source_package_digest,
    statement._source_data_ref
from {{ ref('fct_statutory_statement_lines') }} statement
inner join {{ ref('dim_period') }} period using (period_id)
