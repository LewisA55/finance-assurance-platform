"""Generate reviewable PBIP bindings and the pinned P2 semantic adapter.

Run from any directory. Does not alter C2 or create a Desktop cache.
Package metadata, role bounds and PBIR construction come from
`../shared/nexus_build.py`; everything below is P2's own contract.

The adapter unpivots each wide schedule mart into ordered step rows. Component
closure is evaluated before aggregation so an aggregated schedule still reports
how many of its components failed, and two offsetting breaks cannot cancel.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'shared'))
import nexus_build as nb

POLICY = json.loads((HERE / 'policy.json').read_text())
GUID = 'NexusRollforwardBridgeB7E4C1A9D3F84E2B9065C7D18A34F052'
PAGE = 'b7e4c1a9d3f84e2b9065'
TABLE = 'Bridge Steps'

roles = nb.roles(
    grouping=[*nb.COMMON_IDENTITY, 'bridgeKey', 'stepKey', 'stepLabel', 'stepOrder', 'stepKind'],
    group_or_measure=[*nb.COMMON_CONTEXT, 'period', 'scope', 'version', 'currency', 'sourceStatus', 'assertionPolicyRef'],
    measure=['amountMinor', 'sourceDifferenceMinor', 'toleranceMinor', 'failedComponentCount', *nb.COMMON_MEASURE],
)
nb.emit_package(HERE, roles, optional={'evidenceDigest', 'sourceStatus', 'sourceDifferenceMinor'}, window=32,
    name='nexusRollforwardBridge', display_name='Nexus Rollforward Bridge', guid=GUID,
    description='Opening to closing schedule with replayed arithmetic closure and separate source assertions.',
    rgb=(22, 44, 67))

# ---------------------------------------------------------------- adapter ---
def m_list(values):
    return '{' + ', '.join(values) + '}'


sources = []
for key, b in POLICY['bridges'].items():
    movements = m_list(f'{{"{m["field"]}", "{m["label"]}", {m["sign"]}}}' for m in b['movements'])
    sources.append('Build("{k}", "{t}", "{sc}", {s}, "{a}", "{of}", "{ol}", {mv}, "{cf}", "{cl}", {df}, {sf})'.format(
        k=key, t=b['table'], sc=b['scope'],
        s='null' if b['scopeField'] is None else f'"{b["scopeField"]}"', a=b['authority'],
        of=b['opening']['field'], ol=b['opening']['label'], mv=movements,
        cf=b['closing']['field'], cl=b['closing']['label'],
        df='null' if b['differenceField'] is None else f'"{b["differenceField"]}"',
        sf='null' if b['statusField'] is None else f'"{b["statusField"]}"'))

m_source = '''let
    Build = (bridgeKey as text, tableName as text, scopeId as text, scopeField as nullable text, authority as text,
             openingField as text, openingLabel as text, movements as list,
             closingField as text, closingLabel as text,
             differenceField as nullable text, statusField as nullable text) as table =>
        let
            Raw = ReadC2(tableName),
            // Buffered once: every period below re-reads this table, and an
            // unbuffered parquet source is fetched again for each of them.
            Scoped = Table.Buffer(
                if scopeField = null then Raw else Table.SelectRows(Raw, each Record.Field(_, scopeField) = scopeId)),
            Closes = (r as record) as logical =>
                Record.Field(r, openingField)
                    + List.Sum(List.Transform(movements, (m) => m{2} * Record.Field(r, m{0})))
                    = Record.Field(r, closingField),
            Periods = List.Sort(List.Distinct(Table.Column(Scoped, "period_id"))),
            PeriodSteps = (p as text) as list =>
                let
                    Recs = Table.ToRecords(Table.SelectRows(Scoped, each [period_id] = p)),
                    First = Recs{0},
                    Version = "RV-" & scopeId & "-" & p & "@v1",
                    Total = (f as text) as number => List.Sum(List.Transform(Recs, (r) => Record.Field(r, f))),
                    Failed = List.Count(List.Select(Recs, (r) => not Closes(r))),
                    Agrees = List.AllTrue(List.Transform(Recs, (r) =>
                        r[reporting_version_ref] = Version and r[currency] = "CURRENCY"
                        and r[value_authority] = authority and r[source_package_digest] = "SOURCE_DIGEST")),
                    Context = if List.Count(Recs) > 0 and Agrees then "VALID" else "AMBIGUOUS",
                    Difference = if differenceField = null then null else Total(differenceField),
                    Statuses = if statusField = null then null
                        else List.Distinct(List.Transform(Recs, (r) => Record.Field(r, statusField))),
                    Status = if Statuses = null then null
                        else if List.Count(Statuses) = 1 then Statuses{0} else "MIXED",
                    Defs = List.Combine({
                        {{openingField, openingLabel, "OPENING", Total(openingField)}},
                        List.Transform(movements, (m) => {m{0}, m{1}, "MOVEMENT", m{2} * Total(m{0})}),
                        {{closingField, closingLabel, "CLOSING", Total(closingField)}}}),
                    Rows = List.Transform(List.Positions(Defs), (i) =>
                        let d = Defs{i} in [
                            claimKey = bridgeKey & "|" & Version, bridgeKey = bridgeKey,
                            stepKey = d{0}, stepLabel = d{1}, stepOrder = i, stepKind = d{2}, amountMinor = d{3},
                            period = p, scope = scopeId, version = Version, currency = "CURRENCY",
                            sourceDifferenceMinor = Difference, sourceStatus = Status,
                            toleranceMinor = TOLERANCE, assertionPolicyRef = "POLICY_VERSION",
                            failedComponentCount = Failed, purpose = "PURPOSE", authority = authority,
                            deliveryRef = "DELIVERY_REF", deliveryDigest = "DELIVERY_DIGEST",
                            sourceDigest = First[source_package_digest],
                            evidenceRef = tableName & " / " & bridgeKey & " / " & Version & " / "
                                & First[drill_through_relation],
                            evidenceDigest = null, contextState = Context])
                in Rows
        in
            Table.FromRecords(List.Combine(List.Transform(Periods, PeriodSteps))),
    Combined = Table.Combine({BRIDGE_SOURCES})
in
    Table.TransformColumnTypes(Combined, {{"stepOrder", Int64.Type}, {"amountMinor", Int64.Type},
        {"sourceDifferenceMinor", Int64.Type}, {"toleranceMinor", Int64.Type}, {"failedComponentCount", Int64.Type}})'''

# Longest token first, so a short name is never substituted inside a longer one.
for token, value in sorted({
    'SOURCE_DIGEST': POLICY['sourceDigest'], 'POLICY_VERSION': POLICY['version'], 'PURPOSE': POLICY['purpose'],
    'DELIVERY_REF': POLICY['deliveryRef'], 'DELIVERY_DIGEST': POLICY['deliveryDigest'],
    'CURRENCY': POLICY['currency'], 'TOLERANCE': str(POLICY['toleranceMinor']),
    'BRIDGE_SOURCES': ',\n        '.join(sources),
}.items(), key=lambda kv: -len(kv[0])):
    m_source = m_source.replace(token, value)

# ---------------------------------------------------------------- measures ---
nb.assert_balanced(m_source, TABLE)

selected = f"CALCULATETABLE ( '{TABLE}', ALLSELECTED ( '{TABLE}' ), ALLSELECTED ( 'Reporting Version' ) )"
measures = {
    'Amount Minor': f"SUM ( '{TABLE}'[amountMinor] )",
    'Tolerance Minor': f"MAX ( '{TABLE}'[toleranceMinor] )",
    'Failed Component Count': f"MAX ( '{TABLE}'[failedComponentCount] )",
    'Source Difference Minor': f"MAX ( '{TABLE}'[sourceDifferenceMinor] )",
    # Expected step count for the supported selection, before display reduction.
    'Step Count': f"COUNTROWS ( {selected} )",
    # Measure names are unique across the whole model, so this one is prefixed.
    'Bridge Context State': (
        f"VAR Selected = {selected} "
        f"VAR Claims = COUNTROWS ( DISTINCT ( SELECTCOLUMNS ( Selected, \"c\", '{TABLE}'[claimKey] ) ) ) "
        f"VAR Invalid = COUNTROWS ( FILTER ( Selected, '{TABLE}'[contextState] <> \"VALID\" ) ) "
        "RETURN IF ( Claims = 1 && ISBLANK ( Invalid ), \"VALID\", \"AMBIGUOUS\" )"),
}
# SUMMARIZECOLUMNS pairs the step fact with the canonical version dimension;
# every measure must stay blank for absent fact/version combinations.
measures = {name: f"IF ( ISEMPTY ( '{TABLE}' ), BLANK(), {expr} )" for name, expr in measures.items()}

INT_COLUMNS = {'stepOrder', 'amountMinor', 'sourceDifferenceMinor', 'toleranceMinor', 'failedComponentCount'}
columns = ['claimKey', 'bridgeKey', 'stepKey', 'stepLabel', 'stepOrder', 'stepKind', 'amountMinor', 'period', 'scope',
           'version', 'currency', 'sourceDifferenceMinor', 'sourceStatus', 'toleranceMinor', 'assertionPolicyRef',
           'failedComponentCount', 'purpose', 'authority', 'deliveryRef', 'deliveryDigest', 'sourceDigest',
           'evidenceRef', 'evidenceDigest', 'contextState']

tmdl = f"table '{TABLE}'\n\n"
for name, expr in measures.items():
    tmdl += f"\tmeasure '{name}' = {expr}\n\n"
for name in columns:
    tmdl += (f"\tcolumn {name}\n\t\tdataType: {'int64' if name in INT_COLUMNS else 'string'}\n"
             f"\t\tsourceColumn: {name}\n\t\tsummarizeBy: none\n\t\tisHidden\n\n")
tmdl += (f"\tpartition '{TABLE}' = m\n\t\tmode: import\n\t\tsource =\n"
         + '\n'.join('\t\t\t' + line for line in m_source.splitlines()) + '\n')
nb.write_table(TABLE, tmdl)
nb.ref_tables([TABLE])
nb.add_relationships([
    ('b7e4c1a9-d3f8-4e2b-9065-c7d18a34f001', TABLE, 'period', 'Period', 'Period ID'),
    ('b7e4c1a9-d3f8-4e2b-9065-c7d18a34f002', TABLE, 'version', 'Reporting Version', 'Reporting Version Ref'),
])

# ------------------------------------------------------------------- page ---
page_spec = nb.page(PAGE, 'Rollforward Assurance', height=3184,
    filters=[nb.filter_value('Period', 'Period ID', '2026-06')])
# Fit the width and scroll, rather than shrinking a tall page until its
# step labels and amounts stop being readable.
page_spec['displayOption'] = 'FitToWidth'
nb.register_page(PAGE, page_spec)

MEASURE_ROLES = {'amountMinor': 'Amount Minor', 'sourceDifferenceMinor': 'Source Difference Minor',
                 'toleranceMinor': 'Tolerance Minor', 'failedComponentCount': 'Failed Component Count',
                 'expectedRowCount': 'Step Count', 'contextState': 'Bridge Context State'}
# Cash leads at full width; the remaining eight pair up by statement area.
# Fixed assets sit together because they share an entity scope the others do not.
LAYOUT = {
    'CASH': (24, 96, 1232, 600),
    'DEFERRED_REVENUE': (24, 712, 604, 600), 'MRR': (652, 712, 604, 600),
    'DEBT': (24, 1328, 604, 600), 'LEASE': (652, 1328, 604, 600),
    'GROSS_ASSETS': (24, 1944, 604, 600), 'ACCUMULATED_DEPRECIATION': (652, 1944, 604, 600),
    'TAX_PAYABLE': (24, 2560, 604, 600), 'RETAINED_EARNINGS': (652, 2560, 604, 600),
}

for i, key in enumerate(POLICY['bridges']):
    x, y, w, h = LAYOUT[key]
    v = nb.visual(f'b7e4c1a9d3f84e2b90{i:02d}', GUID, x, y, w, h)
    # The accepted Reporting Version dimension is Group-only. Group schedules
    # bind it so the existing evidence drill-through keeps working; an
    # entity-scoped schedule has no row there and carries its own source
    # version instead, rather than being shown under a Group version it does
    # not have.
    group_scoped = POLICY['bridges'][key]['scope'] == 'NEXUS-GROUP'
    query = {}
    for role in roles:
        prop = MEASURE_ROLES.get(role, role)
        kind = 'Measure' if role in MEASURE_ROLES else 'Column'
        table = TABLE
        if role == 'version' and group_scoped:
            table, prop, kind = 'Reporting Version', 'Reporting Version Ref', 'Column'
        query[role] = {'projections': [{'field': nb.field(table, prop, kind), 'queryRef': f'{table}.{prop}',
                                        'nativeQueryRef': prop}]}
    v['visual']['query'] = {'queryState': query}
    v['visual']['visualContainerObjects'] = {'title': [{'properties': {'show': {'expr': {'Literal': {'Value': 'false'}}}}}]}
    v['filterConfig'] = {'filters': [nb.filter_value(TABLE, 'bridgeKey', key)]}
    nb.write_visual(PAGE, v)

v = nb.visual('b7e4c1a9d3f84e2b9099', 'textbox', 24, 12, 900, 70)
v['visual']['objects'] = {'general': [{'properties': {'paragraphs': [
    {'textRuns': [{'value': 'NEXUS / ROLLFORWARD ASSURANCE', 'textStyle': {'fontSize': '22px', 'fontFamily': 'Segoe UI Semibold', 'color': '#162c43'}}]},
    {'textRuns': [{'value': 'Nine schedules | Arithmetic replayed at zero tolerance | Source assertions kept separate | Each card states its own reporting scope', 'textStyle': {'fontSize': '12px', 'color': '#566879'}}]}]}}]}
nb.write_visual(PAGE, v)

print(f'Generated capabilities, {TABLE} adapter and the Rollforward Assurance page.')
