{{ config(tags=['slice_b2']) }}

with source_refs as (
    select distinct _source_data_ref from {{ ref('stg_treasury__bank_accounts') }}
    union all select distinct _source_data_ref from {{ ref('stg_treasury__bank_transactions') }}
    union all select distinct _source_data_ref from {{ ref('stg_treasury__debt_schedule') }}
    union all select distinct _source_data_ref from {{ ref('stg_fixed_assets__fixed_asset_register') }}
    union all select distinct _source_data_ref from {{ ref('stg_fixed_assets__fixed_asset_movements') }}
    union all select distinct _source_data_ref from {{ ref('stg_leases__lease_schedule') }}
    union all select distinct _source_data_ref from {{ ref('stg_tax__tax_schedule') }}
    union all select distinct _source_data_ref from {{ ref('stg_equity__equity_movements') }}
    union all select distinct _source_data_ref from {{ ref('stg_working_capital__accrual_schedule') }}
    union all select distinct _source_data_ref from {{ ref('stg_working_capital__prepayment_schedule') }}
    union all select distinct _source_data_ref from {{ ref('stg_intercompany__intercompany_transactions') }}
    union all select distinct _source_data_ref from {{ ref('stg_assurance__statutory_subledger_control_results') }}
    union all select distinct _source_data_ref from {{ ref('stg_hermes__source_admission_results') }}
)
select * from source_refs
where _source_data_ref <> '{{ var("a24_data_ref") }}' or _source_data_ref is null
