{{ config(tags=['slice_b3']) }}

select
    md5(compensation.compensation_line_id) as employee_compensation_hk,
    compensation.* exclude (_ingested_at, _source_file, _source_file_sha256),
    payroll.legal_entity_id,
    payroll.business_event_ref,
    payroll.reporting_version_ref,
    payroll.close_status,
    payroll.reliability_status,
    payroll.reliability_purpose,
    payroll.source_package_digest
from {{ ref('stg_workforce__employee_compensation') }} compensation
inner join {{ ref('fct_payroll_expense_lines') }} payroll
  using (period_id, employee_id, department_id, region_id, currency)
