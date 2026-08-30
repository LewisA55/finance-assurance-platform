{{ config(tags=['slice_b2']) }}

select
    md5(concat_ws('|', loss.period_id, loss.legal_entity_id,
                  loss.jurisdiction_code, loss.loss_vintage_year)) as tax_loss_register_hk,
    loss.* exclude (_ingested_at, _source_file, _source_file_sha256),
    version.reporting_version_ref,
    version.close_status,
    version.reliability_status,
    version.reliability_purpose,
    version.source_package_digest
from {{ ref('stg_tax__tax_loss_register') }} loss
inner join {{ ref('dim_tax_jurisdiction') }} jurisdiction
    using (legal_entity_id, jurisdiction_code)
inner join {{ ref('dim_reporting_version') }} version
  on loss.period_id = version.period_id and loss.legal_entity_id = version.scope_id
