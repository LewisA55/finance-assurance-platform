select
    md5(period_id) as period_hk,
    period_id,
    month_start,
    month_end,
    fiscal_year,
    fiscal_quarter,
    fiscal_quarter_number,
    month_number,
    is_actual_period,
    case when is_actual_period then 'ACTUAL' else 'FUTURE' end as period_status,
    _source_row_hash,
    _source_data_ref
from {{ ref('stg_reference__periods') }}
