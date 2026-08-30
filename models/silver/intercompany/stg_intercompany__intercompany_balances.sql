{{ config(tags=['slice_b2']) }}

select
    trim(period_id) as period_id,
    trim(seller_entity_id) as seller_entity_id,
    trim(buyer_entity_id) as buyer_entity_id,
    cast(seller_receivable_minor as bigint) as seller_receivable_minor,
    cast(buyer_payable_minor as bigint) as buyer_payable_minor,
    cast(confirmed_difference_minor as bigint) as confirmed_difference_minor,
    upper(trim(currency)) as currency,
    upper(trim(confirmation_status)) as confirmation_status,
    trim(seller_confirmation_ref) as seller_confirmation_ref,
    trim(buyer_confirmation_ref) as buyer_confirmation_ref,
    cast(confirmed_at as timestamptz) as confirmed_at,
    trim(evidence_ref) as evidence_ref,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'intercompany__intercompany_balances') }}
