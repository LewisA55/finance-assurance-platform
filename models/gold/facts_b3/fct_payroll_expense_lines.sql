{{ config(tags=['slice_b3']) }}

select
    md5(payroll.payroll_line_id) as payroll_expense_line_hk,
    payroll.* exclude (_ingested_at, _source_file, _source_file_sha256),
    employee.employment_status,
    department.business_unit,
    department.opex_class,
    link.business_event_ref,
    link.legal_entity_id,
    link.gl_journal_line_count,
    link.gl_debit_minor,
    link.gl_credit_minor,
    link.reporting_version_ref,
    link.close_status,
    link.reliability_status,
    link.reliability_purpose,
    link.source_package_digest
from {{ ref('stg_workforce__payroll_expense_lines') }} payroll
inner join {{ ref('dim_employee') }} employee using (employee_id)
inner join {{ ref('dim_department') }} department
  on payroll.department_id = department.department_id
inner join {{ ref('fct_operational_event_links') }} link
  on link.object_type = 'PAYROLL_LINE'
 and payroll.payroll_line_id = link.object_ref
