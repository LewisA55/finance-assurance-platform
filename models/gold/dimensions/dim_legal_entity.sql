select
    md5(legal_entity_id) as legal_entity_hk,
    legal_entity_id,
    legal_entity_name,
    parent_entity_id,
    functional_currency,
    incorporation_date,
    consolidation_method,
    entity_status,
    _source_row_hash,
    _source_data_ref
from {{ ref('stg_reference__legal_entities') }}
