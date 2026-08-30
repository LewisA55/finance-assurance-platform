{{ config(tags=['slice_b3']) }}

select
    md5(line.invoice_line_id) as customer_invoice_line_hk,
    line.* exclude (_ingested_at, _source_file, _source_file_sha256),
    invoice.customer_id,
    invoice.subscription_id,
    invoice.invoice_date,
    invoice.service_period_start,
    invoice.service_period_end,
    invoice.business_event_ref,
    invoice.legal_entity_id,
    invoice.period_id,
    invoice.reporting_version_ref,
    invoice.close_status,
    invoice.reliability_status,
    invoice.reliability_purpose,
    invoice.source_package_digest
from {{ ref('stg_billing__invoice_lines') }} line
inner join {{ ref('fct_customer_invoices') }} invoice using (invoice_id)
