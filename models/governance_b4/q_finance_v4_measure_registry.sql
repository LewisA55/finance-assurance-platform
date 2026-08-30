-- depends_on: {{ ref('q_finance_v4_dataset_registry') }}

with additions as (
    select * from (values
        ('QF-M95','QF-D75','Budget amount','amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','budget_version_ref|period_id|department_id|account_id|currency','PLANNING_VERSION_REQUIRED'),
        ('QF-M96','QF-D75','Reporting-currency budget amount','reporting_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','budget_version_ref|period_id|department_id|account_id|reporting_currency','PLANNING_VERSION_REQUIRED'),
        ('QF-M97','QF-D76','Forecast amount','amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','planning_scenario_ref|period_id|department_id|account_id|currency','EXACT_SCENARIO_REQUIRED'),
        ('QF-M98','QF-D76','Reporting-currency forecast amount','reporting_amount_minor','ADDITIVE_GOVERNED_TOTAL','SUM','planning_scenario_ref|period_id|department_id|account_id|reporting_currency','EXACT_SCENARIO_REQUIRED'),
        ('QF-M99','QF-D77','Management-report actual','actual_amount_minor','ADDITIVE_SOURCE_REPORT_TOTAL','SUM','period_id|department_id|account_id|currency','NOT_STATUTORY_ACTUAL'),
        ('QF-M100','QF-D77','Management-report budget','budget_amount_minor','ADDITIVE_SOURCE_REPORT_TOTAL','SUM','period_id|department_id|account_id|currency','SOURCE_REPORT_ONLY'),
        ('QF-M101','QF-D77','Management-report forecast','forecast_amount_minor','ADDITIVE_SOURCE_REPORT_TOTAL','SUM','period_id|department_id|account_id|currency','SOURCE_REPORT_ONLY'),
        ('QF-M102','QF-D77','Actual versus budget variance','actual_vs_budget_variance_minor','ADDITIVE_SOURCE_REPORT_TOTAL','SUM','period_id|department_id|account_id|currency','SOURCE_REPORT_ONLY'),
        ('QF-M103','QF-D77','Actual versus forecast variance','actual_vs_forecast_variance_minor','ADDITIVE_SOURCE_REPORT_TOTAL','SUM','period_id|department_id|account_id|currency','SOURCE_REPORT_ONLY'),
        ('QF-M104','QF-D77','Forecast versus budget variance','forecast_vs_budget_variance_minor','ADDITIVE_SOURCE_REPORT_TOTAL','SUM','period_id|department_id|account_id|currency','SOURCE_REPORT_ONLY'),
        ('QF-M105','QF-D78','Planned positions','position_id','DISTINCT_COUNT','COUNT_DISTINCT','planning_scenario_ref|department_id|region_id|position_status','EXACT_SCENARIO_REQUIRED'),
        ('QF-M106','QF-D78','Planned salary midpoint','salary_mid_minor','ADDITIVE_GOVERNED_TOTAL','SUM','planning_scenario_ref|department_id|region_id|currency','EXACT_SCENARIO_REQUIRED'),
        ('QF-M107','QF-D78','Reporting-currency planned salary midpoint','reporting_salary_mid_minor','ADDITIVE_GOVERNED_TOTAL','SUM','planning_scenario_ref|department_id|region_id|reporting_currency','EXACT_SCENARIO_REQUIRED')
    ) t(measure_id, dataset_id, measure_name, source_field, measure_class, aggregation, required_grain, reporting_version_policy)
)
select * from {{ ref('q_finance_v3_measure_registry') }}
union all
select * from additions
