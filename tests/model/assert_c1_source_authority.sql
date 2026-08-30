{{ config(tags=['slice_c']) }}

with registered as (
    select relation_name from {{ ref('q_finance_v5_dataset_registry') }}
    where dataset_id between 'QF-D79' and 'QF-D99'
), failures as (
    select dataset.dataset_id object_ref
    from {{ ref('q_finance_v5_dataset_registry') }} dataset
    where dataset.dataset_id between 'QF-D79' and 'QF-D99'
      and (dataset.source_data_ref <> '{{ var("a24_data_ref") }}'
        or dataset.source_package_digest <> '{{ var("a24_package_digest") }}'
        or dataset.finance_model_ref <> '{{ var("finance_model_ref") }}')
    union all
    select 'C1_DATASET_COUNT' where (select count(*) from registered) <> 21
)
select * from failures
