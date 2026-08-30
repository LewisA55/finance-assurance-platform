{{ config(tags=['slice_c']) }}

select planning_performance_hk as object_ref
from {{ ref('mart_planning_performance_monthly') }}
where is_statutory_actual or value_authority <> 'MANAGEMENT_SOURCE_REPORT'
union all
select model_planning_input_hk
from {{ ref('mart_model_planning_inputs') }}
where is_governed_pythia_snapshot
   or actuals_scope_id <> 'NEXUS-GROUP'
   or actuals_close_status <> 'HARD_CLOSED'
   or actuals_reliability_status <> 'RELIABLE_FOR_STATUTORY_ACTUALS'
