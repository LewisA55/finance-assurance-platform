{{ config(tags=['slice_c']) }}

with invoice as (
    select period_id, region_id, customer_segment, reporting_currency as currency,
           sum(reporting_amount_minor)::bigint as billings_minor,
           count(distinct invoice_id)::bigint as invoice_count,
           count(distinct customer_id)::bigint as billed_customer_count
    from {{ ref('fct_customer_invoices') }} group by 1, 2, 3, 4
), payment as (
    select period_id, region_id, customer_segment, reporting_currency as currency,
           sum(reporting_amount_minor)::bigint as collections_minor,
           count(distinct payment_id)::bigint as payment_count,
           count(distinct customer_id)::bigint as paying_customer_count
    from {{ ref('fct_customer_payments') }} group by 1, 2, 3, 4
), ageing as (
    select period_id, region_id, customer_segment, reporting_currency as currency,
           sum(reporting_open_amount_minor)::bigint as closing_ar_minor,
           sum(case when days_past_due > 0 then reporting_open_amount_minor else 0 end)::bigint as overdue_ar_minor,
           count(distinct case when days_past_due > 0 then invoice_id end)::bigint as overdue_invoice_count
    from {{ ref('fct_ar_ageing_daily') }}
    where snapshot_date = last_day(snapshot_date)
    group by 1, 2, 3, 4
), keys as (
    select period_id, region_id, customer_segment, currency from invoice
    union select period_id, region_id, customer_segment, currency from payment
    union select period_id, region_id, customer_segment, currency from ageing
)
select
    md5(concat_ws('|', keys.period_id, keys.region_id, keys.customer_segment, keys.currency)) as o2c_customer_collections_hk,
    keys.period_id,
    keys.region_id,
    region.region_name,
    keys.customer_segment,
    keys.currency,
    coalesce(invoice.billings_minor, 0)::bigint as billings_minor,
    coalesce(payment.collections_minor, 0)::bigint as collections_minor,
    coalesce(ageing.closing_ar_minor, 0)::bigint as closing_ar_minor,
    coalesce(ageing.overdue_ar_minor, 0)::bigint as overdue_ar_minor,
    coalesce(invoice.invoice_count, 0)::bigint as invoice_count,
    coalesce(payment.payment_count, 0)::bigint as payment_count,
    coalesce(invoice.billed_customer_count, 0)::bigint as billed_customer_count,
    coalesce(payment.paying_customer_count, 0)::bigint as paying_customer_count,
    coalesce(ageing.overdue_invoice_count, 0)::bigint as overdue_invoice_count,
    case when coalesce(invoice.billings_minor, 0) = 0 then null else
        round(10000.0 * coalesce(payment.collections_minor, 0) / invoice.billings_minor)::integer
    end as collection_efficiency_bps,
    case when coalesce(invoice.billings_minor, 0) = 0 then null else
        cast(round(30.4375 * coalesce(ageing.closing_ar_minor, 0) / invoice.billings_minor, 4) as decimal(18,4))
    end as dso_days,
    version.reporting_version_ref,
    'OPERATIONAL_EVENT_AND_STATE' as value_authority,
    'RELIABLE_FOR_O2C_ANALYTICS' as reliability_status,
    'EXECUTIVE_CUSTOMER_COLLECTIONS' as reliability_purpose,
    'gold.fct_customer_invoices|gold.fct_customer_payments|gold.fct_ar_ageing_daily' as drill_through_relation,
    version.source_package_digest,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from keys
left join invoice using (period_id, region_id, customer_segment, currency)
left join payment using (period_id, region_id, customer_segment, currency)
left join ageing using (period_id, region_id, customer_segment, currency)
inner join {{ ref('dim_region') }} region using (region_id)
inner join {{ ref('dim_reporting_version') }} version
  on keys.period_id = version.period_id and version.scope_id = 'NEXUS-GROUP'
