{{ config(tags=['slice_b2']) }}

select
    md5(account.bank_account_id) as bank_account_hk,
    account.bank_account_id,
    account.legal_entity_id,
    entity.legal_entity_name,
    account.bank_name,
    account.account_type,
    account.currency,
    account.opened_date,
    account.closed_date,
    account.linked_facility_id,
    account.status,
    'SOURCE_MASTER_DATA' as reliability_status,
    'TREASURY_ANALYTICS' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest,
    account._source_row_hash,
    account._source_data_ref
from {{ ref('stg_treasury__bank_accounts') }} as account
inner join {{ ref('dim_legal_entity') }} as entity using (legal_entity_id)
