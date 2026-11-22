"""Generate reviewable PBIP bindings for P3 and the Exception Register.

Run from any directory. Does not alter C2 or create a Desktop cache.

Two tables are produced. `Assertions` normalises the 36 C2 delivery controls
and the 15 C1 readiness controls while keeping them distinguishable by source
and grain. `Exception Observations` emits one row per declared rule hit, so a
passing delivery yields an empty control class rather than an invented one.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'shared'))
import nexus_build as nb

POLICY = json.loads((HERE / 'policy.json').read_text(encoding='utf-8'))
GUID = 'NexusTieOutPanelD4B82E6A1C7F49538A0D2E95B7461FC3'
PAGE = 'd4b82e6a1c7f49538a0d'
TABLE = 'Assertions'
OBS = 'Exception Observations'

roles = nb.roles(
    grouping=[*nb.COMMON_IDENTITY, 'assertionId', 'assertionLabel', 'assertionType'],
    group_or_measure=[*nb.COMMON_CONTEXT, 'assertionSource', 'operator', 'unit', 'publishedResult',
                      'assertionPolicyRef', 'actualEvidenceRef', 'expectedEvidenceRef', 'failureRef',
                      'period', 'scope', 'version'],
    measure=['actualValue', 'expectedValue', 'sourceDifference', *nb.COMMON_MEASURE],
)
nb.emit_package(HERE, roles,
    optional={'evidenceDigest', 'actualEvidenceRef', 'expectedEvidenceRef', 'failureRef', 'sourceDifference',
              'period', 'scope', 'version'},
    window=128, name='nexusTieOutPanel', display_name='Nexus Tie-Out Panel', guid=GUID,
    description='Published and replayed control results side by side, with assertion types kept distinct.',
    rgb=(90, 58, 26))


def m_text(v):
    return 'null' if v is None else '"' + str(v).replace('"', '""') + '"'


def m_list(items):
    return '{' + ', '.join(items) + '}'


C2 = POLICY['sources']['C2_DELIVERY']
C1 = POLICY['sources']['C1_READINESS']

# ------------------------------------------------------- assertions table ---
assertions_m = '''let
    Root = Text.TrimEnd(Text.Trim(C2Root), {"\\", "/"}),
    Manifest = Json.Document(File.Contents(Root & "/delivery-manifest.json")),
    Seal = Text.Trim(Text.FromBinary(File.Contents(Root & "/finance-delivery.digest"), TextEncoding.Utf8)),
    Verified = Manifest[delivery_ref] = "DELIVERY_REF" and Manifest[status] = "PUBLISHED"
        and Seal = "DELIVERY_DIGEST",
    Recon = if Verified then Json.Document(File.Contents(Root & "/metadata/reconciliation.json"))
        else error "C2 package identity differs. Set C2Root to the verified Q-FINANCE-C2@v1 directory.",
    ContractOk = Recon[contract_version] = "C2_CONTRACT",
    // reconciliation.json has no comparison_operator. EQUAL is this adapter's
    // declaration against the contract version above, not a source column.
    C2Rows = List.Transform(Recon[rows], (r) =>
        let
            id = r[control_id],
            kind = if Text.StartsWith(id, "PARITY_PREFIX") then "DELIVERY_PARITY"
                else if List.Contains(SOURCE_BINDING_IDS, id) then "SOURCE_BINDING"
                else "ARITHMETIC"
        in [
            claimKey = "C2_DELIVERY|DELIVERY_REF", assertionSource = "C2_DELIVERY",
            assertionId = id, assertionLabel = r[table_name], assertionType = kind,
            operator = if ContractOk then "EQUAL" else "UNDECLARED", unit = "COUNT",
            actualValue = Number.From(r[actual_value]), expectedValue = Number.From(r[expected_value]),
            sourceDifference = Number.From(r[difference]), publishedResult = r[status],
            evidenceRef = r[evidence], actualEvidenceRef = r[evidence], expectedEvidenceRef = null,
            failureRef = null, evidenceDigest = null,
            purpose = "PURPOSE", authority = "C2_DELIVERY_CONTROL",
            assertionPolicyRef = "POLICY_VERSION", deliveryRef = "DELIVERY_REF",
            deliveryDigest = "DELIVERY_DIGEST", sourceDigest = "SOURCE_DIGEST",
            contextState = if ContractOk then "VALID" else "AMBIGUOUS"
        ]),
    C1Rows = List.Transform(Table.ToRecords(ReadC2("mart_model_readiness_controls")), (r) => [
        claimKey = "C1_READINESS|DELIVERY_REF", assertionSource = "C1_READINESS",
        assertionId = r[control_id], assertionLabel = r[control_name],
        assertionType = if r[comparison_operator] = "EQUAL" then "ARITHMETIC" else "THRESHOLD",
        operator = r[comparison_operator], unit = "COUNT",
        actualValue = Number.From(r[actual_value]), expectedValue = Number.From(r[expected_value]),
        sourceDifference = null, publishedResult = r[result_status],
        evidenceRef = r[evidence_relation] & " / " & r[validator_ref],
        actualEvidenceRef = r[evidence_relation], expectedEvidenceRef = null,
        failureRef = if r[first_failure_ref] = "\\N" then null else r[first_failure_ref],
        evidenceDigest = null,
        purpose = "PURPOSE", authority = r[value_authority],
        assertionPolicyRef = "POLICY_VERSION", deliveryRef = "DELIVERY_REF",
        deliveryDigest = "DELIVERY_DIGEST", sourceDigest = r[source_package_digest],
        contextState = if r[source_package_digest] = "SOURCE_DIGEST" then "VALID" else "AMBIGUOUS"
    ])
in
    Table.TransformColumnTypes(Table.FromRecords(C2Rows & C1Rows),
        {{"actualValue", Int64.Type}, {"expectedValue", Int64.Type}, {"sourceDifference", Int64.Type}})'''

for token, value in sorted({
    'DELIVERY_REF': POLICY['deliveryRef'], 'DELIVERY_DIGEST': POLICY['deliveryDigest'],
    'SOURCE_DIGEST': POLICY['sourceDigest'], 'POLICY_VERSION': POLICY['version'], 'PURPOSE': POLICY['purpose'],
    'C2_CONTRACT': POLICY['c2ContractVersion'], 'PARITY_PREFIX': C2['parityPrefix'],
    'SOURCE_BINDING_IDS': m_list(m_text(i) for i in C2['sourceBindingIds']),
}.items(), key=lambda kv: -len(kv[0])):
    assertions_m = assertions_m.replace(token, value)
nb.assert_balanced(assertions_m, TABLE)

# -------------------------------------------------- exception observations ---
rules = [
    'Observe({}, {}, {}, {}, {}, {}, {}, {}, {}, {}, {})'.format(
        m_text(o['rule']), m_text(o['class']), m_text(o['label']), m_text(o['table']), m_text(o['field']),
        m_text(o['metric']), m_text(o['unit']), m_text(o['operator']),
        'null' if o['expected'] is None else str(o['expected']),
        m_text(o['affectedPurpose']), m_text(o['relation']))
    for o in POLICY['observations']]

OBS_TYPE = ('type table [observationId = text, ruleRef = text, observationClass = text, observationLabel = text, '
            'sourceRelation = text, sourceRowKey = text, period = text, scope = text, version = text, '
            'metric = text, observedValue = Int64.Type, unit = text, operator = nullable text, '
            'expectedValue = nullable Int64.Type, machineResult = text, resultReason = text, '
            'evidenceRef = text, affectedPurpose = text, governanceLinks = text]')

observations_m = '''let
    // One row per rule hit. A rule that is satisfied everywhere contributes
    // nothing: an empty class is a legitimate passing state, not a gap.
    Observe = (rule as text, cls as text, label as text, tableName as text, field as text, metric as text,
               unit as text, operator as nullable text, expected as nullable number,
               affectedPurpose as text, relation as text) as list =>
        let
            Rows = Table.ToRecords(ReadC2(tableName)),
            Baseline = if expected = null then 0 else expected,
            Hits = List.Select(Rows, (r) =>
                Record.Field(r, field) <> null and Number.From(Record.Field(r, field)) <> Baseline)
        in
            List.Transform(List.Positions(Hits), (i) =>
                let
                    r = Hits{i},
                    version = r[reporting_version_ref],
                    period = r[period_id],
                    scope = Text.Replace(Text.Replace(version, "RV-", ""), "-" & period & "@v1", ""),
                    ordinal = Text.PadStart(Text.From(i + 1), 5, "0")
                in [
                    observationId = rule & "#" & ordinal,
                    ruleRef = rule, observationClass = cls, observationLabel = label,
                    sourceRelation = relation, sourceRowKey = version & " / " & field & " #" & ordinal,
                    period = period, scope = scope, version = version,
                    metric = metric, observedValue = Number.From(Record.Field(r, field)), unit = unit,
                    operator = operator, expectedValue = expected,
                    // An exposure indicator has no registered threshold, so it is
                    // recorded and left unassessed rather than called a failure.
                    machineResult = if cls = "CONTROL" then "FAIL" else "NOT_ASSESSED",
                    resultReason = if cls = "CONTROL"
                        then "Observed value differs from the registered expected value."
                        else "EXPOSURE_NOTE",
                    evidenceRef = tableName & " / " & version & " / " & field,
                    affectedPurpose = affectedPurpose, governanceLinks = "GOVERNANCE_LINKS"
                ]),
    All = List.Combine({RULES})
in
    Table.FromRecords(All, OBS_TYPE)'''

for token, value in sorted({
    'RULES': ',\n        '.join(rules), 'OBS_TYPE': OBS_TYPE,
    'EXPOSURE_NOTE': POLICY['exposureNote'], 'GOVERNANCE_LINKS': POLICY['governanceLinkState'],
}.items(), key=lambda kv: -len(kv[0])):
    observations_m = observations_m.replace(token, value)
nb.assert_balanced(observations_m, OBS)

# ----------------------------------------------------------------- tables ---
selected = f"CALCULATETABLE ( '{TABLE}', ALLSELECTED ( '{TABLE}' ) )"
measures = {
    'Actual Value': f"SUM ( '{TABLE}'[actualValue] )",
    'Expected Value': f"SUM ( '{TABLE}'[expectedValue] )",
    'Source Difference': f"SUM ( '{TABLE}'[sourceDifference] )",
    'Assertion Count': f"COUNTROWS ( {selected} )",
    'Assertion Context State': (
        f"VAR Selected = {selected} "
        f"VAR Sources = COUNTROWS ( DISTINCT ( SELECTCOLUMNS ( Selected, \"s\", '{TABLE}'[assertionSource] ) ) ) "
        f"VAR Invalid = COUNTROWS ( FILTER ( Selected, '{TABLE}'[contextState] <> \"VALID\" ) ) "
        "RETURN IF ( Sources = 1 && ISBLANK ( Invalid ), \"VALID\", \"AMBIGUOUS\" )"),
}
measures = {name: f"IF ( ISEMPTY ( '{TABLE}' ), BLANK(), {expr} )" for name, expr in measures.items()}

INT_COLUMNS = {'actualValue', 'expectedValue', 'sourceDifference'}
columns = ['claimKey', 'assertionSource', 'assertionId', 'assertionLabel', 'assertionType', 'operator', 'unit',
           'actualValue', 'expectedValue', 'sourceDifference', 'publishedResult', 'evidenceRef', 'actualEvidenceRef',
           'expectedEvidenceRef', 'failureRef', 'evidenceDigest', 'purpose', 'authority', 'assertionPolicyRef',
           'deliveryRef', 'deliveryDigest', 'sourceDigest', 'contextState']

tmdl = f"table '{TABLE}'\n\n"
for name, expr in measures.items():
    tmdl += f"\tmeasure '{name}' = {expr}\n\n"
for name in columns:
    tmdl += (f"\tcolumn {name}\n\t\tdataType: {'int64' if name in INT_COLUMNS else 'string'}\n"
             f"\t\tsourceColumn: {name}\n\t\tsummarizeBy: none\n\t\tisHidden\n\n")
tmdl += (f"\tpartition '{TABLE}' = m\n\t\tmode: import\n\t\tsource =\n"
         + '\n'.join('\t\t\t' + line for line in assertions_m.splitlines()) + '\n')
nb.write_table(TABLE, tmdl)

OBS_INT = {'observedValue', 'expectedValue'}
OBS_COLUMNS = ['observationId', 'ruleRef', 'observationClass', 'observationLabel', 'sourceRelation', 'sourceRowKey',
               'period', 'scope', 'version', 'metric', 'observedValue', 'unit', 'operator', 'expectedValue',
               'machineResult', 'resultReason', 'evidenceRef', 'affectedPurpose', 'governanceLinks']
NAMES = {'observationClass': 'Class', 'ruleRef': 'Rule', 'period': 'Period', 'scope': 'Scope', 'metric': 'Metric',
         'observedValue': 'Observed', 'unit': 'Unit', 'operator': 'Operator', 'expectedValue': 'Expected',
         'machineResult': 'Machine result', 'affectedPurpose': 'Affected purpose', 'version': 'Reporting version',
         'observationLabel': 'Observation', 'sourceRelation': 'Source relation', 'evidenceRef': 'Evidence',
         'governanceLinks': 'Governance links', 'resultReason': 'Reason', 'sourceRowKey': 'Source row',
         'observationId': 'Observation ID'}

obs_tmdl = f"table '{OBS}'\n\n"
obs_tmdl += f"\tmeasure 'Observation Count' = COUNTROWS ( '{OBS}' )\n\t\tformatString: 0\n\n"
for name in OBS_COLUMNS:
    obs_tmdl += (f"\tcolumn '{NAMES.get(name, name)}'\n\t\tdataType: {'int64' if name in OBS_INT else 'string'}\n"
                 f"\t\tsourceColumn: {name}\n\t\tsummarizeBy: none\n\n")
obs_tmdl += (f"\tpartition '{OBS}' = m\n\t\tmode: import\n\t\tsource =\n"
             + '\n'.join('\t\t\t' + line for line in observations_m.splitlines()) + '\n')
nb.write_table(OBS, obs_tmdl)

# Every declared rule, so a rule that produced nothing reads as evaluated and
# clean rather than as a gap in the register.
INVENTORY = 'Rule Inventory'
rows = ', '.join('{{ "{r}", "{c}", "{l}" }}'.format(r=o['rule'], c=o['class'], l=o['label'])
                 for o in POLICY['observations'])
nb.write_table(INVENTORY, f"""table '{INVENTORY}'

