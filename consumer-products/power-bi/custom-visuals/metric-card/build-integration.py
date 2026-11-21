"""Bring the Nexus card design to the financial and assurance dashboards.

Run from any directory. Does not alter C2 or create a Desktop cache.

Each native KPI card is replaced in place by the dashboard tile, keeping its
position and its existing measure, so the figures the pages already show are
unchanged. Tile wording lives in a reviewable registry rather than in report
JSON, and the tile is explicitly a presentation primitive: it states a
measure's declared context and authority and makes no assurance claim.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'shared'))
import nexus_build as nb

POLICY = json.loads((HERE / 'policy.json').read_text(encoding='utf-8'))
GUID = 'NexusMetricCardA7F25B81D394C6E0472B9D53E18A6C4F'
TABLE = 'Dashboard Tiles'

roles = nb.roles(
    grouping=['tileKey', 'tileLabel'],
    group_or_measure=['caption', 'contextLine', 'authority', 'unit', 'deliveryRef', 'tilePolicyRef'],
    measure=['value'],
)
nb.emit_package(HERE, roles, optional=set(), window=2,
    name='nexusMetricCard', display_name='Nexus Metric Card', guid=GUID,
    description='Dashboard tile over a governed measure, stating its declared context and authority.',
    rgb=(22, 119, 110))

# ---------------------------------------------------------------- registry ---
COLUMNS = [('Tile Key', 'key'), ('Tile Label', 'label'), ('Tile Caption', 'caption'),
           ('Tile Context', 'context'), ('Tile Authority', 'authority'), ('Tile Unit', 'unit'),
           ('Tile Delivery', 'delivery'), ('Tile Policy', 'policy')]


def row(key, tile):
    cells = {'key': key, 'label': tile['label'], 'caption': tile['caption'], 'context': tile['context'],
             'authority': tile['authority'], 'unit': tile['unit'],
             'delivery': POLICY['deliveryRef'], 'policy': POLICY['version']}
    return '{ ' + ', '.join('"' + cells[field].replace('"', '""') + '"' for _, field in COLUMNS) + ' }'


datatable = 'DATATABLE ( ' + ', '.join(f'"{name}", STRING' for name, _ in COLUMNS) + ', {\n\t' \
    + ',\n\t'.join(row(key, tile) for key, tile in POLICY['tiles'].items()) + '\n} )'

tmdl = f"table '{TABLE}'\n\n"
for name, _ in COLUMNS:
    tmdl += (f"\tcolumn '{name}'\n\t\tdataType: string\n\t\tsourceColumn: [{name}]\n"
             f"\t\tsummarizeBy: none\n\t\tisHidden\n\n")
tmdl += f"\tpartition '{TABLE}' = calculated\n\t\tmode: import\n\t\tsource =\n"
tmdl += '\n'.join('\t\t\t' + line for line in datatable.splitlines()) + '\n'
nb.write_table(TABLE, tmdl)
nb.ref_tables([TABLE])

# ------------------------------------------------------------- page tiles ---
ROLE_COLUMN = {'tileKey': 'Tile Key', 'tileLabel': 'Tile Label', 'caption': 'Tile Caption',
               'contextLine': 'Tile Context', 'authority': 'Tile Authority', 'unit': 'Tile Unit',
               'deliveryRef': 'Tile Delivery', 'tilePolicyRef': 'Tile Policy'}

replaced = []
for key, tile in POLICY['tiles'].items():
    path = nb.REPORT / 'definition/pages' / tile['page'] / 'visuals' / tile['visual'] / 'visual.json'
    existing = json.loads(path.read_text(encoding='utf-8'))
    was = existing['visual']['visualType']
    query = {}
    for role in roles:
        if role == 'value':
            query[role] = {'projections': [{'field': nb.field(tile['table'], tile['measure'], 'Measure'),
                                            'queryRef': f"{tile['table']}.{tile['measure']}",
                                            'nativeQueryRef': tile['measure']}]}
        else:
            column = ROLE_COLUMN[role]
            query[role] = {'projections': [{'field': nb.field(TABLE, column), 'queryRef': f'{TABLE}.{column}',
                                            'nativeQueryRef': column}]}
    # Preserve the grid and give the card room for its context and authority.
    existing['position']['height'] = 120
    existing['visual'] = {
        'visualType': GUID,
        'query': {'queryState': query},
        'visualContainerObjects': {
            'title': [{'properties': {'show': {'expr': {'Literal': {'Value': 'false'}}}}}],
            'general': [{'properties': {'altText': {'expr': {'Literal': {
                'Value': f"'{tile['label']}. {tile['context']}. Hover for the full amount.'"}}}}}],
        },
    }
    existing['filterConfig'] = {'filters': [nb.filter_value(TABLE, 'Tile Key', key)]}
    nb.write_json(path, existing)
    replaced.append(f"{tile['page'][:8]}/{tile['visual'][-4:]} {was} -> tile ({key})")

print(f'Generated capabilities and the {TABLE} registry.')
for line in replaced:
    print(' ', line)
