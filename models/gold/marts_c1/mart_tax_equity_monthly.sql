{{ config(tags=['slice_c']) }}

with tax_entity as (
    select period_id, legal_entity_id as scope_id, currency,
           sum(opening_tax_payable_minor)::bigint as opening_tax_payable_minor,
           sum(profit_before_tax_minor)::bigint as profit_before_tax_minor,
           sum(taxable_profit_minor)::bigint as taxable_profit_minor,
           sum(loss_generated_minor)::bigint as loss_generated_minor,
           sum(loss_utilised_minor)::bigint as loss_utilised_minor,
           sum(current_tax_expense_minor)::bigint as current_tax_expense_minor,
           sum(deferred_tax_movement_minor)::bigint as deferred_tax_movement_minor,
           sum(cash_tax_paid_minor)::bigint as cash_tax_paid_minor,
           sum(closing_tax_payable_minor)::bigint as closing_tax_payable_minor,
           sum(opening_deferred_tax_asset_minor)::bigint as opening_deferred_tax_asset_minor,
           sum(closing_deferred_tax_asset_minor)::bigint as closing_deferred_tax_asset_minor
    from {{ ref('fct_tax_schedule') }} group by 1, 2, 3
), tax as (
    select * from tax_entity
    union all
    select period_id, 'NEXUS-GROUP', currency,
           sum(opening_tax_payable_minor)::bigint, sum(profit_before_tax_minor)::bigint,
           sum(taxable_profit_minor)::bigint, sum(loss_generated_minor)::bigint,
           sum(loss_utilised_minor)::bigint, sum(current_tax_expense_minor)::bigint,
           sum(deferred_tax_movement_minor)::bigint, sum(cash_tax_paid_minor)::bigint,
           sum(closing_tax_payable_minor)::bigint, sum(opening_deferred_tax_asset_minor)::bigint,
           sum(closing_deferred_tax_asset_minor)::bigint
    from tax_entity group by 1, 3
), equity_entity as (
    select period_id, legal_entity_id as scope_id, currency,
           sum(amount_minor)::bigint as external_equity_movement_minor,
           count(distinct equity_movement_id)::bigint as equity_movement_count
    from {{ ref('fct_equity_movements') }} group by 1, 2, 3
), equity as (
    select * from equity_entity
    union all
    select period_id, 'NEXUS-GROUP', currency,
           sum(external_equity_movement_minor)::bigint, sum(equity_movement_count)::bigint
    from equity_entity group by 1, 3
)
select
    md5(concat_ws('|', retained.period_id, retained.scope_id, retained.currency)) as tax_equity_hk,
    retained.period_id,
    retained.scope_id,
    retained.currency,
    coalesce(tax.opening_tax_payable_minor, 0)::bigint as opening_tax_payable_minor,
    coalesce(tax.profit_before_tax_minor, 0)::bigint as profit_before_tax_minor,
    coalesce(tax.taxable_profit_minor, 0)::bigint as taxable_profit_minor,
    coalesce(tax.loss_generated_minor, 0)::bigint as loss_generated_minor,
    coalesce(tax.loss_utilised_minor, 0)::bigint as loss_utilised_minor,
    coalesce(tax.current_tax_expense_minor, 0)::bigint as current_tax_expense_minor,
    coalesce(tax.deferred_tax_movement_minor, 0)::bigint as deferred_tax_movement_minor,
    coalesce(tax.cash_tax_paid_minor, 0)::bigint as cash_tax_paid_minor,
    coalesce(tax.closing_tax_payable_minor, 0)::bigint as closing_tax_payable_minor,
    coalesce(tax.opening_deferred_tax_asset_minor, 0)::bigint as opening_deferred_tax_asset_minor,
    coalesce(tax.closing_deferred_tax_asset_minor, 0)::bigint as closing_deferred_tax_asset_minor,
    coalesce(equity.external_equity_movement_minor, 0)::bigint as external_equity_movement_minor,
    coalesce(equity.equity_movement_count, 0)::bigint as equity_movement_count,
    retained.opening_retained_earnings_minor,
    retained.net_income_minor,
    retained.dividends_minor,
    retained.other_equity_movements_minor,
    retained.closing_retained_earnings_minor,
    retained.reconciliation_status,
    retained.reporting_version_ref,
    'TAX_EQUITY_AND_STATUTORY_ROLLFORWARD' as value_authority,
    retained.reliability_status,
    'EXECUTIVE_TAX_AND_EQUITY' as reliability_purpose,
    'gold.fct_tax_schedule|gold.fct_equity_movements|gold.fct_retained_earnings_bridge' as drill_through_relation,
    retained.source_package_digest,
    retained._source_data_ref
from {{ ref('fct_retained_earnings_bridge') }} retained
left join tax using (period_id, scope_id, currency)
left join equity using (period_id, scope_id, currency)
