{{ config(tags=['slice_b2']) }}

select
    md5(lease.lease_contract_id) as lease_contract_hk,
    lease.lease_contract_id,
    lease.legal_entity_id,
    entity.legal_entity_name,
    lease.lessor_ref,
    lease.lease_class,
    lease.commencement_date,
    lease.maturity_date,
    lease.payment_frequency,
    lease.payment_minor,
    lease.currency,
    lease.incremental_borrowing_rate_bps,
    lease.initial_liability_minor,
    lease.initial_rou_asset_minor,
    lease.lease_status,
    lease.approval_ref,
    lease.source_recorded_at,
    'SOURCE_MASTER_DATA' as reliability_status,
    'LEASE_ANALYTICS' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest,
    lease._source_row_hash,
    lease._source_data_ref
from {{ ref('stg_leases__lease_contracts') }} as lease
inner join {{ ref('dim_legal_entity') }} as entity using (legal_entity_id)
