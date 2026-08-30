{{ config(tags=['slice_b3']) }}

select
    md5(payment.payment_id) as customer_payment_hk,
    payment.* exclude (_ingested_at, _source_file, _source_file_sha256),
    customer.region_id,
    customer.segment as customer_segment,
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
from {{ ref('stg_billing__payments') }} payment
inner join {{ ref('dim_customer') }} customer using (customer_id)
inner join {{ ref('fct_operational_event_links') }} link
  on link.object_type = 'CUSTOMER_PAYMENT'
 and payment.payment_id = link.object_ref
