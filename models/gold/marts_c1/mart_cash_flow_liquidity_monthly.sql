{{ config(tags=['slice_c']) }}

with debt_entity as (
    select period_id, legal_entity_id as scope_id,
           sum(closing_principal_minor)::bigint as closing_debt_minor,
           sum(undrawn_facility_minor)::bigint as undrawn_facility_minor,
           sum(cash_interest_minor)::bigint as cash_interest_minor
    from {{ ref('fct_debt_schedule') }} group by 1, 2
), debt as (
    select * from debt_entity
    union all
    select period_id, 'NEXUS-GROUP', sum(closing_debt_minor)::bigint,
           sum(undrawn_facility_minor)::bigint, sum(cash_interest_minor)::bigint
    from debt_entity group by 1
), lease_entity as (
    select period_id, legal_entity_id as scope_id,
           sum(closing_liability_minor)::bigint as closing_lease_liability_minor,
           sum(cash_payment_minor)::bigint as lease_cash_payment_minor
    from {{ ref('fct_lease_schedule') }} group by 1, 2
), lease as (
    select * from lease_entity
    union all
    select period_id, 'NEXUS-GROUP', sum(closing_lease_liability_minor)::bigint,
           sum(lease_cash_payment_minor)::bigint
    from lease_entity group by 1
)
select
    md5(concat_ws('|', cash.period_id, cash.scope_id, cash.reporting_version_ref)) as cash_flow_liquidity_hk,
    cash.period_id,
    cash.scope_id,
    cash.reporting_version_ref,
    cash.currency,
    cash.opening_cash_minor,
    cash.operating_cash_flow_minor,
    cash.investing_cash_flow_minor,
    cash.financing_cash_flow_minor,
    cash.fx_and_other_movement_minor,
    cash.statement_cash_movement_minor as net_change_in_cash_minor,
    cash.closing_cash_minor,
    coalesce(debt.closing_debt_minor, 0)::bigint as closing_debt_minor,
    coalesce(lease.closing_lease_liability_minor, 0)::bigint as closing_lease_liability_minor,
    coalesce(debt.undrawn_facility_minor, 0)::bigint as undrawn_facility_minor,
    coalesce(debt.cash_interest_minor, 0)::bigint as cash_interest_minor,
    coalesce(lease.lease_cash_payment_minor, 0)::bigint as lease_cash_payment_minor,
    (coalesce(debt.closing_debt_minor, 0) + coalesce(lease.closing_lease_liability_minor, 0)
        - cash.closing_cash_minor)::bigint as net_debt_minor,
    (cash.closing_cash_minor + coalesce(debt.undrawn_facility_minor, 0))::bigint as available_liquidity_minor,
    cash.unreconciled_difference_minor,
    cash.reconciliation_status,
    'STATUTORY_CASH_FLOW_AND_SUBLEDGER' as value_authority,
    cash.reliability_status,
    'EXECUTIVE_CASH_FLOW_AND_LIQUIDITY' as reliability_purpose,
    'gold.fct_cash_flow_reconciliation|gold.fct_debt_schedule|gold.fct_lease_schedule' as drill_through_relation,
    cash.source_package_digest,
    cash._source_data_ref
from {{ ref('fct_cash_flow_reconciliation') }} cash
left join debt using (period_id, scope_id)
left join lease using (period_id, scope_id)
