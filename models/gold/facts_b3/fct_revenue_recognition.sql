{{ config(tags=['slice_b3']) }}

select
    md5(schedule.schedule_id) as revenue_recognition_hk,
    schedule.* exclude (_ingested_at, _source_file, _source_file_sha256),
    invoice.customer_id,
    subscription.product_id,
    subscription.region_id,
    subscription.customer_segment,
    link.business_event_ref,
    link.legal_entity_id,
    link.gl_journal_line_count,
    link.gl_debit_minor,
    link.gl_credit_minor,
    link.reporting_version_ref,
    link.close_status,
    link.reliability_status,
    link.reliability_purpose,
    link.source_package_digest
from {{ ref('stg_revenue__revenue_recognition_schedule') }} schedule
inner join {{ ref('fct_customer_invoices') }} invoice using (invoice_id, subscription_id)
inner join {{ ref('dim_subscription') }} subscription using (subscription_id, customer_id)
inner join {{ ref('fct_operational_event_links') }} link
  on link.object_type = 'REVENUE_SCHEDULE'
 and schedule.schedule_id = link.object_ref
