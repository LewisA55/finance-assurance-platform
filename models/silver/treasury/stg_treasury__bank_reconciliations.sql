{{ config(tags=['slice_b2']) }}

select
    trim(period_id) as period_id,
    trim(bank_account_id) as bank_account_id,
    cast(statement_closing_minor as bigint) as statement_closing_minor,
    cast(gl_cash_closing_minor as bigint) as gl_cash_closing_minor,
    cast(outstanding_receipts_minor as bigint) as outstanding_receipts_minor,
    cast(outstanding_disbursements_minor as bigint) as outstanding_disbursements_minor,
    cast(other_reconciling_items_minor as bigint) as other_reconciling_items_minor,
    cast(unreconciled_difference_minor as bigint) as unreconciled_difference_minor,
    upper(trim(currency)) as currency,
    upper(trim(reconciliation_status)) as reconciliation_status,
    trim(evidence_ref) as evidence_ref,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'treasury__bank_reconciliations') }}
