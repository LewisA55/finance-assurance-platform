with populations as (
    select 'dim_period' as model_name, (select count(*) from {{ ref('dim_period') }}) as actual_rows, (select count(*) from {{ ref('stg_reference__periods') }}) as expected_rows
    union all select 'dim_legal_entity', (select count(*) from {{ ref('dim_legal_entity') }}), (select count(*) from {{ ref('stg_reference__legal_entities') }})
    union all select 'dim_reporting_scope', (select count(*) from {{ ref('dim_reporting_scope') }}), (select count(*) + 1 from {{ ref('stg_reference__legal_entities') }})
    union all select 'dim_gl_account', (select count(*) from {{ ref('dim_gl_account') }}), (select count(*) from {{ ref('stg_accounting__chart_of_accounts') }})
    union all select 'dim_reporting_version', (select count(*) from {{ ref('dim_reporting_version') }}), (select count(*) from {{ ref('stg_accounting__monthly_close_status') }})
    union all select 'fct_business_events', (select count(*) from {{ ref('fct_business_events') }}), (select count(*) from {{ ref('stg_events__business_events') }})
    union all select 'fct_accounting_events', (select count(*) from {{ ref('fct_accounting_events') }}), (select count(*) from {{ ref('stg_accounting__accounting_events') }})
    union all select 'fct_gl_journal_lines', (select count(*) from {{ ref('fct_gl_journal_lines') }}), (select count(*) from {{ ref('stg_accounting__source_gl_journal_lines') }})
    union all select 'fct_elimination_journal_lines', (select count(*) from {{ ref('fct_elimination_journal_lines') }}), (select count(*) from {{ ref('stg_consolidation__elimination_journal_lines') }})
    union all select 'fct_statutory_trial_balance', (select count(*) from {{ ref('fct_statutory_trial_balance') }}), (select count(*) from {{ ref('stg_accounting__statutory_trial_balance') }})
    union all select 'fct_statutory_statement_lines', (select count(*) from {{ ref('fct_statutory_statement_lines') }}), (select count(*) from {{ ref('stg_accounting__statutory_statement_lines') }})
    union all select 'fct_retained_earnings_bridge', (select count(*) from {{ ref('fct_retained_earnings_bridge') }}), (select count(*) from {{ ref('stg_accounting__retained_earnings_bridge') }})
    union all select 'fct_cash_flow_reconciliation', (select count(*) from {{ ref('fct_cash_flow_reconciliation') }}), (select count(*) from {{ ref('stg_accounting__cash_flow_reconciliation') }})
    union all select 'fct_monthly_close_status', (select count(*) from {{ ref('fct_monthly_close_status') }}), (select count(*) from {{ ref('stg_accounting__monthly_close_status') }})
    union all select 'fct_statutory_reconciliations', (select count(*) from {{ ref('fct_statutory_reconciliations') }}), (select count(*) from {{ ref('stg_governance__statutory_reconciliation_results') }})
)
select * from populations where actual_rows <> expected_rows
