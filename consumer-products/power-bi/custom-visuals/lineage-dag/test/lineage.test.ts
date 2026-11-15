import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {parse, neighbourhood, findCycle, type Edge} from '../src/contract';
import {Visual} from '../src/visual';
import policy from '../policy.json';

type Row = Record<string, unknown>;

/** A small graph with the same shapes as the delivery: gold, boundary, symbolic. */
const DECLARED: [string, string, string, string][] = [
    // from, to, datasetId, transformationClass
    ['stg_reference__periods', 'dim_period', 'QF-D01', 'STRICT_TYPE_AND_CONFORM'],
    ['stg_accounting__trial_balance', 'mart_financial_performance_monthly', 'QF-D20', 'CONFORM_AND_AGGREGATE'],
    ['dim_period', 'mart_financial_performance_monthly', 'QF-D20', 'CONFORM_AND_AGGREGATE'],
    ['mart_financial_performance_monthly', 'mart_cfo_presented_operating_metrics', 'QF-D92', 'EXECUTIVE_PRESENTATION'],
    ['C1_MARTS', 'mart_model_readiness_controls', 'QF-D99', 'READINESS_CONTROLS'],
];
const GOLDS = new Set(DECLARED.map(([, to]) => to));
const SYMBOLIC = new Set(policy.symbolicCollections);
const kindOf = (id: string) =>
    SYMBOLIC.has(id) ? 'SYMBOLIC_COLLECTION' : GOLDS.has(id) ? 'GOLD_MODEL' : 'BOUNDARY';

function edges(patch: Row = {}, perEdge: (from: string, to: string) => Row = () => ({})): Row[] {
    return DECLARED.map(([from, to, datasetId, transformationClass]) => ({
        claimKey: `LINEAGE|${policy.deliveryRef}`,
        edgeId: `${from} -> ${to}`, fromNodeId: from, toNodeId: to, fromLabel: from, toLabel: to,
        fromKind: kindOf(from), toKind: 'GOLD_MODEL', edgeKind: policy.edgeKind,
        transformationClass, datasetId,
        declaredBronzeSources: to === 'mart_model_readiness_controls'
            ? 'MULTIPLE_GOVERNED_A24_SOURCES' : 'accounting__statutory_trial_balance',
        evidenceDepth: policy.evidenceDepth, lineagePolicyRef: policy.version,
        purpose: policy.purpose, authority: policy.authority, deliveryRef: policy.deliveryRef,
        deliveryDigest: policy.deliveryDigest, sourceDigest: policy.sourceDigest,
        evidenceRef: `${policy.file} / ${datasetId}`, evidenceDigest: null, contextState: 'VALID',
        expectedRowCount: DECLARED.length,
        ...patch, ...perEdge(from, to),
    }));
}

function view(data: Row[] = edges()) {
    const columns = Object.keys(data[0]).map(role => ({displayName: role, roles: {[role]: true}}));
    return {metadata: {columns}, table: {columns, rows: data.map(r => Object.values(r))}} as any;
}

test('declared edges resolve into typed nodes', () => {
    const graph = parse(view());
    assert.equal(graph.state, 'RESOLVED');
    assert.equal(graph.edges.length, 5);
    assert.equal(graph.nodes.get('dim_period')!.kind, 'GOLD_MODEL');
    assert.equal(graph.nodes.get('stg_reference__periods')!.kind, 'BOUNDARY');
    assert.equal(graph.nodes.get('C1_MARTS')!.kind, 'SYMBOLIC_COLLECTION');
});

test('a gold model met first as a dependency still gets its own dataset row', () => {
    // dim_period appears as a dependency of the financial mart before its own
    // row is reached in edge order.
    const reordered = [edges()[2], ...edges().filter((_, i) => i !== 2)];
    const graph = parse(view(reordered));
    const node = graph.nodes.get('dim_period')!;
    assert.equal(node.datasetId, 'QF-D01');
    assert.equal(node.transformationClass, 'STRICT_TYPE_AND_CONFORM');
});

test('bronze sources stay on the dataset and are never drawn as edges', () => {
    const graph = parse(view());
    const readiness = graph.nodes.get('mart_model_readiness_controls')!;
    assert.deepEqual(readiness.bronze, ['MULTIPLE_GOVERNED_A24_SOURCES']);
    // No edge originates from a bronze source name.
    assert.equal(graph.edges.some(e => e.from.includes('MULTIPLE_GOVERNED')), false);
    assert.equal(graph.nodes.has('MULTIPLE_GOVERNED_A24_SOURCES'), false);
});

test('the neighbourhood is direct dependencies and dependants only', () => {
    const graph = parse(view());
    const {upstream, downstream} = neighbourhood(graph, 'mart_financial_performance_monthly');
    assert.deepEqual(upstream.map(e => e.from).sort(),
        ['dim_period', 'stg_accounting__trial_balance']);
    assert.deepEqual(downstream.map(e => e.to), ['mart_cfo_presented_operating_metrics']);
    // Not transitive: the staging table is not reported as feeding the executive mart.
    assert.equal(neighbourhood(graph, 'mart_cfo_presented_operating_metrics').upstream.length, 1);
});

