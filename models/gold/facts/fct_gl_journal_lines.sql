select
    md5(line.source_journal_line_id) as gl_journal_line_hk,
    line.source_journal_line_id,
    line.source_journal_id,
    line.line_no,
    line.business_event_ref,
    line.posting_rule_ref,
    line.period_id,
    line.effective_date,
    line.recorded_at,
    line.legal_entity_id,
    line.account_id,
    line.debit_minor,
    line.credit_minor,
    line.debit_minor - line.credit_minor as signed_amount_minor,
    line.currency,
    line.source_record_ref,
    event.event_type,
    event.source_system,
    event.record_semantic_hash as business_event_semantic_hash,
    'POSTED_SOURCE_LEDGER' as reliability_status,
    'LEDGER_ACTUALS' as reliability_purpose,
    line._source_row_hash,
    line._source_file,
    line._source_file_sha256,
    line._source_data_ref
from {{ ref('stg_accounting__source_gl_journal_lines') }} as line
left join {{ ref('stg_events__business_events') }} as event
    on line.business_event_ref = event.business_event_ref
