{{ config(tags=['slice_b3']) }}

select
    md5(concat_ws('|', ageing.snapshot_date, ageing.vendor_invoice_id)) as ap_ageing_daily_hk,
    ageing.* exclude (_ingested_at, _source_file, _source_file_sha256),
    invoice.department_id,
    invoice.expense_account_id,
    invoice.vendor_category,
    invoice.legal_entity_id,
    strftime(ageing.snapshot_date, '%Y-%m') as period_id,
    invoice.business_event_ref,
    'RELIABLE_FOR_WORKING_CAPITAL_ANALYTICS' as reliability_status,
    'DAILY_AP_AGEING' as reliability_purpose,
    '{{ var("a24_package_digest") }}' as source_package_digest
from {{ ref('stg_procurement__ap_ageing_snapshot') }} ageing
inner join {{ ref('fct_vendor_invoices') }} invoice using (vendor_invoice_id, vendor_id)
