{{ config(tags=['slice_b3']) }}

select
    trim(payroll_line_id) as payroll_line_id,
    trim(period_id) as period_id,
    trim(employee_id) as employee_id,
    trim(department_id) as department_id,
    trim(region_id) as region_id,
    cast(gross_pay_minor as bigint) as gross_pay_minor,
    cast(employer_tax_minor as bigint) as employer_tax_minor,
    cast(benefits_minor as bigint) as benefits_minor,
    cast(total_payroll_cost_minor as bigint) as total_payroll_cost_minor,
    upper(trim(currency)) as currency,
    cast(reporting_payroll_cost_minor as bigint) as reporting_payroll_cost_minor,
    upper(trim(reporting_currency)) as reporting_currency,
    upper(trim(payroll_status)) as payroll_status,
    _source_row_hash, cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file, _source_file_sha256, _source_data_ref
from {{ source('a24_bronze', 'workforce__payroll_expense_lines') }}
