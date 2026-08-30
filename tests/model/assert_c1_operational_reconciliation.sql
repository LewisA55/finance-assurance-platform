{{ config(tags=['slice_c']) }}

with o2c_mart as (
    select period_id, sum(billings_minor)::bigint billings_minor,
           sum(collections_minor)::bigint collections_minor,
           sum(closing_ar_minor)::bigint closing_ar_minor
    from {{ ref('mart_o2c_customer_collections_monthly') }} group by 1
), o2c_source as (
    select period_id,
           (select sum(reporting_amount_minor) from {{ ref('fct_customer_invoices') }} invoice where invoice.period_id = period.period_id)::bigint billings_minor,
           (select sum(reporting_amount_minor) from {{ ref('fct_customer_payments') }} payment where payment.period_id = period.period_id)::bigint collections_minor,
           (select sum(reporting_open_amount_minor) from {{ ref('fct_ar_ageing_daily') }} ageing
             where ageing.period_id = period.period_id and snapshot_date = last_day(snapshot_date))::bigint closing_ar_minor
    from {{ ref('dim_period') }} period where period.is_actual_period
), workforce_mart as (
    select sum(payroll_cost_minor)::bigint payroll_minor from {{ ref('mart_workforce_cost_monthly') }}
), workforce_source as (
    select sum(reporting_payroll_cost_minor)::bigint payroll_minor from {{ ref('fct_payroll_expense_lines') }}
), failures as (
    select mart.period_id object_ref from o2c_mart mart inner join o2c_source source using (period_id)
    where mart.billings_minor <> source.billings_minor
       or mart.collections_minor <> source.collections_minor
       or mart.closing_ar_minor <> source.closing_ar_minor
    union all
    select 'WORKFORCE' from workforce_mart mart cross join workforce_source source
    where mart.payroll_minor <> source.payroll_minor
    union all
    select period_id from {{ ref('mart_revenue_waterfall_monthly') }}
    where rollforward_difference_minor <> 0 or schedule_difference_minor <> 0
)
select * from failures
