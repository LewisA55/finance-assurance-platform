{{ config(tags=['slice_b4']) }}

select
    md5(line.budget_line_id) as budget_plan_line_hk,
    line.* exclude (_ingested_at, _source_file, _source_file_sha256),
    budget.budget_version_hk,
    budget.budget_name,
    budget.planning_input_status,
    budget.reliability_purpose
from {{ ref('stg_planning__budget_lines') }} line
inner join {{ ref('dim_budget_version') }} budget using (budget_version_ref)
inner join {{ ref('dim_period') }} period using (period_id)
inner join {{ ref('dim_department') }} department using (department_id)
inner join {{ ref('dim_gl_account') }} account using (account_id)
