"""Shared PBIP and pbiviz integration helpers for the Nexus custom visuals.

Each visual owns its policy, semantic adapter and page layout. This module owns
what must stay identical across visuals: package metadata, the common role
contract C from the specification, PBIR field and filter construction, and the
model and page registries. It never reads or alters the sealed C2 delivery.
"""
import json
import struct
import zlib
from pathlib import Path

CUSTOM_VISUALS = Path(__file__).resolve().parents[1]
POWERBI = CUSTOM_VISUALS.parent
REPO = POWERBI.parents[1]
PBIP = POWERBI / 'NexusFinance'
MODEL = PBIP / 'NexusFinance.SemanticModel' / 'definition'
REPORT = PBIP / 'NexusFinance.Report'
DELIVERY = REPO / 'build/finance-delivery/Q-FINANCE-C2-V1'

API_VERSION = '5.11.1'
AUTHOR = {'name': 'Finance Assurance Platform (local development)', 'email': 'development@example.invalid'}

# Common roles C, specification section 3. A visual lists these alongside its
# own roles so the emitted order stays explicit and reviewable per package.
COMMON_IDENTITY = ['claimKey']
COMMON_CONTEXT = ['purpose', 'authority', 'deliveryRef', 'deliveryDigest', 'sourceDigest', 'evidenceRef', 'evidenceDigest', 'contextState']
COMMON_MEASURE = ['expectedRowCount']


def assert_balanced(m_source, label):
    """Fail at generation time if emitted M has unbalanced brackets.

    Power BI only reports this as a parser error when the project is opened,
    long after the generator has exited, so the check runs here instead.
    """
    closers = {')': '(', ']': '[', '}': '{'}
    stack = []
    i, n = 0, len(m_source)
    while i < n:
        c = m_source[i]
        if c == '"':  # M escapes a quote by doubling it
            i += 1
            while i < n:
                if m_source[i] == '"':
                    if i + 1 < n and m_source[i + 1] == '"':
                        i += 2
                        continue
                    break
                i += 1
        elif c == '/' and m_source[i + 1:i + 2] == '/':
            while i < n and m_source[i] != '\n':
                i += 1
        elif c in '([{':
            stack.append((c, i))
        elif c in closers:
            if not stack or stack[-1][0] != closers[c]:
                raise AssertionError(
                    f"{label}: unexpected {c!r} on line {m_source.count(chr(10), 0, i) + 1}")
            stack.pop()
        i += 1
    if stack:
        opener, at = stack[-1]
        raise AssertionError(f"{label}: unclosed {opener!r} opened on line {m_source.count(chr(10), 0, at) + 1}")


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def roles(grouping, group_or_measure, measure):
    """Ordered role name to capability kind. Order is the emitted role order."""
    ordered = {}
    for name in grouping:
        ordered[name] = 'Grouping'
    for name in group_or_measure:
        ordered[name] = 'GroupingOrMeasure'
    for name in measure:
        ordered[name] = 'Measure'
    return ordered


def emit_capabilities(here, role_map, optional, window):
    """One table mapping selecting every role, with explicit bounds per role.

    `window` is the display row budget: a single-claim visual uses 2 so an
    extra row is still detectable, a multirow bridge needs its step budget.
    """
    write_json(here / 'capabilities.json', {
        'privileges': [], 'dataRoles': [{'name': n, 'displayName': n, 'kind': k} for n, k in role_map.items()],
        'dataViewMappings': [{'conditions': [{n: {'min': 0 if n in optional else 1, 'max': 1} for n in role_map}],
            'table': {'rows': {'select': [{'for': {'in': n}} for n in role_map], 'dataReductionAlgorithm': {'window': {'count': window}}}}}],
        'objects': {}, 'supportsEmptyDataView': True, 'supportsLandingPage': True, 'supportsKeyboardFocus': True,
        'supportsHighlight': False, 'sorting': {'custom': {}}, 'tooltips': {'supportedTypes': {'default': True}}
    })


def emit_pbiviz(here, name, display_name, guid, description, version='0.1.0.0'):
    write_json(here / 'pbiviz.json', {
        'visual': {'name': name, 'displayName': display_name, 'guid': guid, 'visualClassName': 'Visual', 'version': version, 'description': description, 'supportUrl': 'https://github.com', 'gitHubUrl': ''},
        'apiVersion': API_VERSION, 'author': AUTHOR,
        'assets': {'icon': 'assets/icon.png'}, 'externalJS': None, 'style': 'style/visual.less', 'capabilities': 'capabilities.json', 'dependencies': None, 'stringResources': []
    })


def emit_style(here):
    (here / 'style').mkdir(exist_ok=True)
    (here / 'style/visual.less').write_text('/* Styles are scoped and bundled in src/styles.ts. */\n')


