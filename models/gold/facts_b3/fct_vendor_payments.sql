{{ config(tags=['slice_b3']) }}

select
    md5(payment.vendor_payment_id) as vendor_payment_hk,
    payment.* exclude (_ingested_at, _source_file, _source_file_sha256),
    invoice.department_id,
    invoice.expense_account_id,
    invoice.vendor_category,
    link.business_event_ref,
    link.legal_entity_id,
    link.period_id,
    link.gl_journal_line_count,
    link.gl_debit_minor,
    link.gl_credit_minor,
    link.reporting_version_ref,
    link.close_status,
    link.reliability_status,
    link.reliability_purpose,
    link.source_package_digest
from {{ ref('stg_procurement__vendor_payments') }} payment
inner join {{ ref('fct_vendor_invoices') }} invoice using (vendor_invoice_id, vendor_id)
inner join {{ ref('fct_operational_event_links') }} link
  on link.object_type = 'VENDOR_PAYMENT'
 and payment.vendor_payment_id = link.object_ref
