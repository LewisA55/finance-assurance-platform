{{ config(tags=['slice_b4']) }}

select
    md5(budget_version_ref) as budget_version_hk,
    budget.* exclude (_ingested_at, _source_file, _source_file_sha256),
    case
        when approval_status = 'APPROVED' and locked_flag
            then 'APPROVED_AND_LOCKED_PLANNING_INPUT'
        when approval_status = 'APPROVED'
            then 'APPROVED_UNLOCKED_PLANNING_INPUT'
        else 'DRAFT_PLANNING_INPUT'
    end as planning_input_status,
    'PLANNING_INPUTS' as reliability_purpose
from {{ ref('stg_planning__budget_versions') }} budget
