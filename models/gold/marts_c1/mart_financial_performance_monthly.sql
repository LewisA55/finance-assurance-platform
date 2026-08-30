{{ config(tags=['slice_c']) }}

with statement as (
    select
        period_id,
        scope_id,
        reporting_version_ref,
        currency,
        max(case when statement_line = 'subscription_revenue' then amount_minor end)::bigint as subscription_revenue_minor,
        max(case when statement_line = 'services_revenue' then amount_minor end)::bigint as services_revenue_minor,
        max(case when statement_line = 'cost_of_revenue' then amount_minor end)::bigint as cost_of_revenue_minor,
        max(case when statement_line = 'research_and_development' then amount_minor end)::bigint as research_and_development_minor,
        max(case when statement_line = 'sales_and_marketing' then amount_minor end)::bigint as sales_and_marketing_minor,
        max(case when statement_line = 'general_and_administrative' then amount_minor end)::bigint as general_and_administrative_minor,
        max(case when statement_line = 'depreciation_and_amortisation' then amount_minor end)::bigint as depreciation_and_amortisation_minor,
        max(case when statement_line = 'interest_expense' then amount_minor end)::bigint as interest_expense_minor,
        max(case when statement_line = 'income_tax_expense' then amount_minor end)::bigint as income_tax_expense_minor,
        max(case when statement_line = 'net_income' then amount_minor end)::bigint as net_income_minor,
        max(reliability_status) as reliability_status,
        max(source_package_digest) as source_package_digest
    from {{ ref('fct_statutory_statement_lines') }}
    where statement_class = 'INCOME_STATEMENT'
    group by 1, 2, 3, 4
), derived as (
    select
        *,
        (subscription_revenue_minor + services_revenue_minor)::bigint as revenue_minor,
        (subscription_revenue_minor + services_revenue_minor + cost_of_revenue_minor)::bigint as gross_profit_minor,
        (research_and_development_minor + sales_and_marketing_minor
            + general_and_administrative_minor + depreciation_and_amortisation_minor)::bigint as operating_expense_minor
    from statement
)
select
    md5(concat_ws('|', period_id, scope_id, reporting_version_ref)) as financial_performance_hk,
    period_id,
    scope_id,
    reporting_version_ref,
    currency,
    subscription_revenue_minor,
    services_revenue_minor,
    revenue_minor,
    cost_of_revenue_minor,
    gross_profit_minor,
    research_and_development_minor,
    sales_and_marketing_minor,
    general_and_administrative_minor,
    depreciation_and_amortisation_minor,
    operating_expense_minor,
    (gross_profit_minor + operating_expense_minor)::bigint as operating_profit_minor,
    (gross_profit_minor + operating_expense_minor - depreciation_and_amortisation_minor)::bigint as ebitda_minor,
    interest_expense_minor,
    (net_income_minor - income_tax_expense_minor)::bigint as profit_before_tax_minor,
    income_tax_expense_minor,
    net_income_minor,
    case when revenue_minor = 0 then null else round(10000.0 * gross_profit_minor / revenue_minor)::integer end as gross_margin_bps,
    case when revenue_minor = 0 then null else round(10000.0 * (gross_profit_minor + operating_expense_minor) / revenue_minor)::integer end as operating_margin_bps,
    case when revenue_minor = 0 then null else round(10000.0 * (gross_profit_minor + operating_expense_minor - depreciation_and_amortisation_minor) / revenue_minor)::integer end as ebitda_margin_bps,
    'STATUTORY_STATEMENT' as value_authority,
    reliability_status,
    'EXECUTIVE_FINANCIAL_PERFORMANCE' as reliability_purpose,
    'gold.fct_statutory_statement_lines' as drill_through_relation,
    source_package_digest,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from derived
