select
    md5(line.elimination_journal_line_id) as elimination_journal_line_hk,
    line.elimination_journal_line_id,
    line.elimination_journal_id,
    line.line_no,
    line.period_id,
    line.accounting_event_ref,
    line.source_intercompany_transaction_id,
    line.account_id,
    line.debit_minor,
    line.credit_minor,
    line.debit_minor - line.credit_minor as signed_amount_minor,
    line.currency,
    event.record_semantic_hash as accounting_event_semantic_hash,
    event.governance_basis_ref,
    line._source_row_hash,
    line._source_data_ref
from {{ ref('stg_consolidation__elimination_journal_lines') }} as line
left join {{ ref('stg_accounting__accounting_events') }} as event
    on line.accounting_event_ref = event.accounting_event_ref
