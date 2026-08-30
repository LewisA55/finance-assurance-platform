{{ config(tags=['slice_b4']) }}

select table_name
from information_schema.columns
where table_schema = 'gold'
  and table_name in (
      'dim_budget_version', 'dim_planning_scenario', 'fct_budget_plan_lines',
      'fct_forecast_plan_lines', 'fct_planning_variance_source', 'fct_headcount_plan'
  )
  and column_name in ('business_event_ref', 'accounting_event_ref', 'journal_id')
