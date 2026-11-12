import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {parse, replay} from '../src/contract';
import {Visual} from '../src/visual';
import policy from '../policy.json';

type Row = Record<string, unknown>;

const BASE = {
    purpose: policy.purpose, deliveryRef: policy.deliveryRef, deliveryDigest: policy.deliveryDigest,
    sourceDigest: policy.sourceDigest, assertionPolicyRef: policy.version, contextState: 'VALID',
    unit: 'COUNT', evidenceDigest: null, expectedEvidenceRef: null, failureRef: null,
};

/** The real C2 shape: 29 parity rows, 5 replayed differences, 2 source bindings. */
function c2Rows(patch: Row = {}, perRow: (id: string) => Row = () => ({})): Row[] {
    const ids = [
        ...Array.from({length: 29}, (_, i) => `C2-TABLE-${String(i + 1).padStart(2, '0')}`),
        'C2-READINESS', 'C2-BALANCE-SHEET', 'C2-CASH-FLOW', 'C2-REVENUE', 'C2-CFO-READINESS',
        'C2-TAX-EQUITY', 'C2-SOURCE-BINDING',
    ];
    return ids.map(id => ({
        ...BASE, claimKey: `C2_DELIVERY|${policy.deliveryRef}`, assertionSource: 'C2_DELIVERY',
        assertionId: id, assertionLabel: 'mart_example',
        assertionType: id.startsWith('C2-TABLE-') ? 'DELIVERY_PARITY'
            : ['C2-TAX-EQUITY', 'C2-SOURCE-BINDING'].includes(id) ? 'SOURCE_BINDING' : 'ARITHMETIC',
        operator: 'EQUAL', actualValue: 0, expectedValue: 0, sourceDifference: 0, publishedResult: 'PASS',
        evidenceRef: 'C1, CSV and Parquet share sha256:abc', actualEvidenceRef: 'C1, CSV and Parquet',
        authority: 'C2_DELIVERY_CONTROL', expectedRowCount: ids.length,
        ...patch, ...perRow(id),
    }));
}

/** C1 readiness: 14 EQUAL plus the one GREATER_THAN_OR_EQUAL that passes at 66 vs 60. */
function c1Rows(patch: Row = {}, perRow: (id: string) => Row = () => ({})): Row[] {
    const ids = Array.from({length: 15}, (_, i) => `C1-RDY-${String(i + 1).padStart(2, '0')}`);
    return ids.map(id => {
        const threshold = id === 'C1-RDY-01';
        return {
            ...BASE, claimKey: `C1_READINESS|${policy.deliveryRef}`, assertionSource: 'C1_READINESS',
            assertionId: id, assertionLabel: 'Readiness control',
            assertionType: threshold ? 'THRESHOLD' : 'ARITHMETIC',
            operator: threshold ? 'GREATER_THAN_OR_EQUAL' : 'EQUAL',
            actualValue: 66, expectedValue: threshold ? 60 : 66, sourceDifference: null,
            publishedResult: 'PASS', evidenceRef: 'gold.fct_x / validator', actualEvidenceRef: 'gold.fct_x',
            authority: 'MODEL_READINESS', expectedRowCount: ids.length,
            ...patch, ...perRow(id),
        };
    });
}

function view(data: Row[] = c2Rows()) {
    const columns = Object.keys(data[0]).map(role => ({displayName: role, roles: {[role]: true}}));
    return {metadata: {columns}, table: {columns, rows: data.map(r => Object.values(r))}} as any;
}

test('both declared sources agree and stay distinguishable', () => {
    const c2 = parse(view(c2Rows()));
    assert.equal(c2.state, 'AGREED');
    assert.equal(c2.assertions.length, 36);
    assert.equal(c2.label, 'C2 delivery controls');
    assert.equal(c2.byType.find(t => t.type === 'DELIVERY_PARITY')!.count, 29);
    assert.equal(c2.byType.find(t => t.type === 'SOURCE_BINDING')!.count, 2);

    const c1 = parse(view(c1Rows()));
    assert.equal(c1.state, 'AGREED');
    assert.equal(c1.assertions.length, 15);
    assert.equal(c1.byType.find(t => t.type === 'THRESHOLD')!.count, 1);
});

test('no claim is classified as an independent reconciliation', () => {
    for (const rows of [c2Rows(), c1Rows()]) {
        const panel = parse(view(rows));
        assert.equal(panel.byType.find(t => t.type === 'INDEPENDENT_RECONCILIATION')!.count, 0);
        assert.ok(panel.checks.some(c => c.label === 'Independent reconciliations' && c.state === 'UNASSESSED'));
    }
});

