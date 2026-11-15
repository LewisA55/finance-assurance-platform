"""Generate reviewable PBIP bindings and the pinned P4 close-governance adapter.

Run from any directory. Does not alter C2 or create a Desktop cache.

One row per reporting version, which is the register's own grain. The adapter
classifies nothing: raw statuses are passed through and the renderer maps them
with the versioned dictionary, so an unknown value stays visible.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'shared'))
import nexus_build as nb

POLICY = json.loads((HERE / 'policy.json').read_text(encoding='utf-8'))
GUID = 'NexusCloseGridE7C34D918B2A4F67905E81D2A6C4B30F'
PAGE = 'e7c34d918b2a4f67905e'
TABLE = 'Close Grid'
DIMENSIONS = [d['key'] for d in POLICY['dimensions']]
EVENTS = ['softCloseEvent', 'hardCloseEvent', 'publicationEvent']

roles = nb.roles(
    grouping=[*nb.COMMON_IDENTITY, 'period', 'scope', 'scopeType', 'version'],
    group_or_measure=[*nb.COMMON_CONTEXT, *DIMENSIONS, 'closeStatus', 'closedAt', *EVENTS, 'gridPolicyRef'],
    measure=[*nb.COMMON_MEASURE],
)
nb.emit_package(HERE, roles, optional={'evidenceDigest', *EVENTS}, window=512,
    name='nexusCloseGrid', display_name='Nexus Close Grid', guid=GUID,
    description='Reporting-version close register with per-dimension statuses and lifecycle event evidence.',
    rgb=(62, 38, 92))

FIELD = {d['key']: d['field'] for d in POLICY['dimensions']}
dimension_fields = ',\n            '.join(f'{k} = r[{FIELD[k]}]' for k in DIMENSIONS)

m_source = '''let
    Source = ReadC2("TABLE_NAME"),
    Rows = List.Transform(Table.ToRecords(Source), (r) => [
            claimKey = "CLOSE_GRID|DELIVERY_REF",
            period = r[period_id], scope = r[scope_id], scopeType = r[scope_type],
            version = r[reporting_version_ref],
            DIMENSION_FIELDS,
            closeStatus = r[close_status],
            // Delivered as an offset timestamp; shown with its zone named.
            closedAt = try DateTime.ToText(
                    DateTimeZone.RemoveZone(DateTimeZone.ToUtc(r[closed_at])), "yyyy-MM-dd HH:mm") & " TIMEZONE"
                otherwise Text.From(r[closed_at]),
            softCloseEvent = r[soft_close_accounting_event_ref],
            hardCloseEvent = r[hard_close_accounting_event_ref],
            publicationEvent = r[reporting_publication_accounting_event_ref],
            gridPolicyRef = "POLICY_VERSION",
            purpose = "PURPOSE", authority = "AUTHORITY",
            deliveryRef = "DELIVERY_REF", deliveryDigest = "DELIVERY_DIGEST",
            sourceDigest = r[source_package_digest],
            evidenceRef = "TABLE_NAME / " & r[reporting_version_ref],
            evidenceDigest = null,
            contextState = if r[source_package_digest] = "SOURCE_DIGEST"
                and r[reliability_status] = "STATUS" and r[reliability_purpose] = "SOURCE_PURPOSE"
                then "VALID" else "AMBIGUOUS"
        ])
in
    Table.FromRecords(Rows)'''

for token, value in sorted({
    'TABLE_NAME': POLICY['table'], 'DELIVERY_REF': POLICY['deliveryRef'],
    'DELIVERY_DIGEST': POLICY['deliveryDigest'], 'SOURCE_DIGEST': POLICY['sourceDigest'],
    'POLICY_VERSION': POLICY['version'], 'PURPOSE': POLICY['purpose'], 'AUTHORITY': POLICY['authority'],
    'SOURCE_PURPOSE': POLICY['sourcePurpose'], 'STATUS': POLICY['status'], 'TIMEZONE': POLICY['timezone'],
    'DIMENSION_FIELDS': dimension_fields,
}.items(), key=lambda kv: -len(kv[0])):
    m_source = m_source.replace(token, value)

nb.assert_balanced(m_source, TABLE)

selected = f"CALCULATETABLE ( '{TABLE}', ALLSELECTED ( '{TABLE}' ) )"
measures = {
    'Close Cell Count': f"COUNTROWS ( {selected} )",
    'Close Context State': (
        f"VAR Selected = {selected} "
        f"VAR Claims = COUNTROWS ( DISTINCT ( SELECTCOLUMNS ( Selected, \"c\", '{TABLE}'[claimKey] ) ) ) "
        f"VAR Invalid = COUNTROWS ( FILTER ( Selected, '{TABLE}'[contextState] <> \"VALID\" ) ) "
        "RETURN IF ( Claims = 1 && ISBLANK ( Invalid ), \"VALID\", \"AMBIGUOUS\" )"),
}
measures = {name: f"IF ( ISEMPTY ( '{TABLE}' ), BLANK(), {expr} )" for name, expr in measures.items()}

columns = ['claimKey', 'period', 'scope', 'scopeType', 'version', *DIMENSIONS, 'closeStatus', 'closedAt',
           *EVENTS, 'gridPolicyRef', 'purpose', 'authority', 'deliveryRef', 'deliveryDigest', 'sourceDigest',
           'evidenceRef', 'evidenceDigest', 'contextState']

tmdl = f"table '{TABLE}'\n\n"
for name, expr in measures.items():
    tmdl += f"\tmeasure '{name}' = {expr}\n\n"
for name in columns:
    tmdl += (f"\tcolumn {name}\n\t\tdataType: string\n"
             f"\t\tsourceColumn: {name}\n\t\tsummarizeBy: none\n\t\tisHidden\n\n")
tmdl += (f"\tpartition '{TABLE}' = m\n\t\tmode: import\n\t\tsource =\n"
         + '\n'.join('\t\t\t' + line for line in m_source.splitlines()) + '\n')
nb.write_table(TABLE, tmdl)
nb.ref_tables([TABLE])
nb.add_relationships([('e7c34d91-8b2a-4f67-905e-81d2a6c4b301', TABLE, 'period', 'Period', 'Period ID')])

# No page filter: periods are the grid's rows, not a selection to narrow.
page_spec = nb.page(PAGE, 'Close Governance', height=1500)
page_spec['displayOption'] = 'FitToWidth'
nb.register_page(PAGE, page_spec)

MEASURE_ROLES = {'expectedRowCount': 'Close Cell Count', 'contextState': 'Close Context State'}
v = nb.visual('e7c34d918b2a4f67905e00', GUID, 24, 96, 1232, 1380)
query = {}
for role in roles:
    prop = MEASURE_ROLES.get(role, role)
    kind = 'Measure' if role in MEASURE_ROLES else 'Column'
    query[role] = {'projections': [{'field': nb.field(TABLE, prop, kind), 'queryRef': f'{TABLE}.{prop}',
                                    'nativeQueryRef': prop}]}
v['visual']['query'] = {'queryState': query}
v['visual']['visualContainerObjects'] = {'title': [{'properties': {'show': {'expr': {'Literal': {'Value': 'false'}}}}}]}
nb.write_visual(PAGE, v)

v = nb.visual('e7c34d918b2a4f67905e99', 'textbox', 24, 12, 1000, 70)
v['visual']['objects'] = {'general': [{'properties': {'paragraphs': [
    {'textRuns': [{'value': 'NEXUS / CLOSE GOVERNANCE', 'textStyle': {'fontSize': '22px', 'fontFamily': 'Segoe UI Semibold', 'color': '#162c43'}}]},
    {'textRuns': [{'value': 'Periods by reporting scope | Five status dimensions kept separate | Lifecycle event evidence per version | Read-only review surface', 'textStyle': {'fontSize': '12px', 'color': '#566879'}}]}]}}]}
nb.write_visual(PAGE, v)

print(f'Generated capabilities, {TABLE} adapter and the Close Governance page.')