test('a cycle is a metadata error and the edges are still kept', () => {
    const cyclic: Edge[] = [
        {id: 'a', from: 'a', to: 'b', kind: policy.edgeKind},
        {id: 'b', from: 'b', to: 'c', kind: policy.edgeKind},
        {id: 'c', from: 'c', to: 'a', kind: policy.edgeKind},
    ];
    assert.notEqual(findCycle(cyclic), null);
    assert.equal(findCycle(parse(view()).edges), null);

    const looped = [...edges(), {
        ...edges()[0], edgeId: 'mart_cfo_presented_operating_metrics -> dim_period',
        fromNodeId: 'mart_cfo_presented_operating_metrics', toNodeId: 'dim_period',
        fromLabel: 'mart_cfo_presented_operating_metrics', toLabel: 'dim_period',
        fromKind: 'GOLD_MODEL', datasetId: 'QF-D01',
        transformationClass: 'STRICT_TYPE_AND_CONFORM', expectedRowCount: 6,
    }];
    const graph = parse(view(looped.map(e => ({...e, expectedRowCount: 6}))));
    assert.equal(graph.state, 'INCOMPLETE');
    assert.equal(graph.edges.length, 6, 'edges are kept despite the cycle');
    assert.ok(graph.checks.some(c => c.label === 'Acyclic' && c.state === 'BROKEN'));
});

test('a self-edge is reported without dropping it', () => {
    const selfed = edges().map((e, i) => i === 0
        ? {...e, edgeId: 'dim_period -> dim_period', fromNodeId: 'dim_period', fromLabel: 'dim_period',
           fromKind: 'GOLD_MODEL', toNodeId: 'dim_period', toLabel: 'dim_period'} : e);
    const graph = parse(view(selfed));
    assert.equal(graph.state, 'INCOMPLETE');
    assert.equal(graph.edges.length, 5);
    assert.ok(graph.checks.some(c => c.label === 'No self-edges' && c.state === 'BROKEN'));
});

test('evidence depth is declared and never upgraded', () => {
    const graph = parse(view());
    assert.ok(graph.checks.some(c => c.label === 'Evidence depth' && c.state === 'UNASSESSED'
        && c.detail.includes('no row-level proof')));
    assert.equal(parse(view(edges({evidenceDepth: 'ROW_LEVEL'}))).state, 'BLOCKED');
});

for (const [name, data] of Object.entries({
    'duplicate edge identity': [...edges(), edges()[0]],
    'unknown node kind': edges({}, (from) => from === 'C1_MARTS' ? {fromKind: 'MAGIC'} : {}),
    'unsupported edge kind': edges({edgeKind: 'INVENTED'}),
    'node with two identities': edges({}, (from, to) =>
        to === 'mart_financial_performance_monthly' && from === 'dim_period' ? {fromKind: 'BOUNDARY'} : {}),
    'wrong policy version': edges({lineagePolicyRef: 'v99'}),
    'wrong delivery digest': edges({deliveryDigest: 'sha256:wrong'}),
    'ambiguous context': edges({contextState: 'AMBIGUOUS'}),
    'edge count mismatch': edges({expectedRowCount: 99}),
})) test(`${name} never presents a resolved graph`, () => {
    assert.notEqual(parse(view(data)).state, 'RESOLVED');
});

test('empty, segmented and duplicate role input fail closed', () => {
    assert.equal(parse().state, 'BLOCKED');
    const segmented = view(); segmented.metadata.segment = {};
    assert.equal(parse(segmented).state, 'BLOCKED');
    const duplicated = view();
    duplicated.table.columns.push(duplicated.table.columns[0]);
    duplicated.table.rows.forEach((r: unknown[]) => r.push('duplicate'));
    assert.equal(parse(duplicated).state, 'BLOCKED');
});

test('DOM offers search, an edge list and a neighbourhood on selection', () => {
    const dom = new JSDOM('<div id="root"></div>');
    const g: any = globalThis;
    g.document = dom.window.document;
    const root = dom.window.document.getElementById('root')!;
    const host: any = {
        createSelectionManager: () => ({select: () => {}, showContextMenu: () => {}}),
        createSelectionIdBuilder: () => ({withTable: () => ({createSelectionId: () => ({})})}),
        colorPalette: {isHighContrast: false}, hostCapabilities: {allowInteractions: true},
        eventService: {renderingStarted: () => {}, renderingFinished: () => {}, renderingFailed: () => {}},
        tooltipService: {hide: () => {}},
    };
    const visual = new Visual({element: root, host} as any);
    visual.update({dataViews: [view()], viewport: {width: 900, height: 900}} as any);
    assert.equal(root.querySelectorAll('input.search').length, 1);
    assert.equal(root.querySelectorAll('button.node').length, 7);
    assert.equal(root.querySelectorAll('table tbody tr').length, 5);
    assert.equal(root.querySelectorAll('svg').length, 0, 'no diagram until a node is selected');
    assert.match(root.textContent!, /not drawn as edges/);

    const target = [...root.querySelectorAll('button.node')]
        .find(b => b.getAttribute('data-node') === 'mart_financial_performance_monthly') as HTMLButtonElement;
    target.click();
    assert.equal(root.querySelectorAll('svg').length, 1);
    assert.equal(root.querySelectorAll('table tbody tr').length, 3, 'edge list narrows to the selection');
    assert.match(root.textContent!, /Direct dependencies/);

    const scripted = edges({}, (from) => from === 'C1_MARTS' ? {fromLabel: '<img src=x onerror=alert(1)>'} : {});
    visual.update({dataViews: [view(scripted)], viewport: {width: 900, height: 900}} as any);
    assert.equal(root.querySelectorAll('img').length, 0);

    visual.update({dataViews: []} as any);
    assert.doesNotMatch(root.textContent!, /dim_period/);
});
