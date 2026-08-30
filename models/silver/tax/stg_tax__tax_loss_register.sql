{{ config(tags=['slice_b2']) }}

select
    trim(period_id) as period_id,
    trim(legal_entity_id) as legal_entity_id,
    upper(trim(jurisdiction_code)) as jurisdiction_code,
    cast(loss_vintage_year as integer) as loss_vintage_year,
    cast(opening_tax_loss_minor as bigint) as opening_tax_loss_minor,
    cast(loss_generated_minor as bigint) as loss_generated_minor,
    cast(loss_utilised_minor as bigint) as loss_utilised_minor,
    cast(loss_expired_minor as bigint) as loss_expired_minor,
    cast(closing_tax_loss_minor as bigint) as closing_tax_loss_minor,
    cast(tax_rate_bps as integer) as tax_rate_bps,
    upper(trim(currency)) as currency,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'tax__tax_loss_register') }}
