{{ config(tags=['slice_b3']) }}

with mapped_events as (
    select
        case
            when event_type = 'CUSTOMER_INVOICE_ISSUED' then 'CUSTOMER_INVOICE'
            when event_type = 'CASH_RECEIPT_RECORDED' then 'CUSTOMER_PAYMENT'
            when event_type = 'SUBSCRIPTION_REVENUE_RECOGNISED' then 'REVENUE_SCHEDULE'
            when event_type = 'VENDOR_INVOICE_APPROVED' then 'VENDOR_INVOICE'
            when event_type = 'VENDOR_PAYMENT_SETTLED' then 'VENDOR_PAYMENT'
            when event_type = 'PAYROLL_COST_INCURRED' then 'PAYROLL_LINE'
            when event_type in ('CAPITAL_ASSET_INVOICE_APPROVED', 'CAPITAL_ASSET_INVOICE_PAID') then 'CAPITAL_INVOICE'
        end as object_type,
        case
            when event_type = 'CAPITAL_ASSET_INVOICE_APPROVED'
                then split_part(source_record_ref, '#', 1)
            when event_type = 'CAPITAL_ASSET_INVOICE_PAID'
                then capital.capital_invoice_id
            else source_record_ref
        end as object_ref,
        event.*
    from {{ ref('fct_business_events') }} event
    left join {{ ref('stg_procurement__capital_invoices') }} capital
      on event.event_type = 'CAPITAL_ASSET_INVOICE_PAID'
     and event.source_record_ref = capital.payment_ref
    where event.event_type in (
        'CUSTOMER_INVOICE_ISSUED', 'CASH_RECEIPT_RECORDED',
        'SUBSCRIPTION_REVENUE_RECOGNISED', 'VENDOR_INVOICE_APPROVED',
        'VENDOR_PAYMENT_SETTLED', 'PAYROLL_COST_INCURRED',
        'CAPITAL_ASSET_INVOICE_APPROVED', 'CAPITAL_ASSET_INVOICE_PAID'
    )
), gl as (
    select business_event_ref, legal_entity_id,
           count(*) as gl_journal_line_count,
           sum(debit_minor)::bigint as gl_debit_minor,
           sum(credit_minor)::bigint as gl_credit_minor
    from {{ ref('fct_gl_journal_lines') }}
    group by 1, 2
)
select
    md5(concat_ws('|', event.object_type, event.object_ref, event.business_event_ref)) as operational_event_link_hk,
    event.object_type,
    event.object_ref,
    event.business_event_ref,
    event.event_type,
    event.source_system,
    event.source_record_ref,
    event.legal_entity_id,
    strftime(event.effective_date, '%Y-%m') as period_id,
    event.effective_date,
    event.recorded_at,
    event.record_semantic_hash,
    gl.gl_journal_line_count,
    gl.gl_debit_minor,
    gl.gl_credit_minor,
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest,
    event._source_data_ref
from mapped_events event
inner join gl using (business_event_ref, legal_entity_id)
inner join {{ ref('dim_reporting_version') }} version
  on strftime(event.effective_date, '%Y-%m') = version.period_id
 and event.legal_entity_id = version.scope_id
where event.object_ref is not null
