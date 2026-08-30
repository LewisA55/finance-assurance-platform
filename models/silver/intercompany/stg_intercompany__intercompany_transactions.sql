{{ config(tags=['slice_b2']) }}

select
    trim(intercompany_transaction_id) as intercompany_transaction_id,
    trim(period_id) as period_id,
    trim(seller_entity_id) as seller_entity_id,
    trim(buyer_entity_id) as buyer_entity_id,
    upper(trim(transaction_type)) as transaction_type,
    trim(seller_source_record_ref) as seller_source_record_ref,
    trim(buyer_source_record_ref) as buyer_source_record_ref,
    cast(transaction_date as date) as transaction_date,
    trim(buyer_expense_account_id) as buyer_expense_account_id,
    cast(amount_minor as bigint) as amount_minor,
    upper(trim(currency)) as currency,
    trim(transfer_pricing_policy_ref) as transfer_pricing_policy_ref,
    upper(trim(settlement_status)) as settlement_status,
    cast(source_recorded_at as timestamptz) as source_recorded_at,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'intercompany__intercompany_transactions') }}
