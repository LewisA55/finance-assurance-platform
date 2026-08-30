{{ config(tags=['slice_b2']) }}

select
    md5(concat_ws('|', legal_entity_id, jurisdiction_code)) as tax_jurisdiction_hk,
    legal_entity_id,
    jurisdiction_code,
    max(statutory_tax_rate_bps) as latest_statutory_tax_rate_bps,
    max(deferred_tax_recognition_bps) as latest_deferred_tax_recognition_bps,
    max(currency) as currency,
    max(source_recorded_at) as latest_source_recorded_at,
    'APPROVED_TAX_INPUT' as reliability_status,
    'TAX_ANALYTICS' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest,
    max(_source_data_ref) as _source_data_ref
from {{ ref('stg_tax__tax_calculation_inputs') }}
group by legal_entity_id, jurisdiction_code
