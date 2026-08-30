{{ config(tags=['slice_c']) }}

with debt_entity as (
    select period_id, legal_entity_id as scope_id, currency,
           sum(opening_principal_minor)::bigint as opening_debt_minor,
           sum(drawdown_minor)::bigint as debt_drawdown_minor,
           sum(principal_repayment_minor)::bigint as debt_repayment_minor,
           sum(cash_interest_minor)::bigint as debt_cash_interest_minor,
           sum(accrued_interest_minor)::bigint as debt_accrued_interest_minor,
           sum(closing_principal_minor)::bigint as closing_debt_minor,
           sum(undrawn_facility_minor)::bigint as undrawn_facility_minor,
           count(distinct debt_instrument_id)::bigint as debt_instrument_count
    from {{ ref('fct_debt_schedule') }} group by 1, 2, 3
), debt as (
    select * from debt_entity
    union all
    select period_id, 'NEXUS-GROUP', currency,
           sum(opening_debt_minor)::bigint, sum(debt_drawdown_minor)::bigint,
           sum(debt_repayment_minor)::bigint, sum(debt_cash_interest_minor)::bigint,
           sum(debt_accrued_interest_minor)::bigint, sum(closing_debt_minor)::bigint,
           sum(undrawn_facility_minor)::bigint, sum(debt_instrument_count)::bigint
    from debt_entity group by 1, 3
), lease_entity as (
    select period_id, legal_entity_id as scope_id, currency,
           sum(opening_liability_minor)::bigint as opening_lease_liability_minor,
           sum(liability_addition_minor)::bigint as lease_addition_minor,
           sum(cash_payment_minor)::bigint as lease_cash_payment_minor,
           sum(interest_accretion_minor)::bigint as lease_interest_minor,
           sum(principal_reduction_minor)::bigint as lease_principal_reduction_minor,
           sum(closing_liability_minor)::bigint as closing_lease_liability_minor,
           count(distinct lease_contract_id)::bigint as lease_contract_count
    from {{ ref('fct_lease_schedule') }} group by 1, 2, 3
), lease as (
    select * from lease_entity
    union all
    select period_id, 'NEXUS-GROUP', currency,
           sum(opening_lease_liability_minor)::bigint, sum(lease_addition_minor)::bigint,
           sum(lease_cash_payment_minor)::bigint, sum(lease_interest_minor)::bigint,
           sum(lease_principal_reduction_minor)::bigint, sum(closing_lease_liability_minor)::bigint,
           sum(lease_contract_count)::bigint
    from lease_entity group by 1, 3
), cash as (
    select period_id, scope_id, currency, amount_minor as cash_minor
    from {{ ref('fct_statutory_statement_lines') }}
    where statement_class = 'BALANCE_SHEET' and statement_line = 'cash'
)
select
    md5(concat_ws('|', debt.period_id, debt.scope_id, debt.currency)) as capital_structure_hk,
    debt.period_id,
    debt.scope_id,
    debt.currency,
    debt.opening_debt_minor,
    debt.debt_drawdown_minor,
    debt.debt_repayment_minor,
    debt.debt_cash_interest_minor,
    debt.debt_accrued_interest_minor,
    debt.closing_debt_minor,
    debt.undrawn_facility_minor,
    debt.debt_instrument_count,
    coalesce(lease.opening_lease_liability_minor, 0)::bigint as opening_lease_liability_minor,
    coalesce(lease.lease_addition_minor, 0)::bigint as lease_addition_minor,
    coalesce(lease.lease_cash_payment_minor, 0)::bigint as lease_cash_payment_minor,
    coalesce(lease.lease_interest_minor, 0)::bigint as lease_interest_minor,
    coalesce(lease.lease_principal_reduction_minor, 0)::bigint as lease_principal_reduction_minor,
    coalesce(lease.closing_lease_liability_minor, 0)::bigint as closing_lease_liability_minor,
    coalesce(lease.lease_contract_count, 0)::bigint as lease_contract_count,
    cash.cash_minor,
    (debt.closing_debt_minor + coalesce(lease.closing_lease_liability_minor, 0))::bigint as gross_debt_minor,
    (debt.closing_debt_minor + coalesce(lease.closing_lease_liability_minor, 0) - cash.cash_minor)::bigint as net_debt_minor,
    (cash.cash_minor + debt.undrawn_facility_minor)::bigint as available_liquidity_minor,
    version.reporting_version_ref,
    'TREASURY_AND_LEASE_SUBLEDGER' as value_authority,
    version.reliability_status,
    'EXECUTIVE_CAPITAL_STRUCTURE' as reliability_purpose,
    'gold.fct_debt_schedule|gold.fct_lease_schedule|gold.fct_statutory_statement_lines' as drill_through_relation,
    version.source_package_digest,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from debt
left join lease using (period_id, scope_id, currency)
inner join cash using (period_id, scope_id, currency)
inner join {{ ref('dim_reporting_version') }} version
  on debt.period_id = version.period_id and debt.scope_id = version.scope_id
