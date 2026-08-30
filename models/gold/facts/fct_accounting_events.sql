select
    md5(event.accounting_event_ref) as accounting_event_hk,
    event.accounting_event_ref,
    event.accounting_event_type,
    event.occurred_at,
    event.effective_date,
    event.period_id,
    event.legal_entity_id,
    event.governance_basis_ref,
    event.source_record_refs,
    event.record_semantic_hash,
    event._source_row_hash,
    event._source_data_ref
from {{ ref('stg_accounting__accounting_events') }} as event
