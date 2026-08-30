{{ config(tags=['slice_b2']) }}

select
    md5(input.tax_calculation_input_id) as tax_calculation_input_hk,
    input.* exclude (_ingested_at, _source_file, _source_file_sha256),
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest
from {{ ref('stg_tax__tax_calculation_inputs') }} input
inner join {{ ref('dim_tax_jurisdiction') }} jurisdiction
    using (legal_entity_id, jurisdiction_code)
inner join {{ ref('dim_reporting_version') }} version
  on input.period_id = version.period_id and input.legal_entity_id = version.scope_id
