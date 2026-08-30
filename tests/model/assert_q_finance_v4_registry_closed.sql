{{ config(tags=['slice_b4']) }}

with counts as (
    select 'DATASETS' registry_name, count(*) actual_count, 78 expected_count
    from {{ ref('q_finance_v4_dataset_registry') }}
    union all
    select 'RELATIONSHIPS', count(*), 127
    from {{ ref('q_finance_v4_relationship_registry') }}
    union all
    select 'MEASURES', count(*), 107
    from {{ ref('q_finance_v4_measure_registry') }}
    union all
    select 'LINEAGE', count(*), 78
    from {{ ref('q_finance_v4_lineage_registry') }}
)
select * from counts where actual_count <> expected_count
