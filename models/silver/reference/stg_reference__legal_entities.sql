select
    trim(legal_entity_id) as legal_entity_id,
    trim(legal_entity_name) as legal_entity_name,
    nullif(trim(parent_entity_id), '') as parent_entity_id,
    upper(trim(functional_currency)) as functional_currency,
    cast(incorporation_date as date) as incorporation_date,
    upper(trim(consolidation_method)) as consolidation_method,
    upper(trim(status)) as entity_status,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'reference__legal_entities') }}