test('a threshold is not failed by a nonzero difference', () => {
    const panel = parse(view(c1Rows()));
    const threshold = panel.assertions.find(a => a.id === 'C1-RDY-01')!;
    assert.equal(threshold.operator, 'GREATER_THAN_OR_EQUAL');
    assert.equal(threshold.replayDifference, 6);
    assert.equal(threshold.replay, 'PASS');
    assert.equal(threshold.agrees, true);
    assert.equal(panel.state, 'AGREED');
    // The same operands under equality would fail.
    assert.equal(replay('EQUAL', 66, 60), 'FAIL');
    assert.equal(replay('GREATER_THAN_OR_EQUAL', 59, 60), 'FAIL');
});

test('a published pass with a failing replay is an explicit disagreement', () => {
    const panel = parse(view(c2Rows({}, (id) => id === 'C2-CASH-FLOW' ? {actualValue: 3} : {})));
    assert.equal(panel.state, 'DISAGREED');
    const row = panel.assertions.find(a => a.id === 'C2-CASH-FLOW')!;
    assert.equal(row.published, 'PASS');
    assert.equal(row.replay, 'FAIL');
    assert.equal(row.agrees, false);
    assert.ok(panel.checks.some(c => c.state === 'BROKEN' && c.detail.includes('neither result overwrites')));
});

test('unknown operators and missing operands are unassessed, not zero', () => {
    assert.equal(replay('BETWEEN', 1, 1), 'UNASSESSED');
    assert.equal(replay('EQUAL', null, 0), 'UNASSESSED');
    const panel = parse(view(c2Rows({}, (id) => id === 'C2-REVENUE' ? {operator: 'BETWEEN'} : {})));
    const row = panel.assertions.find(a => a.id === 'C2-REVENUE')!;
    assert.equal(row.replay, 'UNASSESSED');
    assert.equal(row.agrees, null);
    assert.notEqual(panel.state, 'DISAGREED');
});

test('a supplied diagnostic difference is checked against the replay', () => {
    const panel = parse(view(c2Rows({}, (id) => id === 'C2-REVENUE' ? {sourceDifference: 7} : {})));
    assert.ok(panel.checks.some(c => c.label.startsWith('Supplied diagnostic') && c.state === 'BROKEN'));
});

for (const [name, data] of Object.entries({
    'period bound to a delivery-wide control': c2Rows({period: '2026-06'}),
    'scope bound to a delivery-wide control': c2Rows({scope: 'NEXUS-GROUP'}),
    'version bound to a delivery-wide control': c2Rows({version: 'RV-NEXUS-GROUP-2026-06@v1'}),
    'independent reconciliation without two operand refs':
        c2Rows({}, (id) => id === 'C2-CASH-FLOW' ? {assertionType: 'INDEPENDENT_RECONCILIATION'} : {}),
    'unknown assertion type': c2Rows({}, (id) => id === 'C2-CASH-FLOW' ? {assertionType: 'VIBES'} : {}),
    'duplicate assertion id': [...c2Rows(), ...c2Rows().slice(0, 1)],
    'count mismatch': c2Rows({expectedRowCount: 99}),
    'mixed sources': [...c2Rows().slice(0, 35), ...c1Rows().slice(0, 1)],
    'wrong policy version': c2Rows({assertionPolicyRef: 'v99'}),
    'wrong delivery digest': c2Rows({deliveryDigest: 'sha256:wrong'}),
    'ambiguous context': c2Rows({contextState: 'AMBIGUOUS'}),
})) test(`${name} never presents an affirmative panel`, () => {
    assert.notEqual(parse(view(data)).state, 'AGREED');
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

test('DOM shows both results side by side and clears between updates', () => {
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
    visual.update({dataViews: [view(c1Rows())]} as any);
    assert.equal(root.querySelectorAll('table tbody tr').length, 15);
    assert.match(root.textContent!, /two independent operand references are not supplied/);
    assert.match(root.textContent!, /Delivery-wide model readiness/);

    const scripted = c1Rows({}, (id) => id === 'C1-RDY-02' ? {assertionLabel: '<img src=x onerror=alert(1)>'} : {});
    visual.update({dataViews: [view(scripted)]} as any);
    assert.equal(root.querySelectorAll('img').length, 0);

    visual.update({dataViews: []} as any);
    assert.doesNotMatch(root.textContent!, /C1-RDY-01/);
});
