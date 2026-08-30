select
    trim(period_id) as period_id,
    cast(month_start as date) as month_start,
    cast(month_end as date) as month_end,
    cast(fiscal_year as integer) as fiscal_year,
    upper(trim(fiscal_quarter)) as fiscal_quarter,
    cast(replace(upper(trim(fiscal_quarter)), 'Q', '') as integer) as fiscal_quarter_number,
    cast(month_number as integer) as month_number,
    cast(is_actual_period as boolean) as is_actual_period,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'reference__periods') }}
