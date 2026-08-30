{{ config(tags=['slice_c']) }}

with invoice as (
    select period_id, reporting_currency as currency,
           count(distinct vendor_invoice_id)::bigint as vendor_invoice_count,
           count(distinct vendor_id)::bigint as active_vendor_count
    from {{ ref('fct_vendor_invoices') }} group by 1, 2
), payment as (
    select period_id, reporting_currency as currency,
           count(distinct vendor_payment_id)::bigint as vendor_payment_count
    from {{ ref('fct_vendor_payments') }} group by 1, 2
)
select
    md5(concat_ws('|', working.period_id, working.currency)) as ap_working_capital_hk,
    working.period_id,
    working.currency,
    working.closing_ar_minor,
    working.overdue_ar_minor,
    working.closing_trade_ap_minor,
    working.closing_capital_ap_minor,
    working.closing_ap_minor,
    working.overdue_ap_minor,
    working.billings_minor,
    working.collections_minor,
    working.purchases_minor,
    working.supplier_payments_minor,
    working.closing_deferred_revenue_minor,
    working.trade_working_capital_minor,
    working.operating_working_capital_minor,
    working.dso_days,
    working.dpo_days,
    invoice.vendor_invoice_count,
    invoice.active_vendor_count,
    payment.vendor_payment_count,
    case when working.closing_ap_minor = 0 then null else
        round(10000.0 * working.overdue_ap_minor / working.closing_ap_minor)::integer
    end as overdue_ap_bps,
    working.reporting_version_ref,
    'OPERATIONAL_EVENT_AND_STATE' as value_authority,
    working.reliability_status,
    'EXECUTIVE_AP_AND_WORKING_CAPITAL' as reliability_purpose,
    'gold.fct_working_capital_monthly|gold.fct_vendor_invoices|gold.fct_vendor_payments' as drill_through_relation,
    working.source_package_digest,
    working._source_data_ref
from {{ ref('fct_working_capital_monthly') }} working
inner join invoice using (period_id, currency)
inner join payment using (period_id, currency)
