{{ config(tags=['slice_b2']) }}

select
    trim(period_id) as period_id,
    trim(legal_entity_id) as legal_entity_id,
    upper(trim(jurisdiction_code)) as jurisdiction_code,
    cast(opening_tax_payable_minor as bigint) as opening_tax_payable_minor,
    cast(profit_before_tax_minor as bigint) as profit_before_tax_minor,
    cast(permanent_difference_minor as bigint) as permanent_difference_minor,
    cast(temporary_difference_minor as bigint) as temporary_difference_minor,
    cast(taxable_profit_minor as bigint) as taxable_profit_minor,
    cast(loss_generated_minor as bigint) as loss_generated_minor,
    cast(loss_utilised_minor as bigint) as loss_utilised_minor,
    cast(current_tax_expense_minor as bigint) as current_tax_expense_minor,
    cast(deferred_tax_movement_minor as bigint) as deferred_tax_movement_minor,
    cast(cash_tax_paid_minor as bigint) as cash_tax_paid_minor,
    cast(closing_tax_payable_minor as bigint) as closing_tax_payable_minor,
    cast(opening_deferred_tax_asset_minor as bigint) as opening_deferred_tax_asset_minor,
    cast(closing_deferred_tax_asset_minor as bigint) as closing_deferred_tax_asset_minor,
    cast(statutory_tax_rate_bps as integer) as statutory_tax_rate_bps,
    upper(trim(currency)) as currency,
    coalesce(trim(business_event_refs), '') as business_event_refs,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'tax__tax_schedule') }}
