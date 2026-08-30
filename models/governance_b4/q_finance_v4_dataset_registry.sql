-- depends_on: {{ ref('dim_budget_version') }}
-- depends_on: {{ ref('dim_planning_scenario') }}
-- depends_on: {{ ref('fct_budget_plan_lines') }}
-- depends_on: {{ ref('fct_forecast_plan_lines') }}
-- depends_on: {{ ref('fct_planning_variance_source') }}
-- depends_on: {{ ref('fct_headcount_plan') }}

with inherited as (
    select
        registry_id, 4 as registry_version, dataset_id, dataset_version,
        relation_schema, relation_name, grain, semantic_owner, model_class,
        consumption_class, reliability_purpose, source_data_ref,
        source_package_digest, '{{ var("finance_model_ref") }}' as finance_model_ref,
        money_contract
    from {{ ref('q_finance_v3_dataset_registry') }}
), additions as (
    select * from (values
        ('QF-D73','dim_budget_version','ONE_ROW_PER_BUDGET_VERSION','PYTHIA','DIMENSION','CORE','PLANNING_INPUT_GOVERNANCE'),
        ('QF-D74','dim_planning_scenario','ONE_ROW_PER_FORECAST_VERSION_SCENARIO','PYTHIA','DIMENSION','CORE','SCENARIO_AND_ACTUALS_BOUNDARY'),
        ('QF-D75','fct_budget_plan_lines','ONE_ROW_PER_VERSION_PERIOD_DEPARTMENT_ACCOUNT','PYTHIA','ATOMIC_FACT','CORE','BUDGET_ANALYTICS'),
        ('QF-D76','fct_forecast_plan_lines','ONE_ROW_PER_SCENARIO_PERIOD_DEPARTMENT_ACCOUNT','PYTHIA','ATOMIC_FACT','CORE','FORECAST_INPUT_ANALYTICS'),
        ('QF-D77','fct_planning_variance_source','ONE_ROW_PER_PERIOD_DEPARTMENT_ACCOUNT','PYTHIA','SOURCE_REPORT_FACT','CORE','MANAGEMENT_VARIANCE_ANALYTICS'),
        ('QF-D78','fct_headcount_plan','ONE_ROW_PER_PLANNED_POSITION','PYTHIA','ATOMIC_FACT','CORE','WORKFORCE_PLANNING_INPUTS')
    ) t(dataset_id, relation_name, grain, semantic_owner, model_class, consumption_class, reliability_purpose)
)
select * from inherited
union all
select
    'Q-FINANCE', 4, dataset_id, 1, 'gold', relation_name, grain,
    semantic_owner, model_class, consumption_class, reliability_purpose,
    '{{ var("a24_data_ref") }}', '{{ var("a24_package_digest") }}',
    '{{ var("finance_model_ref") }}', 'INTEGER_MINOR_UNITS_PLUS_CURRENCY'
from additions
