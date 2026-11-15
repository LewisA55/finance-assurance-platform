"""Generate reviewable PBIP bindings and the pinned P6 lineage adapter.

Run from any directory. Does not alter C2 or create a Desktop cache.

One row per declared dependency edge. Pipe-delimited dependencies are split
and exact duplicates removed. Declared A24 bronze sources are carried on the
dataset, never crossed with its dependencies: the source file does not say
which bronze source feeds which dependency.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'shared'))
import nexus_build as nb

POLICY = json.loads((HERE / 'policy.json').read_text(encoding='utf-8'))
GUID = 'NexusLineageDagF18D6C40A932E5B74C81036FD2E9A5B7'
PAGE = 'f18d6c40a932e5b74c81'
TABLE = 'Lineage Edges'

roles = nb.roles(
    grouping=[*nb.COMMON_IDENTITY, 'edgeId', 'fromNodeId', 'toNodeId', 'fromLabel', 'toLabel', 'fromKind', 'toKind'],
    group_or_measure=[*nb.COMMON_CONTEXT, 'edgeKind', 'transformationClass', 'datasetId', 'declaredBronzeSources',
                      'evidenceDepth', 'lineagePolicyRef'],
    measure=[*nb.COMMON_MEASURE],
)
nb.emit_package(HERE, roles, optional={'evidenceDigest'}, window=256,
    name='nexusLineageDag', display_name='Nexus Lineage DAG', guid=GUID,
    description='Declared dataset dependencies with node kinds, transformation class and honest evidence depth.',
    rgb=(26, 86, 92))


def m_list(items):
    return '{' + ', '.join('"' + i.replace('"', '""') + '"' for i in items) + '}'


m_source = '''let
    Root = Text.TrimEnd(Text.Trim(C2Root), {"\\", "/"}),
    Manifest = Json.Document(File.Contents(Root & "/delivery-manifest.json")),
    Seal = Text.Trim(Text.FromBinary(File.Contents(Root & "/finance-delivery.digest"), TextEncoding.Utf8)),
    Verified = Manifest[delivery_ref] = "DELIVERY_REF" and Manifest[status] = "PUBLISHED"
        and Seal = "DELIVERY_DIGEST",
    Lineage = if Verified then Json.Document(File.Contents(Root & "/LINEAGE_FILE"))
        else error "C2 package identity differs. Set C2Root to the verified Q-FINANCE-C2@v1 directory.",
    ContractOk = Lineage[contract_version] = "LINEAGE_CONTRACT",
    Rows = Lineage[rows],
    Golds = List.Distinct(List.Transform(Rows, each _[gold_model])),
    Symbolic = SYMBOLIC_COLLECTIONS,
    // A node with no dataset row of its own is a boundary, not a gap to fill.
    KindOf = (id as text) as text =>
        if List.Contains(Symbolic, id) then "SYMBOLIC_COLLECTION"
        else if List.Contains(Golds, id) then "GOLD_MODEL"
        else "BOUNDARY",
    Edges = List.Combine(List.Transform(Rows, (r) =>
        let
            Deps = List.Select(List.Transform(Text.Split(r[direct_dependencies], "|"), Text.Trim), each _ <> "")
        in
            List.Transform(Deps, (d) => [
                edgeId = d & " -> " & r[gold_model],
                fromNodeId = d, toNodeId = r[gold_model],
                fromLabel = d, toLabel = r[gold_model],
                fromKind = KindOf(d), toKind = "GOLD_MODEL",
                edgeKind = "EDGE_KIND",
                transformationClass = r[transformation_class],
                datasetId = r[dataset_id],
                declaredBronzeSources = r[a24_bronze_sources],
                evidenceDepth = "EVIDENCE_DEPTH",
                claimKey = "LINEAGE|DELIVERY_REF",
                lineagePolicyRef = "POLICY_VERSION",
                purpose = "PURPOSE", authority = "AUTHORITY",
                deliveryRef = "DELIVERY_REF", deliveryDigest = "DELIVERY_DIGEST",
                sourceDigest = "SOURCE_DIGEST",
                evidenceRef = "LINEAGE_FILE / " & r[dataset_id],
                evidenceDigest = null,
                contextState = if ContractOk then "VALID" else "AMBIGUOUS"
            ])))
in
    Table.Distinct(Table.FromRecords(Edges), {"edgeId"})'''

for token, value in sorted({
    'DELIVERY_REF': POLICY['deliveryRef'], 'DELIVERY_DIGEST': POLICY['deliveryDigest'],
    'SOURCE_DIGEST': POLICY['sourceDigest'], 'POLICY_VERSION': POLICY['version'], 'PURPOSE': POLICY['purpose'],
    'AUTHORITY': POLICY['authority'], 'LINEAGE_CONTRACT': POLICY['contractVersion'],
    'LINEAGE_FILE': POLICY['file'], 'EDGE_KIND': POLICY['edgeKind'], 'EVIDENCE_DEPTH': POLICY['evidenceDepth'],
    'SYMBOLIC_COLLECTIONS': m_list(POLICY['symbolicCollections']),
}.items(), key=lambda kv: -len(kv[0])):
    m_source = m_source.replace(token, value)

nb.assert_balanced(m_source, TABLE)

selected = f"CALCULATETABLE ( '{TABLE}', ALLSELECTED ( '{TABLE}' ) )"
measures = {
    'Lineage Edge Count': f"COUNTROWS ( {selected} )",
    'Lineage Context State': (
        f"VAR Selected = {selected} "
        f"VAR Claims = COUNTROWS ( DISTINCT ( SELECTCOLUMNS ( Selected, \"c\", '{TABLE}'[claimKey] ) ) ) "
        f"VAR Invalid = COUNTROWS ( FILTER ( Selected, '{TABLE}'[contextState] <> \"VALID\" ) ) "
        "RETURN IF ( Claims = 1 && ISBLANK ( Invalid ), \"VALID\", \"AMBIGUOUS\" )"),
}
measures = {name: f"IF ( ISEMPTY ( '{TABLE}' ), BLANK(), {expr} )" for name, expr in measures.items()}

columns = ['claimKey', 'edgeId', 'fromNodeId', 'toNodeId', 'fromLabel', 'toLabel', 'fromKind', 'toKind',
           'edgeKind', 'transformationClass', 'datasetId', 'declaredBronzeSources', 'evidenceDepth',
           'lineagePolicyRef', 'purpose', 'authority', 'deliveryRef', 'deliveryDigest', 'sourceDigest',
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

# Lineage is delivery-wide metadata, so the page carries no period filter.
page_spec = nb.page(PAGE, 'Dataset Lineage', height=1180)
page_spec['displayOption'] = 'FitToWidth'
nb.register_page(PAGE, page_spec)

MEASURE_ROLES = {'expectedRowCount': 'Lineage Edge Count', 'contextState': 'Lineage Context State'}
v = nb.visual('f18d6c40a932e5b74c8100', GUID, 24, 96, 1232, 1060)
query = {}
for role in roles:
    prop = MEASURE_ROLES.get(role, role)
    kind = 'Measure' if role in MEASURE_ROLES else 'Column'
    query[role] = {'projections': [{'field': nb.field(TABLE, prop, kind), 'queryRef': f'{TABLE}.{prop}',
                                    'nativeQueryRef': prop}]}
v['visual']['query'] = {'queryState': query}
v['visual']['visualContainerObjects'] = {'title': [{'properties': {'show': {'expr': {'Literal': {'Value': 'false'}}}}}]}
nb.write_visual(PAGE, v)

v = nb.visual('f18d6c40a932e5b74c8199', 'textbox', 24, 12, 1000, 70)
v['visual']['objects'] = {'general': [{'properties': {'paragraphs': [
    {'textRuns': [{'value': 'NEXUS / DATASET LINEAGE', 'textStyle': {'fontSize': '22px', 'fontFamily': 'Segoe UI Semibold', 'color': '#162c43'}}]},
    {'textRuns': [{'value': 'Declared dependencies only | Symbolic collections left unresolved | Boundary nodes marked | Dataset depth, no row-level proof', 'textStyle': {'fontSize': '12px', 'color': '#566879'}}]}]}}]}
nb.write_visual(PAGE, v)

print(f'Generated capabilities, {TABLE} adapter and the Dataset Lineage page.')
