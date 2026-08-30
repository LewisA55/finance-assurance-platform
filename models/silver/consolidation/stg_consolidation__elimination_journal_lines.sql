select
    trim(elimination_journal_line_id) as elimination_journal_line_id,
    trim(elimination_journal_id) as elimination_journal_id,
    cast(line_no as integer) as line_no,
    trim(period_id) as period_id,
    trim(accounting_event_ref) as accounting_event_ref,
    trim(source_intercompany_transaction_id) as source_intercompany_transaction_id,
    trim(account_id) as account_id,
    cast(debit_minor as bigint) as debit_minor,
    cast(credit_minor as bigint) as credit_minor,
    upper(trim(currency)) as currency,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'consolidation__elimination_journal_lines') }}
