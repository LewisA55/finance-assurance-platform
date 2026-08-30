{{ config(tags=['slice_c']) }}

with count_failures as (
    select 'DATASETS' object_ref where (select count(*) from {{ ref('q_finance_v5_dataset_registry') }}) <> 99
    union all select 'RELATIONSHIPS' where (select count(*) from {{ ref('q_finance_v5_relationship_registry') }}) <> 187
    union all select 'MEASURES' where (select count(*) from {{ ref('q_finance_v5_measure_registry') }}) <> 189
    union all select 'LINEAGE' where (select count(*) from {{ ref('q_finance_v5_lineage_registry') }}) <> 99
), relation_failures as (
    select dataset.dataset_id object_ref
    from {{ ref('q_finance_v5_dataset_registry') }} dataset
    left join information_schema.tables physical
      on dataset.relation_schema = physical.table_schema and dataset.relation_name = physical.table_name
    where physical.table_name is null or dataset.registry_version <> 5
       or dataset.finance_model_ref <> 'Q-FINANCE-C1@v1'
), endpoint_failures as (
    select relationship.relationship_id object_ref
    from {{ ref('q_finance_v5_relationship_registry') }} relationship
    left join {{ ref('q_finance_v5_dataset_registry') }} source
      on relationship.from_dataset_id = source.dataset_id
    left join {{ ref('q_finance_v5_dataset_registry') }} target
      on relationship.to_dataset_id = target.dataset_id
    where source.dataset_id is null or target.dataset_id is null
), measure_failures as (
    select measure.measure_id object_ref
    from {{ ref('q_finance_v5_measure_registry') }} measure
    inner join {{ ref('q_finance_v5_dataset_registry') }} dataset using (dataset_id)
    left join information_schema.columns field
      on field.table_schema = dataset.relation_schema
     and field.table_name = dataset.relation_name
     and field.column_name = measure.source_field
    where field.column_name is null
), lineage_failures as (
    select coalesce(dataset.dataset_id, lineage.dataset_id) object_ref
    from {{ ref('q_finance_v5_dataset_registry') }} dataset
    full outer join {{ ref('q_finance_v5_lineage_registry') }} lineage using (dataset_id)
    where dataset.dataset_id is null or lineage.dataset_id is null
)
select * from count_failures
union all select * from relation_failures
union all select * from endpoint_failures
union all select * from measure_failures
union all select * from lineage_failures
