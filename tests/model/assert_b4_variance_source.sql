{{ config(tags=['slice_b4']) }}

select variance_line_id
from {{ ref('fct_planning_variance_source') }}
where actual_amount_minor - budget_amount_minor <> actual_vs_budget_variance_minor
   or actual_amount_minor - forecast_amount_minor <> actual_vs_forecast_variance_minor
   or forecast_amount_minor - budget_amount_minor <> forecast_vs_budget_variance_minor
   or is_statutory_actual
   or value_authority <> 'MANAGEMENT_SOURCE_REPORT'
   or (period_status = 'ACTUAL' and source_budget_line_ref is null)
   or (period_status = 'ACTUAL' and source_forecast_line_ref is not null)
   or (period_status = 'FORECAST' and source_forecast_line_ref is null)
