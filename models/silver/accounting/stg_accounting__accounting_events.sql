select
    trim(accounting_event_ref) as accounting_event_ref,
    upper(trim(accounting_event_type)) as accounting_event_type,
    cast(occurred_at as timestamptz) as occurred_at,
    cast(effective_date as date) as effective_date,
    trim(period_id) as period_id,
    trim(legal_entity_id) as legal_entity_id,
    trim(governance_basis_ref) as governance_basis_ref,
    nullif(trim(source_record_refs), '') as source_record_refs,
    record_semantic_hash,
    _source_row_hash,
    cast(_ingested_at as timestamptz) as _ingested_at,
    _source_file,
    _source_file_sha256,
    _source_data_ref
from {{ source('a24_bronze', 'accounting__accounting_events') }}
