{{ config(tags=['slice_c']) }}

with fixed_mart as (
    select period_id, legal_entity_id, asset_class,
           sum(capex_additions_minor)::bigint additions_minor,
           sum(closing_net_book_value_minor)::bigint closing_minor
    from {{ ref('mart_fixed_asset_capex_monthly') }} group by 1, 2, 3
), fixed_source as (
    select period_id, legal_entity_id, asset_class,
           sum(gross_addition_minor)::bigint additions_minor,
           sum(closing_net_book_value_minor)::bigint closing_minor
    from {{ ref('fct_fixed_asset_movements') }} group by 1, 2, 3
), debt_source as (
    select period_id, sum(closing_principal_minor)::bigint closing_debt_minor
    from {{ ref('fct_debt_schedule') }} group by 1
), failures as (
    select concat_ws('|', mart.period_id, mart.legal_entity_id, mart.asset_class) object_ref
    from fixed_mart mart inner join fixed_source source using (period_id, legal_entity_id, asset_class)
    where mart.additions_minor <> source.additions_minor or mart.closing_minor <> source.closing_minor
    union all
    select mart.period_id
    from {{ ref('mart_capital_structure_monthly') }} mart
    inner join debt_source source using (period_id)
    where mart.scope_id = 'NEXUS-GROUP' and mart.closing_debt_minor <> source.closing_debt_minor
    union all
    select reporting_version_ref from {{ ref('mart_tax_equity_monthly') }}
    where reconciliation_status <> 'RECONCILED'
)
select * from failures
