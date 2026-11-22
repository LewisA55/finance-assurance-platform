"""Generate reviewable PBIP bindings and the pinned P5 semantic adapter.

Run from any directory. Does not alter C2 or create a Desktop cache.
Package metadata, role bounds and PBIR construction come from
`../shared/nexus_build.py`; everything below is P5's own contract.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'shared'))
import nexus_build as nb

MODEL = nb.MODEL
POLICY = json.loads((HERE / 'policy.json').read_text())
GUID = 'NexusReliabilityTileA64B7D4392CE4D438640AA814394A621'

roles = nb.roles(
    grouping=[*nb.COMMON_IDENTITY, 'metricId', 'metricLabel'],
    group_or_measure=[*nb.COMMON_CONTEXT, 'unit', 'period', 'scope', 'version', 'selectedPurpose', 'reliabilityStatus', 'reliabilityPurpose', 'eligibilityState', 'policyVersion', 'readinessStatus', 'failureReason'],
    measure=['displayValue', *nb.COMMON_MEASURE],
)
nb.emit_package(HERE, roles, optional={'evidenceDigest', 'failureReason'}, window=2,
    name='nexusReliabilityTile', display_name='Nexus Reliability Tile', guid=GUID,
    description='Purpose-gated finance KPI with explicit authority and evidence.', rgb=(22, 119, 110))

# Power Query uses the actual inputs, including assessment authority and coverage.
metric_sources=[]
for mid,m in POLICY['metrics'].items():
    metric_sources.append(f'Build("{mid}", "{m["label"]}", "{m["table"]}", "{m["value"]}", "{m["authority"]}", "{m["readinessAuthority"]}", "{m["status"]}", "{m["purpose"]}")')
m_source='''let
    Readiness = ReadC2("mart_cfo_metric_readiness"),
    Build = (id as text, label as text, tableName as text, valueField as text, authority as text, assessmentAuthority as text, status as text, sourcePurpose as text) as table =>
        let
            Source = Table.SelectRows(ReadC2(tableName), each [scope_id] = "NEXUS-GROUP" and (id <> "ENDING_ARR" or Record.FieldOrDefault(_, "metric_id", "") = id)),
            Assessment = Table.SelectRows(Readiness, each [metric_id] = id),
            Unique = Table.RowCount(Assessment) = 1,
            R = if Unique then Assessment{0} else null,
            Rows = List.Transform(Table.ToRecords(Source), (s) =>
                let
                    Count = Table.RowCount(Table.SelectRows(Source, each [period_id] = s[period_id])),
                    Reason = if Count <> 1 then "Duplicate metric period."
                        else if s[reporting_version_ref] <> "RV-NEXUS-GROUP-" & s[period_id] & "@v1" or s[currency] <> "GBP" then "Unsupported reporting context."
                        else if s[source_package_digest] <> "SOURCE_DIGEST" then "Source digest mismatch."
                        else if s[value_authority] <> authority or s[reliability_status] <> status or s[reliability_purpose] <> sourcePurpose then "Source reliability or authority mismatch."
                        else if not Unique then "Missing or duplicate readiness assessment."
                        else if R[source_package_digest] <> s[source_package_digest] or R[value_authority] <> assessmentAuthority or R[readiness_authority] <> "VALIDATOR_PRODUCED" or R[reliability_status] <> "RELIABLE_FOR_EXECUTIVE_PRESENTATION" or R[reliability_purpose] <> "CFO_METRIC_READINESS" then "Readiness authority mismatch."
                        else if R[readiness_status] <> "READY" then (R[first_failure_reason] ?? "Readiness assessment has not passed.")
                        else if R[first_failure_reason] <> null then "Readiness result conflicts with a failure reason."
                        else if s[period_id] < R[first_period] or s[period_id] > R[last_period] or R[period_count] < R[minimum_period_count] or R[null_value_count] > R[acceptable_null_value_count] then "Readiness coverage does not support this period."
                        else if Record.Field(s,valueField) = null then "Value is missing." else null
                in [claimKey = id & "|" & s[reporting_version_ref], metricId=id, metricLabel=label,
                    rawValue=Record.Field(s,valueField), baseState=if Reason=null then "ELIGIBLE" else "WITHHELD", baseReason=Reason,
                    period=s[period_id], scope=s[scope_id], version=s[reporting_version_ref], unit="GBP_MINOR",
                    purpose="CFO_EXECUTIVE_REVIEW", authority=s[value_authority], reliabilityStatus=s[reliability_status], reliabilityPurpose=s[reliability_purpose],
                    readinessStatus=if Unique then R[readiness_status] else "UNASSESSED", policyVersion="POLICY_VERSION",
                    deliveryRef="DELIVERY_REF",deliveryDigest="DELIVERY_DIGEST", sourceDigest=s[source_package_digest],
                    evidenceRef=tableName & " / " & id & " / " & s[reporting_version_ref] & " / " & s[drill_through_relation], evidenceDigest=null]),
            Result = Table.FromRecords(Rows)
        in Result,
    Combined = Table.Combine({METRIC_SOURCES})
in Table.TransformColumnTypes(Combined, {{"rawValue", Int64.Type}})'''
for a,b in {'SOURCE_DIGEST':POLICY['sourceDigest'],'POLICY_VERSION':POLICY['version'],'DELIVERY_REF':POLICY['deliveryRef'],'DELIVERY_DIGEST':POLICY['deliveryDigest'],'METRIC_SOURCES':',\n        '.join(metric_sources)}.items():
    m_source=m_source.replace(a,b)
nb.assert_balanced(m_source, 'KPI Claims')

measures={
 'Selected Purpose':'IF ( NOT ISFILTERED ( \'KPI Purpose\' ), "CFO_EXECUTIVE_REVIEW", SELECTEDVALUE ( \'KPI Purpose\'[Purpose], "AMBIGUOUS" ) )',
 'Claim Count':"COUNTROWS ( CALCULATETABLE ( 'KPI Claims', ALLSELECTED ( 'KPI Claims' ), ALLSELECTED ( 'Reporting Version' ) ) )",
 'Eligibility State':'''SWITCH ( TRUE(), [Claim Count] <> 1, "INVALID_CONTEXT", [Selected Purpose] <> "CFO_EXECUTIVE_REVIEW", "WITHHELD", SELECTEDVALUE ( 'KPI Claims'[baseState], "UNASSESSED" ) )''',
 'Display Value':'''IF ( [Eligibility State] = "ELIGIBLE", SELECTEDVALUE ( 'KPI Claims'[rawValue] ), BLANK() )''',
 'Failure Reason':'''SWITCH ( TRUE(), [Claim Count] <> 1, "Select exactly one metric, period and version.", [Selected Purpose] <> "CFO_EXECUTIVE_REVIEW", "This metric is not assessed for the selected purpose.", SELECTEDVALUE ( 'KPI Claims'[baseReason] ) )''',
 'Context State':'''IF ( [Claim Count] = 1, "VALID", "AMBIGUOUS" )'''
}
# SUMMARIZECOLUMNS groups the fact claim alongside the canonical version dimension.
# Every projected measure must stay blank for absent fact/version combinations;
# constant labels and ALLSELECTED counts otherwise keep the cross-product alive.
measures={name: f"IF ( ISEMPTY ( 'KPI Claims' ), BLANK(), {expr} )" for name,expr in measures.items()}
columns=list(roles)
columns=[c for c in columns if c not in ['displayValue','expectedRowCount','selectedPurpose','eligibilityState','failureReason','contextState']]+['rawValue','baseState','baseReason']
tmdl="table 'KPI Claims'\n\n"
for name,expr in measures.items():
    tmdl+=f"\tmeasure '{name}' = {expr}\n\n"
for name in columns:
    tmdl+=f"\tcolumn {name}\n\t\tdataType: {'int64' if name=='rawValue' else 'string'}\n\t\tsourceColumn: {name}\n\t\tsummarizeBy: none\n\t\tisHidden\n\n"
tmdl+="\tpartition 'KPI Claims' = m\n\t\tmode: import\n\t\tsource =\n"+'\n'.join('\t\t\t'+line for line in m_source.splitlines())+'\n'
nb.write_table('KPI Claims', tmdl)
nb.write_table('KPI Purpose', '''table 'KPI Purpose'

    column Purpose
        dataType: string
        sourceColumn: [Purpose]
        summarizeBy: none
        isHidden

    column 'Intended Use'
        dataType: string
        sourceColumn: [Intended Use]
        summarizeBy: none

    partition 'KPI Purpose' = calculated
        mode: import
        source = DATATABLE ( "Purpose", STRING, "Intended Use", STRING, { { "CFO_EXECUTIVE_REVIEW", "CFO executive review" }, { "STATUTORY_SIGN_OFF", "Statutory sign-off" } } )
'''.replace('    ','\t'))
nb.ref_tables(['KPI Claims', 'KPI Purpose'])
nb.add_relationships([
    ('f5377584-7eb2-4338-bcc5-e29060540001', 'KPI Claims', 'period', 'Period', 'Period ID'),
    ('f5377584-7eb2-4338-bcc5-e29060540002', 'KPI Claims', 'version', 'Reporting Version', 'Reporting Version Ref'),
])

page='a64b7d4392ce4d438640'
nb.register_page(page, nb.page(page, 'Governed KPI Review', filters=[nb.filter_value('Period','Period ID','2026-06')]))
for i,(mid,_metric) in enumerate(POLICY['metrics'].items()):
    vid=f'a64b7d4392ce4d4386{i:02d}'
    v=nb.visual(vid,GUID,24+i*416,120,400,540)
    measures_map={'displayValue':'Display Value','expectedRowCount':'Claim Count','selectedPurpose':'Selected Purpose','eligibilityState':'Eligibility State','failureReason':'Failure Reason','contextState':'Context State'}
    query={}
    for role in roles:
        prop=measures_map.get(role,role);kind='Measure' if role in measures_map else 'Column'
        table='Reporting Version' if role=='version' else 'KPI Claims'
        if role=='version':
            prop='Reporting Version Ref'
        query[role]={'projections':[{'field':nb.field(table,prop,kind),'queryRef':f'{table}.{prop}','nativeQueryRef':prop}]}
    v['visual']['query']={'queryState':query}
    v['visual']['visualContainerObjects']={'title':[{'properties':{'show':{'expr':{'Literal':{'Value':'false'}}}}}]}
    v['filterConfig']={'filters':[nb.filter_value('KPI Claims','metricId',mid)]}
    nb.write_visual(page, v)
# Native title and purpose slicer; failure mode uses a real unsupported purpose.
nb.write_visual(page, nb.page_header('a64b7d4392ce4d438699', 'Governed KPI Review',
    'Choose an intended use to see which figures are eligible. The default is CFO executive review.', width=700))
v=nb.visual('a64b7d4392ce4d438698','slicer',760,12,490,90)
v['visual']['query']={'queryState':{'Values':{'projections':[{
    'field':nb.field('KPI Purpose','Intended Use'),'queryRef':'KPI Purpose.Intended Use','nativeQueryRef':'Intended Use'}]}}}
nb.write_visual(page, v)
# CustomVisual binaries are staged by stage-package.py after packaging.
print('Generated capabilities, semantic adapter and Governed KPI Review page.')
