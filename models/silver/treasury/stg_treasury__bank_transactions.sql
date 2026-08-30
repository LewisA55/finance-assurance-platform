{{ config(tags=['slice_b2']) }}

select
    trim(bank_transaction_id) as bank_transaction_id,
    trim(bank_account_id) as bank_account_id,
    trim(legal_entity_id) as legal_entity_id,
    cast(value_date as date) as value_date,
    cast(book_date as date) as book_date,
    upper(trim(transaction_type)) as transaction_type,
    trim(source_record_ref) as source_record_ref,
    trim(business_event_ref) as business_event_ref,
    cast(amount_minor as bigint) as amount_minor,
    upper(trim(currency)) as currency,
    upper(trim(bank_status)) as bank_status,
    upper(trim(reconciliation_status)) as reconciliation_status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'treasury__bank_transactions') }}
