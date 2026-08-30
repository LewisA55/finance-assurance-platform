-- depends_on: {{ ref('q_finance_v4_dataset_registry') }}

with additions as (
    select * from (values
        ('QF-R110','QF-D74','source_budget_version_ref','QF-D73','budget_version_ref','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R111','QF-D74','actuals_reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','ACTUALS_BOUNDARY'),
        ('QF-R112','QF-D75','budget_version_ref','QF-D73','budget_version_ref','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R113','QF-D75','period_id','QF-D01','period_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R114','QF-D75','department_id','QF-D44','department_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R115','QF-D75','account_id','QF-D04','account_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R116','QF-D76','planning_scenario_ref','QF-D74','planning_scenario_ref','MANY_TO_ONE','ACTIVE','SCENARIO_ISOLATION'),
        ('QF-R117','QF-D76','period_id','QF-D01','period_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R118','QF-D76','department_id','QF-D44','department_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R119','QF-D76','account_id','QF-D04','account_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R120','QF-D77','period_id','QF-D01','period_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R121','QF-D77','department_id','QF-D44','department_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R122','QF-D77','account_id','QF-D04','account_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R123','QF-D77','source_budget_line_ref','QF-D75','budget_line_id','MANY_TO_ONE_OPTIONAL','NAVIGATION_ONLY','SOURCE_REPORT_LINEAGE'),
        ('QF-R124','QF-D77','source_forecast_line_ref','QF-D76','forecast_line_id','MANY_TO_ONE_OPTIONAL','NAVIGATION_ONLY','SOURCE_REPORT_LINEAGE'),
        ('QF-R125','QF-D78','planning_scenario_ref','QF-D74','planning_scenario_ref','MANY_TO_ONE','ACTIVE','SCENARIO_ISOLATION'),
        ('QF-R126','QF-D78','department_id','QF-D44','department_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R127','QF-D78','region_id','QF-D43','region_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP')
    ) t(relationship_id, from_dataset_id, from_columns, to_dataset_id, to_columns, cardinality, load_disposition, enforcement)
)
select * from {{ ref('q_finance_v3_relationship_registry') }}
union all
select * from additions
