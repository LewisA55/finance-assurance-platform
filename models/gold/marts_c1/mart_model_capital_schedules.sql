{{ config(tags=['slice_c']) }}

with fixed_asset as (
    select period_id, legal_entity_id, 'FIXED_ASSET' as schedule_domain,
           asset_id as schedule_object_id, asset_class as schedule_class, currency,
           (opening_gross_book_value_minor - opening_accumulated_depreciation_minor)::bigint as opening_balance_minor,
           gross_addition_minor::bigint as additions_minor,
           gross_disposal_minor::bigint as reductions_minor,
           (depreciation_minor + amortisation_minor + impairment_minor)::bigint as noncash_charge_minor,
           null::bigint as interest_minor,
           null::bigint as cash_flow_minor,
           closing_net_book_value_minor::bigint as closing_balance_minor,
           null::date as maturity_date, reporting_version_ref, reliability_status,
           source_package_digest, _source_data_ref
    from {{ ref('fct_fixed_asset_movements') }}
), debt as (
    select period_id, legal_entity_id, 'DEBT' as schedule_domain,
           debt_instrument_id, facility_type, currency,
           opening_principal_minor, drawdown_minor, principal_repayment_minor,
           accrued_interest_minor, cash_interest_minor,
           (drawdown_minor - principal_repayment_minor - cash_interest_minor)::bigint,
           closing_principal_minor, maturity_date, reporting_version_ref,
           reliability_status, source_package_digest, _source_data_ref
    from {{ ref('fct_debt_schedule') }}
), lease as (
    select period_id, legal_entity_id, 'LEASE' as schedule_domain,
           lease_contract_id, lease_class, currency,
           opening_liability_minor, liability_addition_minor, principal_reduction_minor,
           interest_accretion_minor, interest_accretion_minor,
           (-cash_payment_minor)::bigint, closing_liability_minor, maturity_date,
           reporting_version_ref, reliability_status, source_package_digest, _source_data_ref
    from {{ ref('fct_lease_schedule') }}
), tax as (
    select period_id, legal_entity_id, 'TAX' as schedule_domain,
           jurisdiction_code, 'CURRENT_AND_DEFERRED_TAX', currency,
           opening_tax_payable_minor, current_tax_expense_minor, cash_tax_paid_minor,
           deferred_tax_movement_minor, null::bigint,
           (-cash_tax_paid_minor)::bigint, closing_tax_payable_minor, null::date,
           reporting_version_ref, reliability_status, source_package_digest, _source_data_ref
    from {{ ref('fct_tax_schedule') }}
), equity_movement as (
    select period_id, legal_entity_id, equity_component, currency,
           sum(amount_minor)::bigint as movement_minor,
           max(reporting_version_ref) as reporting_version_ref,
           max(reliability_status) as reliability_status,
           max(source_package_digest) as source_package_digest,
           max(_source_data_ref) as _source_data_ref
    from {{ ref('fct_equity_movements') }} group by 1, 2, 3, 4
), equity as (
    select period_id, legal_entity_id, 'EQUITY' as schedule_domain,
           equity_component as schedule_object_id, equity_component as schedule_class, currency,
           coalesce(sum(movement_minor) over (
               partition by legal_entity_id, equity_component, currency order by period_id
               rows between unbounded preceding and 1 preceding), 0)::bigint as opening_balance_minor,
           greatest(movement_minor, 0)::bigint as additions_minor,
           abs(least(movement_minor, 0))::bigint as reductions_minor,
           0::bigint as noncash_charge_minor,
           null::bigint as interest_minor,
           movement_minor::bigint as cash_flow_minor,
           sum(movement_minor) over (
               partition by legal_entity_id, equity_component, currency order by period_id
               rows between unbounded preceding and current row)::bigint as closing_balance_minor,
           null::date as maturity_date, reporting_version_ref, reliability_status,
           source_package_digest, _source_data_ref
    from equity_movement
), combined as (
    select * from fixed_asset union all select * from debt union all select * from lease
    union all select * from tax union all select * from equity
)
select
    md5(concat_ws('|', schedule_domain, period_id, legal_entity_id, schedule_object_id)) as model_capital_schedule_hk,
    *,
    'GOVERNED_SUBLEDGER_SCHEDULE' as value_authority,
    'MODEL_SERVING_CAPITAL_SCHEDULES' as reliability_purpose,
    case schedule_domain
        when 'FIXED_ASSET' then 'gold.fct_fixed_asset_movements'
        when 'DEBT' then 'gold.fct_debt_schedule'
        when 'LEASE' then 'gold.fct_lease_schedule'
        when 'TAX' then 'gold.fct_tax_schedule'
        else 'gold.fct_equity_movements'
    end as drill_through_relation
from combined
