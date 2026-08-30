with source_refs as (
    select distinct _source_data_ref from {{ ref('stg_reference__periods') }}
    union all select distinct _source_data_ref from {{ ref('stg_reference__legal_entities') }}
    union all select distinct _source_data_ref from {{ ref('stg_accounting__chart_of_accounts') }}
    union all select distinct _source_data_ref from {{ ref('stg_events__business_events') }}
    union all select distinct _source_data_ref from {{ ref('stg_accounting__accounting_events') }}
    union all select distinct _source_data_ref from {{ ref('stg_accounting__source_gl_journal_lines') }}
    union all select distinct _source_data_ref from {{ ref('stg_consolidation__elimination_journal_lines') }}
    union all select distinct _source_data_ref from {{ ref('stg_accounting__statutory_trial_balance') }}
    union all select distinct _source_data_ref from {{ ref('stg_accounting__statutory_statement_lines') }}
    union all select distinct _source_data_ref from {{ ref('stg_accounting__retained_earnings_bridge') }}
    union all select distinct _source_data_ref from {{ ref('stg_accounting__cash_flow_reconciliation') }}
    union all select distinct _source_data_ref from {{ ref('stg_accounting__monthly_close_status') }}
    union all select distinct _source_data_ref from {{ ref('stg_governance__statutory_reconciliation_results') }}
)
select *
from source_refs
where _source_data_ref <> '{{ var("a24_data_ref") }}'
   or _source_data_ref is null
