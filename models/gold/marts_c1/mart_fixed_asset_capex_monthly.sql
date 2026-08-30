{{ config(tags=['slice_c']) }}

select
    md5(concat_ws('|', movement.period_id, movement.legal_entity_id, movement.asset_class, movement.currency)) as fixed_asset_capex_hk,
    movement.period_id,
    movement.legal_entity_id,
    entity.legal_entity_name,
    movement.asset_class,
    movement.currency,
    sum(movement.opening_gross_book_value_minor)::bigint as opening_gross_book_value_minor,
    sum(movement.gross_addition_minor)::bigint as capex_additions_minor,
    sum(movement.gross_disposal_minor)::bigint as gross_disposals_minor,
    sum(movement.closing_gross_book_value_minor)::bigint as closing_gross_book_value_minor,
    sum(movement.opening_accumulated_depreciation_minor)::bigint as opening_accumulated_depreciation_minor,
    sum(movement.depreciation_minor)::bigint as depreciation_minor,
    sum(movement.amortisation_minor)::bigint as amortisation_minor,
    sum(movement.impairment_minor)::bigint as impairment_minor,
    sum(movement.accumulated_depreciation_disposal_minor)::bigint as accumulated_depreciation_disposal_minor,
    sum(movement.closing_accumulated_depreciation_minor)::bigint as closing_accumulated_depreciation_minor,
    sum(movement.disposal_proceeds_minor)::bigint as disposal_proceeds_minor,
    sum(movement.disposal_gain_loss_minor)::bigint as disposal_gain_loss_minor,
    sum(movement.closing_net_book_value_minor)::bigint as closing_net_book_value_minor,
    count(distinct movement.asset_id)::bigint as asset_count,
    sum(movement.resolved_business_event_count)::bigint as resolved_business_event_count,
    version.reporting_version_ref,
    'FIXED_ASSET_SUBLEDGER' as value_authority,
    version.reliability_status,
    'EXECUTIVE_FIXED_ASSET_AND_CAPEX' as reliability_purpose,
    'gold.fct_fixed_asset_movements' as drill_through_relation,
    version.source_package_digest,
    '{{ var("a24_data_ref") }}' as _source_data_ref
from {{ ref('fct_fixed_asset_movements') }} movement
inner join {{ ref('dim_legal_entity') }} entity using (legal_entity_id)
inner join {{ ref('dim_reporting_version') }} version
  on movement.period_id = version.period_id and movement.legal_entity_id = version.scope_id
group by 1, 2, 3, 4, 5, movement.currency, version.reporting_version_ref,
         version.reliability_status, version.source_package_digest
