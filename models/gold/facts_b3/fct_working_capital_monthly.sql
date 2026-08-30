{{ config(tags=['slice_b3']) }}

with ar as (
    select period_id, reporting_currency as currency,
           sum(reporting_open_amount_minor)::bigint as closing_ar_minor,
           sum(case when days_past_due > 0 then reporting_open_amount_minor else 0 end)::bigint as overdue_ar_minor
    from {{ ref('fct_ar_ageing_daily') }}
    where snapshot_date = last_day(snapshot_date)
    group by 1, 2
), capital_ap as (
    select
        period.period_id,
        invoice.currency,
        sum(invoice.invoice_amount_minor)::bigint as closing_capital_ap_minor
    from {{ ref('dim_period') }} period
    inner join {{ ref('fct_capital_invoices') }} invoice
      on invoice.is_posted_to_gl
     and invoice.invoice_date <= period.month_end
     and (invoice.payment_date is null or invoice.payment_date > period.month_end)
    group by 1, 2
), ap as (
    select period_id, reporting_currency as currency,
           sum(reporting_open_amount_minor)::bigint as closing_trade_ap_minor,
           sum(case when days_past_due > 0 then reporting_open_amount_minor else 0 end)::bigint as overdue_ap_minor
    from {{ ref('fct_ap_ageing_daily') }}
    where snapshot_date = last_day(snapshot_date)
    group by 1, 2
), billings as (
    select period_id, reporting_currency as currency,
           sum(reporting_amount_minor)::bigint as billings_minor
    from {{ ref('fct_customer_invoices') }} group by 1, 2
), collections as (
    select period_id, reporting_currency as currency,
           sum(reporting_amount_minor)::bigint as collections_minor
    from {{ ref('fct_customer_payments') }} group by 1, 2
), purchases as (
    select period_id, reporting_currency as currency,
           sum(reporting_amount_minor)::bigint as purchases_minor
    from {{ ref('fct_vendor_invoices') }} group by 1, 2
), supplier_payments as (
    select period_id, reporting_currency as currency,
           sum(reporting_amount_minor)::bigint as supplier_payments_minor
    from {{ ref('fct_vendor_payments') }} group by 1, 2
), deferred as (
    select period_id, reporting_currency as currency,
           sum(reporting_closing_deferred_revenue_minor)::bigint as closing_deferred_revenue_minor
    from {{ ref('fct_deferred_revenue_rollforward') }} group by 1, 2
), assembled as (
    select
        ar.period_id, ar.currency, ar.closing_ar_minor, ar.overdue_ar_minor,
        ap.closing_trade_ap_minor,
        coalesce(capital_ap.closing_capital_ap_minor, 0)::bigint as closing_capital_ap_minor,
        (ap.closing_trade_ap_minor + coalesce(capital_ap.closing_capital_ap_minor, 0))::bigint as closing_ap_minor,
        ap.overdue_ap_minor,
        billings.billings_minor, collections.collections_minor,
        purchases.purchases_minor, supplier_payments.supplier_payments_minor,
        deferred.closing_deferred_revenue_minor
    from ar
    inner join ap using (period_id, currency)
    left join capital_ap using (period_id, currency)
    inner join billings using (period_id, currency)
    inner join collections using (period_id, currency)
    inner join purchases using (period_id, currency)
    inner join supplier_payments using (period_id, currency)
    inner join deferred using (period_id, currency)
)
select
    md5(concat_ws('|', assembled.period_id, assembled.currency)) as working_capital_monthly_hk,
    assembled.*,
    (closing_ar_minor - closing_trade_ap_minor)::bigint as trade_working_capital_minor,
    (closing_ar_minor - closing_trade_ap_minor - closing_deferred_revenue_minor)::bigint as operating_working_capital_minor,
    case when billings_minor = 0 then null else
        cast(round(30.4375 * closing_ar_minor / billings_minor, 4) as decimal(18,4))
    end as dso_days,
    case when purchases_minor = 0 then null else
        cast(round(30.4375 * closing_trade_ap_minor / purchases_minor, 4) as decimal(18,4))
    end as dpo_days,
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from assembled
inner join {{ ref('dim_reporting_version') }} version
  on assembled.period_id = version.period_id
 and version.scope_id = 'NEXUS-GROUP'
