with additions as (
    select * from (values
        ('QF-D73','dim_budget_version','stg_planning__budget_versions','planning__budget_versions','STRICT_TYPE_AND_CLASSIFY_APPROVAL'),
        ('QF-D74','dim_planning_scenario','stg_planning__forecast_versions|dim_budget_version|dim_reporting_version','planning__forecast_versions|planning__budget_versions|accounting__monthly_close_status','TYPE_AND_BIND_SCENARIO_TO_EXACT_ATLAS_ACTUALS_BOUNDARY'),
        ('QF-D75','fct_budget_plan_lines','stg_planning__budget_lines|dim_budget_version|dim_period|dim_department|dim_gl_account','planning__budget_lines','TYPE_AND_CONFORM_BUDGET_INPUT'),
        ('QF-D76','fct_forecast_plan_lines','stg_planning__forecast_lines|dim_planning_scenario|dim_period|dim_department|dim_gl_account','planning__forecast_lines|planning__forecast_versions','TYPE_AND_CONFORM_SCENARIO_INPUT'),
        ('QF-D77','fct_planning_variance_source','stg_planning__variance_source_extract|fct_budget_plan_lines|fct_forecast_plan_lines|dim_period|dim_department|dim_gl_account','planning__variance_source_extract|planning__budget_lines|planning__forecast_lines','PRESERVE_SOURCE_REPORT_AND_RESOLVE_LINEAGE_WITHOUT_STATUTORY_PROMOTION'),
        ('QF-D78','fct_headcount_plan','stg_planning__headcount_plan|dim_planning_scenario|dim_department|dim_region','workforce__headcount_plan|planning__forecast_versions','TYPE_AND_CONFORM_WORKFORCE_PLANNING_INPUT')
    ) t(dataset_id, gold_model, direct_dependencies, a24_bronze_sources, transformation_class)
)
select * from {{ ref('q_finance_v3_lineage_registry') }}
union all
select * from additions
