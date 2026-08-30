{{ config(tags=['slice_b2']) }}

select
    trim(tax_calculation_input_id) as tax_calculation_input_id,
    trim(period_id) as period_id,
    trim(legal_entity_id) as legal_entity_id,
    upper(trim(jurisdiction_code)) as jurisdiction_code,
    cast(profit_before_tax_minor as bigint) as profit_before_tax_minor,
    cast(permanent_difference_minor as bigint) as permanent_difference_minor,
    cast(temporary_difference_minor as bigint) as temporary_difference_minor,
    cast(statutory_tax_rate_bps as integer) as statutory_tax_rate_bps,
    cast(deferred_tax_recognition_bps as integer) as deferred_tax_recognition_bps,
    upper(trim(currency)) as currency,
    trim(approval_ref) as approval_ref,
    cast(source_recorded_at as timestamptz) as source_recorded_at,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'tax__tax_calculation_inputs') }}
