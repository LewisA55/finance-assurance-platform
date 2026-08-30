{{ config(tags=['slice_b3']) }}

with link as (
    select object_ref, legal_entity_id,
           string_agg(business_event_ref, ',' order by effective_date, business_event_ref) as business_event_refs,
           sum(gl_journal_line_count)::bigint as gl_journal_line_count,
           sum(gl_debit_minor)::bigint as gl_debit_minor,
           sum(gl_credit_minor)::bigint as gl_credit_minor,
           max(reporting_version_ref) as reporting_version_ref,
           max(close_status) as close_status,
           max(reliability_status) as reliability_status,
           max(reliability_purpose) as reliability_purpose,
           max(source_package_digest) as source_package_digest
    from {{ ref('fct_operational_event_links') }}
    where object_type = 'CAPITAL_INVOICE'
    group by 1, 2
)
select
    md5(invoice.capital_invoice_id) as capital_invoice_hk,
    invoice.* exclude (_ingested_at, _source_file, _source_file_sha256),
    po.asset_class,
    po.asset_description,
    po.ordered_amount_minor,
    receipt.receipt_date,
    receipt.quantity_received,
    link.business_event_refs,
    coalesce(link.gl_journal_line_count, 0)::bigint as gl_journal_line_count,
    coalesce(link.gl_debit_minor, 0)::bigint as gl_debit_minor,
    coalesce(link.gl_credit_minor, 0)::bigint as gl_credit_minor,
    link.reporting_version_ref,
    link.close_status,
    coalesce(link.reliability_status, 'SOURCE_RECORD_UNPOSTED') as reliability_status,
    coalesce(link.reliability_purpose, 'CAPITAL_PROCUREMENT_SOURCE_REVIEW') as reliability_purpose,
    coalesce(link.source_package_digest, '{{ var("a24_package_digest") }}') as source_package_digest,
    link.business_event_refs is not null as is_posted_to_gl,
    asset.asset_id
from {{ ref('stg_procurement__capital_invoices') }} invoice
inner join {{ ref('fct_capital_purchase_orders') }} po
  using (capital_purchase_order_id, legal_entity_id, vendor_id)
inner join {{ ref('fct_capital_goods_receipts') }} receipt
  using (capital_goods_receipt_id, capital_purchase_order_id, legal_entity_id)
left join link on invoice.capital_invoice_id = link.object_ref
             and invoice.legal_entity_id = link.legal_entity_id
left join {{ ref('dim_fixed_asset') }} asset
  on invoice.capital_invoice_id = asset.capital_invoice_id
