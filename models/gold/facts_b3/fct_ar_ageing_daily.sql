{{ config(tags=['slice_b3']) }}

select
    md5(concat_ws('|', ageing.snapshot_date, ageing.invoice_id)) as ar_ageing_daily_hk,
    ageing.* exclude (_ingested_at, _source_file, _source_file_sha256),
    invoice.subscription_id,
    invoice.product_id,
    invoice.region_id,
    invoice.customer_segment,
    invoice.legal_entity_id,
    strftime(ageing.snapshot_date, '%Y-%m') as period_id,
    invoice.business_event_ref,
    'RELIABLE_FOR_WORKING_CAPITAL_ANALYTICS' as reliability_status,
    'DAILY_AR_AGEING' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest
from {{ ref('stg_billing__ar_ageing_snapshot') }} ageing
inner join {{ ref('fct_customer_invoices') }} invoice using (invoice_id, customer_id)
