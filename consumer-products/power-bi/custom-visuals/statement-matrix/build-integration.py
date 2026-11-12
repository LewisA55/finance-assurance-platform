"""Generate reviewable PBIP bindings and the pinned P1 semantic adapter.

Run from any directory. Does not alter C2 or create a Desktop cache.
Package metadata, role bounds and PBIR construction come from
`../shared/nexus_build.py`; everything below is P1's own contract.

The adapter keeps the source lines and their amounts untouched and adds the
registered presentation scaffold around them. Derived subtotals are computed
only where the registry declares a formula, and carry their own evidence
reference rather than a source line's digest.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'shared'))
import nexus_build as nb

POLICY = json.loads((HERE / 'policy.json').read_text(encoding='utf-8'))
GUID = 'NexusStatementMatrixC3A9F57E1B6D4A28B904E7D63F15C8B2'
PAGE = 'c3a9f57e1b6d4a28b904'
TABLE = 'Statement Cells'
VALUED = ('LINE', 'SUPPLIED_TOTAL', 'MEMO', 'DERIVED_SUBTOTAL')

roles = nb.roles(
    grouping=[*nb.COMMON_IDENTITY, 'rowKey', 'rowLabel', 'rowOrder', 'rowKind', 'indentLevel', 'ruleStyle',
              'columnKey', 'columnLabel', 'columnOrder'],
    group_or_measure=[*nb.COMMON_CONTEXT, 'statementClass', 'period', 'scope', 'version', 'currency',
                      'signConvention', 'presentationPolicyRef', 'lineEligibility', 'lineFailureReason'],
    measure=['amountMinor', *nb.COMMON_MEASURE],
)
nb.emit_package(HERE, roles, optional={'evidenceDigest', 'lineFailureReason'}, window=128,
    name='nexusStatementMatrix', display_name='Nexus Statement Matrix', guid=GUID,
    description='Finance statement layout over delivered lines, with replayed subtotals and preserved source totals.',
    rgb=(26, 62, 92))

# ---------------------------------------------------------------- adapter ---
def m_text(value):
    return '"' + str(value).replace('"', '""') + '"'


def m_list(items):
    return '{' + ', '.join(items) + '}'


statements = []
for cls, st in POLICY['statements'].items():
    registry = m_list(
        m_list([m_text(r['kind']), m_text(r['key']), m_text(r['label']), str(r['indent']), m_text(r['rule']),
                m_list(m_text(f) for f in r.get('formula', []))])
        for r in st['rows'])
    statements.append(f'Build({m_text(cls)}, {registry}, {st["sourceLineCount"]}, {m_text(st["signConvention"])})')

m_source = '''let
    Months = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"},
    ColumnLabel = (p as text) as text => Months{Number.FromText(Text.End(p, 2)) - 1} & " " & Text.Start(p, 4),
    // Buffered once: every period and column below re-reads this table.
    Source = Table.Buffer(Table.SelectRows(ReadC2("TABLE_NAME"), each [scope_id] = "SCOPE")),
    Periods = List.Sort(List.Distinct(Table.Column(Source, "period_id"))),
    PriorOf = (p as text) as nullable text =>
        let i = List.PositionOf(Periods, p) in if i <= 0 then null else Periods{i - 1},
    Build = (statementClass as text, registry as list, sourceLineCount as number, signConvention as text) as table =>
        let
            Lines = Table.Buffer(Table.SelectRows(Source, each [statement_class] = statementClass)),
            RecordsFor = (p as text) as list => Table.ToRecords(Table.SelectRows(Lines, each [period_id] = p)),
            // Source amounts first, then registered formulas in scaffold order.
            ValuesFor = (p as text) as record =>
                let
                    Rows = RecordsFor(p),
                    Supplied = Record.FromList(
                        List.Transform(Rows, each [presented_amount_minor]),
                        List.Transform(Rows, each [metric_id]))
                in
                    List.Accumulate(registry, Supplied, (state, r) =>
                        if r{0} <> "DERIVED_SUBTOTAL" then state
                        else Record.AddField(state, r{1},
                            List.Sum(List.Transform(r{5}, (f) => Record.FieldOrDefault(state, f, null))))),
            Identical = (p as text) as logical =>
                let Rows = RecordsFor(p) in
                    List.Count(Rows) = sourceLineCount and List.AllTrue(List.Transform(Rows, (r) =>
                        r[reporting_version_ref] = "RV-SCOPE-" & p & "@v1" and r[currency] = "CURRENCY"
                        and r[value_authority] = "AUTHORITY" and r[reliability_status] = "STATUS"
                        and r[reliability_purpose] = "SOURCE_PURPOSE" and r[sign_convention] = signConvention
                        and r[source_package_digest] = "SOURCE_DIGEST")),
            CellsFor = (asOf as text) as list =>
                let
                    Columns = List.Select({asOf, PriorOf(asOf)}, each _ <> null),
                    Context = if List.AllTrue(List.Transform(Columns, Identical)) then "VALID" else "AMBIGUOUS",
                    Anchor = RecordsFor(asOf){0},
                    StatementEvidence = "TABLE_NAME / " & statementClass & " / RV-SCOPE-" & asOf & "@v1 / "
                        & Anchor[drill_through_relation]
                in
                    List.Combine(List.Transform(List.Positions(Columns), (c) =>
                        let
                            p = Columns{c},
                            Values = ValuesFor(p)
                        in
                            List.Transform(List.Positions(registry), (i) =>
                                let
                                    r = registry{i},
                                    valued = List.Contains({"LINE", "SUPPLIED_TOTAL", "MEMO", "DERIVED_SUBTOTAL"}, r{0}),
                                    amount = if valued then Record.FieldOrDefault(Values, r{1}, null) else null,
                                    derived = r{0} = "DERIVED_SUBTOTAL"
                                in [
                                    claimKey = statementClass & "|" & asOf & "|SCOPE",
                                    statementClass = statementClass, asOfPeriod = asOf,
                                    rowKey = r{1}, rowLabel = r{2}, rowOrder = i, rowKind = r{0},
                                    indentLevel = r{3}, ruleStyle = r{4},
                                    columnKey = p, columnLabel = ColumnLabel(p), columnOrder = c + 1,
                                    amountMinor = amount,
                                    period = p, scope = "SCOPE", version = "RV-SCOPE-" & p & "@v1",
                                    currency = "CURRENCY", signConvention = signConvention,
                                    presentationPolicyRef = "POLICY_VERSION",
                                    lineEligibility = if not valued then "NOT_APPLICABLE"
                                        else if amount = null then "BLOCKED" else "ELIGIBLE",
                                    lineFailureReason = if valued and amount = null
                                        then "No source line was delivered for this period." else null,
                                    purpose = "PURPOSE", authority = "AUTHORITY",
                                    deliveryRef = "DELIVERY_REF", deliveryDigest = "DELIVERY_DIGEST",
                                    sourceDigest = Anchor[source_package_digest],
                                    // A registered subtotal is evidenced by its formula, never by a
                                    // source line's digest copied across to imply it was delivered.
                                    evidenceRef = if derived
                                        then "REGISTERED FORMULA " & "POLICY_VERSION" & " / " & r{1} & " = "
                                            & Text.Combine(r{5}, " + ")
                                        else StatementEvidence,
                                    evidenceDigest = if derived then null else Anchor[evidence_digest],
                                    contextState = Context
                                ])))
        in
            Table.FromRecords(List.Combine(List.Transform(Periods, CellsFor))),
    Combined = Table.Combine({STATEMENTS})
in
    Table.TransformColumnTypes(Combined, {{"rowOrder", Int64.Type}, {"indentLevel", Int64.Type},
        {"columnOrder", Int64.Type}, {"amountMinor", Int64.Type}})'''

# Longest token first, so a short name is never substituted inside a longer one
# (PURPOSE inside SOURCE_PURPOSE).
for token, value in sorted({
    'TABLE_NAME': POLICY['table'], 'SOURCE_DIGEST': POLICY['sourceDigest'], 'POLICY_VERSION': POLICY['version'],
    'PURPOSE': POLICY['purpose'], 'DELIVERY_REF': POLICY['deliveryRef'], 'DELIVERY_DIGEST': POLICY['deliveryDigest'],
    'SOURCE_PURPOSE': POLICY['sourcePurpose'], 'AUTHORITY': POLICY['authority'], 'STATUS': POLICY['status'],
    'SCOPE': POLICY['scope'], 'CURRENCY': POLICY['currency'],
    'STATEMENTS': ',\n        '.join(statements),
}.items(), key=lambda kv: -len(kv[0])):
    m_source = m_source.replace(token, value)

# ---------------------------------------------------------------- measures ---
selected = f"CALCULATETABLE ( '{TABLE}', ALLSELECTED ( '{TABLE}' ) )"
measures = {
    'Statement Amount Minor': f"SUM ( '{TABLE}'[amountMinor] )",
    # Expected cell count for the supported selection, before display reduction.
    'Statement Cell Count': f"COUNTROWS ( {selected} )",
    'Statement Context State': (
        f"VAR Selected = {selected} "
        f"VAR Claims = COUNTROWS ( DISTINCT ( SELECTCOLUMNS ( Selected, \"c\", '{TABLE}'[claimKey] ) ) ) "
        f"VAR Invalid = COUNTROWS ( FILTER ( Selected, '{TABLE}'[contextState] <> \"VALID\" ) ) "
        "RETURN IF ( Claims = 1 && ISBLANK ( Invalid ), \"VALID\", \"AMBIGUOUS\" )"),
}
measures = {name: f"IF ( ISEMPTY ( '{TABLE}' ), BLANK(), {expr} )" for name, expr in measures.items()}

INT_COLUMNS = {'rowOrder', 'indentLevel', 'columnOrder', 'amountMinor'}
columns = ['claimKey', 'statementClass', 'asOfPeriod', 'rowKey', 'rowLabel', 'rowOrder', 'rowKind', 'indentLevel',
           'ruleStyle', 'columnKey', 'columnLabel', 'columnOrder', 'amountMinor', 'period', 'scope', 'version',
           'currency', 'signConvention', 'presentationPolicyRef', 'lineEligibility', 'lineFailureReason',
           'purpose', 'authority', 'deliveryRef', 'deliveryDigest', 'sourceDigest', 'evidenceRef', 'evidenceDigest',
           'contextState']

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
# Only the as-of period joins the calendar: a cell's own period may be the
# prior month, which the page filter must not remove.
nb.add_relationships([('c3a9f57e-1b6d-4a28-b904-e7d63f15c801', TABLE, 'asOfPeriod', 'Period', 'Period ID')])

# ------------------------------------------------------------------- page ---
page_spec = nb.page(PAGE, 'Statutory Statements', height=1324,
    filters=[nb.filter_value('Period', 'Period ID', '2026-06')])
page_spec['displayOption'] = 'FitToWidth'
nb.register_page(PAGE, page_spec)

MEASURE_ROLES = {'amountMinor': 'Statement Amount Minor', 'expectedRowCount': 'Statement Cell Count',
                 'contextState': 'Statement Context State'}
LAYOUT = {'INCOME_STATEMENT': (24, 96, 604, 760), 'BALANCE_SHEET': (652, 96, 604, 1100),
          'CASH_FLOW': (24, 880, 604, 420)}

for i, cls in enumerate(POLICY['statements']):
    x, y, w, h = LAYOUT[cls]
    v = nb.visual(f'c3a9f57e1b6d4a28b9{i:02d}', GUID, x, y, w, h)
    query = {}
    for role in roles:
        prop = MEASURE_ROLES.get(role, role)
        kind = 'Measure' if role in MEASURE_ROLES else 'Column'
        query[role] = {'projections': [{'field': nb.field(TABLE, prop, kind), 'queryRef': f'{TABLE}.{prop}',
                                        'nativeQueryRef': prop}]}
    v['visual']['query'] = {'queryState': query}
    v['visual']['visualContainerObjects'] = {'title': [{'properties': {'show': {'expr': {'Literal': {'Value': 'false'}}}}}]}
    v['filterConfig'] = {'filters': [nb.filter_value(TABLE, 'statementClass', cls)]}
    nb.write_visual(PAGE, v)

v = nb.visual('c3a9f57e1b6d4a28b999', 'textbox', 24, 12, 900, 70)
v['visual']['objects'] = {'general': [{'properties': {'paragraphs': [
    {'textRuns': [{'value': 'NEXUS / STATUTORY STATEMENTS', 'textStyle': {'fontSize': '22px', 'fontFamily': 'Segoe UI Semibold', 'color': '#162c43'}}]},
    {'textRuns': [{'value': 'Selected month and prior month | Executive order over unchanged source lines | Supplied totals preserved, registered subtotals replayed', 'textStyle': {'fontSize': '12px', 'color': '#566879'}}]}]}}]}
nb.write_visual(PAGE, v)

print(f'Generated capabilities, {TABLE} adapter and the Statutory Statements page.')
