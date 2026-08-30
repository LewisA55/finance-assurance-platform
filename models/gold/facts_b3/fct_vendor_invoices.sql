{{ config(tags=['slice_b3']) }}

select
    md5(invoice.vendor_invoice_id) as vendor_invoice_hk,
    invoice.* exclude (_ingested_at, _source_file, _source_file_sha256),
    vendor.category as vendor_category,
    vendor.region_id,
    department.business_unit,
    department.opex_class,
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
from {{ ref('stg_procurement__vendor_invoices') }} invoice
inner join {{ ref('dim_vendor') }} vendor using (vendor_id)
inner join {{ ref('dim_department') }} department using (department_id)
inner join {{ ref('dim_gl_account') }} account on invoice.expense_account_id = account.account_id
inner join {{ ref('fct_operational_event_links') }} link
  on link.object_type = 'VENDOR_INVOICE'
 and invoice.vendor_invoice_id = link.object_ref
