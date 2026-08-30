{{ config(tags=['slice_b4']) }}

with populations as (
    select (select count(*) from {{ ref('dim_budget_version') }}) actual_rows,
           (select count(*) from {{ ref('stg_planning__budget_versions') }}) expected_rows
    union all select (select count(*) from {{ ref('dim_planning_scenario') }}),
                     (select count(*) from {{ ref('stg_planning__forecast_versions') }})
    union all select (select count(*) from {{ ref('fct_budget_plan_lines') }}),
                     (select count(*) from {{ ref('stg_planning__budget_lines') }})
    union all select (select count(*) from {{ ref('fct_forecast_plan_lines') }}),
                     (select count(*) from {{ ref('stg_planning__forecast_lines') }})
    union all select (select count(*) from {{ ref('fct_planning_variance_source') }}),
                     (select count(*) from {{ ref('stg_planning__variance_source_extract') }})
    union all select (select count(*) from {{ ref('fct_headcount_plan') }}),
                     (select count(*) from {{ ref('stg_planning__headcount_plan') }})
)
select * from populations where actual_rows <> expected_rows
