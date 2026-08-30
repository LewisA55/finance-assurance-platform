{{ config(tags=['slice_b3']) }}

select
    md5(allocation.allocation_id) as payment_allocation_hk,
    allocation.* exclude (_ingested_at, _source_file, _source_file_sha256),
    invoice.customer_id,
    invoice.subscription_id,
    invoice.product_id,
    invoice.legal_entity_id,
    strftime(allocation.allocation_date, '%Y-%m') as period_id,
    invoice.reporting_version_ref,
    invoice.close_status,
    invoice.reliability_status,
    invoice.reliability_purpose,
    invoice.source_package_digest
from {{ ref('stg_billing__payment_allocations') }} allocation
inner join {{ ref('fct_customer_invoices') }} invoice using (invoice_id)
inner join {{ ref('fct_customer_payments') }} payment using (payment_id, customer_id)
