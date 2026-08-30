-- depends_on: {{ ref('q_finance_v2_dataset_registry') }}

with additions as (
    select * from (values
        ('QF-R19','QF-D21','period_id','QF-D01','period_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R20','QF-D21','legal_entity_id','QF-D02','legal_entity_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R21','QF-D21','business_event_ref','QF-D06','business_event_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R22','QF-D21','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R23','QF-D22','asset_id','QF-D18','asset_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R24','QF-D23','asset_id','QF-D18','asset_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R25','QF-D23','period_id','QF-D01','period_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R26','QF-D23','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R27','QF-D24','asset_id','QF-D18','asset_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R28','QF-D25','bank_account_id','QF-D16','bank_account_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R29','QF-D25','business_event_ref','QF-D06','business_event_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R30','QF-D25','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R31','QF-D26','bank_transaction_id','QF-D25','bank_transaction_id','ONE_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R32','QF-D26','bank_account_id','QF-D16','bank_account_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R33','QF-D27','bank_account_id','QF-D16','bank_account_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R34','QF-D27','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R35','QF-D28','debt_instrument_id','QF-D17','debt_instrument_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R36','QF-D28','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R37','QF-D29','lease_contract_id','QF-D19','lease_contract_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R38','QF-D30','lease_contract_id','QF-D19','lease_contract_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R39','QF-D30','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R40','QF-D31','legal_entity_id|jurisdiction_code','QF-D20','legal_entity_id|jurisdiction_code','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R41','QF-D31','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R42','QF-D32','legal_entity_id|jurisdiction_code','QF-D20','legal_entity_id|jurisdiction_code','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R43','QF-D32','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R44','QF-D33','legal_entity_id|jurisdiction_code','QF-D20','legal_entity_id|jurisdiction_code','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R45','QF-D33','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R46','QF-D34','business_event_ref','QF-D06','business_event_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R47','QF-D34','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R48','QF-D36','expense_account_id','QF-D04','account_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R49','QF-D36','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R50','QF-D38','expense_account_id','QF-D04','account_id','MANY_TO_ONE','ACTIVE','CONSUMER_RELATIONSHIP'),
        ('QF-R51','QF-D38','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R52','QF-D39','seller_entity_id','QF-D02','legal_entity_id','MANY_TO_ONE','ROLE_PLAYING','CONSUMER_RELATIONSHIP'),
        ('QF-R53','QF-D39','buyer_entity_id','QF-D02','legal_entity_id','MANY_TO_ONE','ROLE_PLAYING','CONSUMER_RELATIONSHIP'),
        ('QF-R54','QF-D39','intercompany_transaction_id','QF-D09','source_intercompany_transaction_id','ONE_TO_MANY','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R55','QF-D40','seller_entity_id','QF-D02','legal_entity_id','MANY_TO_ONE','ROLE_PLAYING','CONSUMER_RELATIONSHIP'),
        ('QF-R56','QF-D40','buyer_entity_id','QF-D02','legal_entity_id','MANY_TO_ONE','ROLE_PLAYING','CONSUMER_RELATIONSHIP'),
        ('QF-R57','QF-D41','reporting_version_ref','QF-D05','reporting_version_ref','MANY_TO_ONE','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE'),
        ('QF-R58','QF-D42','candidate_business_event_ref','QF-D06','business_event_ref','MANY_TO_ONE_OPTIONAL','NAVIGATION_ONLY','INTEGRITY_AND_LINEAGE')
    ) t(relationship_id, from_dataset_id, from_columns, to_dataset_id, to_columns, cardinality, load_disposition, enforcement)
)
select * from {{ ref('q_finance_relationship_registry') }}
union all
select * from additions