\tmeasure 'Observations' = VAR n = COUNTROWS ( RELATEDTABLE ( '{OBS}' ) ) RETURN IF ( ISBLANK ( n ), 0, n )
\t\tformatString: 0

\tcolumn 'Rule'
\t\tdataType: string
\t\tsourceColumn: [Rule]
\t\tsummarizeBy: none

\tcolumn 'Rule class'
\t\tdataType: string
\t\tsourceColumn: [Class]
\t\tsummarizeBy: none

\tcolumn 'Rule label'
\t\tdataType: string
\t\tsourceColumn: [Observation]
\t\tsummarizeBy: none

\tpartition '{INVENTORY}' = calculated
\t\tmode: import
\t\tsource = DATATABLE ( "Rule", STRING, "Class", STRING, "Observation", STRING, {{ {rows} }} )
""")
nb.ref_tables([TABLE, OBS, INVENTORY])
nb.add_relationships([('d4b82e6a-1c7f-4953-8a0d-2e95b7461c01', OBS, 'Rule', INVENTORY, 'Rule')])

# ------------------------------------------------------------------- page ---
# No period filter: these are delivery-wide controls, and a month slicer must
# not relabel a package result as a selected-month result.
page_spec = nb.page(PAGE, 'Assurance Controls', height=1664)
page_spec['displayOption'] = 'FitToWidth'
nb.register_page(PAGE, page_spec)

MEASURE_ROLES = {'actualValue': 'Actual Value', 'expectedValue': 'Expected Value',
                 'sourceDifference': 'Source Difference', 'expectedRowCount': 'Assertion Count',
                 'contextState': 'Assertion Context State'}
# Delivery-wide roles are deliberately left unbound.
UNBOUND = {'period', 'scope', 'version'}
LAYOUT = {'C2_DELIVERY': (24, 96, 616, 820), 'C1_READINESS': (664, 96, 592, 820)}

for i, source in enumerate(POLICY['sources']):
    x, y, w, h = LAYOUT[source]
    v = nb.visual(f'd4b82e6a1c7f49538a{i:02d}', GUID, x, y, w, h)
    query = {}
    for role in roles:
        if role in UNBOUND:
            continue
        prop = MEASURE_ROLES.get(role, role)
        kind = 'Measure' if role in MEASURE_ROLES else 'Column'
        query[role] = {'projections': [{'field': nb.field(TABLE, prop, kind), 'queryRef': f'{TABLE}.{prop}',
                                        'nativeQueryRef': prop}]}
    v['visual']['query'] = {'queryState': query}
    v['visual']['visualContainerObjects'] = {'title': [{'properties': {'show': {'expr': {'Literal': {'Value': 'false'}}}}}]}
    v['filterConfig'] = {'filters': [nb.filter_value(TABLE, 'assertionSource', source)]}
    nb.write_visual(PAGE, v)

# Native register and class counts: the register is a reviewable list, not a
# single combined issue count.
nb.write_visual(PAGE, nb.table_visual('d4b82e6a1c7f49538a10', 24, 936, 892, 420, OBS,
    [('Class', 'Class'), ('Rule', 'Rule'), ('Period', 'Period'), ('Scope', 'Scope'), ('Metric', 'Metric'),
     ('Observed', 'Observed'), ('Unit', 'Unit'), ('Machine result', 'Machine result'),
     ('Affected purpose', 'Affected purpose')],
    'Exception register', sort=('Class', 'Ascending'),
    alt_text='Observations emitted by the registered exception rules. Exposure indicators are recorded, not assessed.'))

nb.write_visual(PAGE, nb.table_visual('d4b82e6a1c7f49538a11', 940, 936, 316, 420, OBS,
    [('Class', 'Class'), ('Observation Count', 'Observations', 'Measure')],
    'Observations by class',
    alt_text='Observation counts by class. Control and exposure classes are counted separately.'))

nb.write_visual(PAGE, nb.table_visual('d4b82e6a1c7f49538a12', 24, 1380, 1232, 260, INVENTORY,
    [('Rule class', 'Class'), ('Rule', 'Rule'), ('Rule label', 'Observation'),
     ('Observations', 'Observations emitted', 'Measure')],
    'Rules evaluated', sort=('Rule class', 'Ascending'),
    alt_text='Every declared exception rule. Zero means the rule emitted no observations.'))

nb.write_visual(PAGE, nb.page_header('d4b82e6a1c7f49538a99', 'Assurance Controls',
    'Review delivery-wide checks above. Scroll down for period observations, exposure indicators and the rules evaluated.'))

print(f'Generated capabilities, {TABLE} and {OBS} adapters, and the Assurance Controls page.')
