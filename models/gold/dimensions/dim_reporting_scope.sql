with entity_scopes as (
    select
        md5(legal_entity_id) as reporting_scope_hk,
        legal_entity_id as scope_id,
        legal_entity_name as scope_name,
        'LEGAL_ENTITY' as scope_type,
        legal_entity_id,
        functional_currency as reporting_currency,
        _source_data_ref
    from {{ ref('stg_reference__legal_entities') }}
),
group_scope as (
    select
        md5('NEXUS-GROUP') as reporting_scope_hk,
        'NEXUS-GROUP' as scope_id,
        'Nexus Group' as scope_name,
        'CONSOLIDATED_GROUP' as scope_type,
        cast(null as varchar) as legal_entity_id,
        'GBP' as reporting_currency,
        '{{ var("a24_data_ref") }}' as _source_data_ref
)
select * from entity_scopes
union all
select * from group_scope
