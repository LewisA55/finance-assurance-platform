{{ config(tags=['slice_b2']) }}

select
    md5(debt.debt_instrument_id) as debt_instrument_hk,
    debt.debt_instrument_id,
    debt.legal_entity_id,
    entity.legal_entity_name,
    debt.lender_name,
    debt.facility_type,
    debt.currency,
    debt.facility_limit_minor,
    debt.start_date,
    debt.maturity_date,
    debt.fixed_rate_bps,
    debt.margin_bps,
    debt.base_rate_ref,
    debt.repayment_profile,
    debt.covenant_policy_ref,
    debt.instrument_status,
    'SOURCE_MASTER_DATA' as reliability_status,
    'DEBT_AND_LIQUIDITY_ANALYTICS' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest,
    debt._source_row_hash,
    debt._source_data_ref
from {{ ref('stg_treasury__debt_instruments') }} as debt
inner join {{ ref('dim_legal_entity') }} as entity using (legal_entity_id)
