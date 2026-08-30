{{ config(tags=['slice_b4']) }}

select planning_scenario_ref
from {{ ref('dim_planning_scenario') }}
where actuals_reporting_version_ref is null
   or actuals_close_status <> 'HARD_CLOSED'
   or actuals_reliability_status <> 'RELIABLE_FOR_STATUTORY_ACTUALS'
   or actuals_reliability_purpose <> 'STATUTORY_ACTUALS'
   or actuals_source_package_digest <> '{{ var("a24_package_digest") }}'
   or is_governed_pythia_snapshot
   or (approval_status = 'APPROVED' and not locked_flag)
   or (approval_status <> 'APPROVED' and locked_flag)
