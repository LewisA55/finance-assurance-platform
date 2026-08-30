{{ config(tags=['slice_b3']) }}

select
    md5(line.vendor_invoice_line_id) as vendor_invoice_line_hk,
    line.* exclude (_ingested_at, _source_file, _source_file_sha256),
    invoice.invoice_date,
    invoice.due_date,
    invoice.vendor_category,
    invoice.business_unit,
    invoice.opex_class,
    invoice.business_event_ref,
    invoice.legal_entity_id,
    invoice.period_id,
    invoice.reporting_version_ref,
    invoice.close_status,
    invoice.reliability_status,
    invoice.reliability_purpose,
    invoice.source_package_digest
from {{ ref('stg_procurement__vendor_invoice_lines') }} line
inner join {{ ref('fct_vendor_invoices') }} invoice
  using (vendor_invoice_id, vendor_id, department_id, expense_account_id)
