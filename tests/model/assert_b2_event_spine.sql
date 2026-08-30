{{ config(tags=['slice_b2']) }}

select subledger_event_link_hk
from {{ ref('fct_subledger_event_links') }}
where event_type is null
   or record_semantic_hash is null
   or reporting_version_ref is null
   or close_status <> 'HARD_CLOSED'
   or reliability_status <> 'RELIABLE_FOR_STATUTORY_ACTUALS'
   or gl_journal_line_count = 0