def emit_icon(here, rgb):
    """Small original raster icon, no external asset dependency."""
    (here / 'assets').mkdir(exist_ok=True)
    def chunk(k, d):
        return struct.pack('>I', len(d)) + k + d + struct.pack('>I', zlib.crc32(k + d) & 0xffffffff)
    fill = bytes((*rgb, 255))
    clear = bytes((255, 255, 255, 0))
    pixels = b''.join(b'\0' + b''.join(fill if (3 <= x < 17 and 3 <= y < 17) else clear for x in range(20)) for y in range(20))
    (here / 'assets/icon.png').write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 20, 20, 8, 6, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b''))


def emit_package(here, role_map, optional, window, name, display_name, guid, description, rgb):
    emit_capabilities(here, role_map, optional, window)
    emit_pbiviz(here, name, display_name, guid, description)
    emit_style(here)
    emit_icon(here, rgb)


def field(table, prop, kind='Column'):
    return {kind: {'Expression': {'SourceRef': {'Entity': table}}, 'Property': prop}}


def filter_value(table, prop, value):
    return {'name': f'{table}_{prop}_{value}', 'field': field(table, prop), 'type': 'Categorical', 'howCreated': 'User',
        'filter': {'Version': 2, 'From': [{'Name': 's', 'Entity': table, 'Type': 0}],
            'Where': [{'Condition': {'In': {'Expressions': [{'Column': {'Expression': {'SourceRef': {'Source': 's'}}, 'Property': prop}}], 'Values': [[{'Literal': {'Value': "'" + value + "'"}}]]}}}]}}


def visual(vid, typ, x, y, w, h):
    return {'$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json',
        'name': vid, 'position': {'x': x, 'y': y, 'width': w, 'height': h, 'z': 0, 'tabOrder': 0}, 'visual': {'visualType': typ}}


def table_visual(vid, x, y, w, h, entity, columns, title, sort=None, alt_text=None):
    """A native table over one entity. `columns` are (property, display[, kind])."""
    def literal(value):
        return {'expr': {'Literal': {'Value': value}}}

    spec = visual(vid, 'tableEx', x, y, w, h)
    projections = []
    for column in columns:
        prop, display = column[0], column[1]
        kind = column[2] if len(column) > 2 else 'Column'
        projections.append({'field': field(entity, prop, kind), 'queryRef': f'{entity}.{prop}',
                            'nativeQueryRef': prop, 'displayName': display})
    spec['visual']['query'] = {'queryState': {'Values': {'projections': projections}}}
    if sort:
        spec['visual']['query']['sortDefinition'] = {
            'sort': [{'field': field(entity, sort[0]), 'direction': sort[1]}], 'isDefaultSort': False}
    spec['visual']['visualContainerObjects'] = {
        'title': [{'properties': {'show': literal('true'), 'text': literal(f"'{title}'"),
                                  'fontColor': {'solid': {'color': literal("'#132841'")}},
                                  'fontSize': literal('13D')}}]}
    if alt_text:
        spec['visual']['visualContainerObjects']['general'] = [{'properties': {'altText': literal(f"'{alt_text}'")}}]
    spec['visual']['objects'] = {
        'total': [{'properties': {'totals': literal('false')}}],
        'columnHeaders': [{'properties': {'fontSize': literal('10D')}}],
        'values': [{'properties': {'fontSize': literal('10D')}}]}
    return spec


def page(page_id, display_name, width=1280, height=720, filters=None):
    return {'$schema': 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json',
        'name': page_id, 'displayName': display_name, 'displayOption': 'FitToPage', 'width': width, 'height': height,
        'filterConfig': {'filters': filters or []}}


def write_visual(page_id, spec):
    write_json(REPORT / 'definition/pages' / page_id / 'visuals' / spec['name'] / 'visual.json', spec)


def register_page(page_id, spec):
    write_json(REPORT / 'definition/pages' / page_id / 'page.json', spec)
    p = REPORT / 'definition/pages/pages.json'
    j = json.loads(p.read_text())
    if page_id not in j['pageOrder']:
        j['pageOrder'].append(page_id)
    write_json(p, j)


def ref_tables(names):
    p = MODEL / 'model.tmdl'
    s = p.read_text()
    for name in names:
        ref = f"ref table '{name}'"
        if ref not in s:
            s += '\n' + ref + '\n'
    p.write_text(s)


def add_relationships(rows):
    """rows: (relationship_id, from_column, to_table, to_column) on this visual's table."""
    p = MODEL / 'relationships.tmdl'
    s = p.read_text()
    for rid, from_table, col, table, to in rows:
        if rid not in s:
            s += f"\nrelationship {rid}\n\tfromColumn: '{from_table}'.{col}\n\ttoColumn: '{table}'.'{to}'\n"
    p.write_text(s)


def write_table(name, tmdl):
    (MODEL / 'tables' / f'{name}.tmdl').write_text(tmdl)
