import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {parse, classify, cellKey} from '../src/contract';
import {Visual} from '../src/visual';
import policy from '../policy.json';

type Row = Record<string, unknown>;
const PERIODS = ['2026-04', '2026-05', '2026-06'];
const SCOPES: [string, string][] = [
    ['NEXUS-GROUP', 'CONSOLIDATED_GROUP'], ['NEXUS-UK', 'LEGAL_ENTITY'], ['NEXUS-US', 'LEGAL_ENTITY'],
];

function cells(patch: Row = {}, perCell: (period: string, scope: string) => Row = () => ({})): Row[] {
    const out: Row[] = [];
    for (const period of PERIODS)
        for (const [scope, scopeType] of SCOPES)
            out.push({
                claimKey: `CLOSE_GRID|${policy.deliveryRef}`, period, scope, scopeType,
                version: `RV-${scope}-${period}@v1`,
                subledgerStatus: 'RECONCILED',
                bankStatus: scope === 'NEXUS-GROUP' ? 'CONSOLIDATED' : 'RECONCILED',
                intercompanyStatus: 'CONFIRMED', trialBalanceStatus: 'BALANCED', statementStatus: 'PUBLISHED',
                closeStatus: 'HARD_CLOSED', closedAt: '2026-06-30 23:00 UTC',
                softCloseEvent: 'AE-SOFT', hardCloseEvent: 'AE-HARD', publicationEvent: 'AE-PUB',
                gridPolicyRef: policy.version, purpose: policy.purpose, authority: policy.authority,
                deliveryRef: policy.deliveryRef, deliveryDigest: policy.deliveryDigest,
                sourceDigest: policy.sourceDigest, evidenceRef: `${policy.table} / RV-${scope}-${period}@v1`,
                evidenceDigest: null, contextState: 'VALID',
                expectedRowCount: PERIODS.length * SCOPES.length,
                ...patch, ...perCell(period, scope),
            });
    return out;
}

function view(data: Row[] = cells()) {
    const columns = Object.keys(data[0]).map(role => ({displayName: role, roles: {[role]: true}}));
    return {metadata: {columns}, table: {columns, rows: data.map(r => Object.values(r))}} as any;
}

test('the register reviews every period and scope', () => {
    const grid = parse(view());
    assert.equal(grid.state, 'REVIEWED');
    assert.equal(grid.periods.length, 3);
    assert.equal(grid.scopes.length, 3);
    assert.equal(grid.cells.size, 9);
    // Newest period first, consolidated scope first.
    assert.equal(grid.periods[0], '2026-06');
    assert.equal(grid.scopes[0].id, 'NEXUS-GROUP');
});

test('consolidated and not applicable are satisfied or declared, never failures', () => {
    assert.equal(classify('bankStatus', 'RECONCILED'), 'SATISFIED');
    assert.equal(classify('bankStatus', 'CONSOLIDATED'), 'SATISFIED');
    assert.equal(classify('bankStatus', 'NOT_APPLICABLE'), 'NOT_APPLICABLE');
    assert.equal(classify('intercompanyStatus', 'NOT_APPLICABLE'), 'NOT_APPLICABLE');
    const grid = parse(view(cells({}, (_p, scope) =>
        scope === 'NEXUS-US' ? {bankStatus: 'NOT_APPLICABLE', intercompanyStatus: 'NOT_APPLICABLE'} : {})));
    assert.equal(grid.state, 'REVIEWED');
    const cell = grid.cells.get(cellKey('2026-06', 'NEXUS-US'))!;
    assert.equal(cell.markers.find(m => m.key === 'bankStatus')!.state, 'NOT_APPLICABLE');
});

test('an unknown status stays visible and unclassified', () => {
    const grid = parse(view(cells({}, (period) => period === '2026-05' ? {bankStatus: 'PENDING_REVIEW'} : {})));
    assert.equal(classify('bankStatus', 'PENDING_REVIEW'), 'UNCLASSIFIED');
    const cell = grid.cells.get(cellKey('2026-05', 'NEXUS-UK'))!;
    const marker = cell.markers.find(m => m.key === 'bankStatus')!;
    assert.equal(marker.state, 'UNCLASSIFIED');
    assert.equal(marker.raw, 'PENDING_REVIEW');
    assert.ok(grid.checks.some(c => c.label.startsWith('Status values') && c.state === 'UNASSESSED'));
});

test('a missing required lifecycle event flags incomplete governance evidence', () => {
    const grid = parse(view(cells({}, (period, scope) =>
        period === '2026-06' && scope === 'NEXUS-UK' ? {hardCloseEvent: ''} : {})));
    assert.equal(grid.state, 'INCOMPLETE');
    const cell = grid.cells.get(cellKey('2026-06', 'NEXUS-UK'))!;
    assert.equal(cell.evidence.state, 'INCOMPLETE');
    assert.deepEqual(cell.evidence.missing, ['hardCloseEvent']);
    assert.ok(grid.checks.some(c => c.label.startsWith('Required lifecycle') && c.state === 'BROKEN'));
});

test('per-dimension counts are reported, never a percent complete', () => {
    const grid = parse(view());
    assert.equal(grid.tally.length, policy.dimensions.length);
    const bank = grid.tally.find(t => t.label === 'Bank')!;
    assert.match(bank.counts, /9 satisfied/);
    for (const entry of grid.tally) assert.doesNotMatch(entry.counts, /%/);
});

for (const [name, data] of Object.entries({
    'a second version for one period and scope': [...cells(), ...cells().slice(0, 1)],
    'version not matching its period and scope':
        cells({}, (period, scope) => scope === 'NEXUS-UK' ? {version: `RV-NEXUS-US-${period}@v1`} : {}),
    'two scope types for one scope': cells({}, (period, scope) =>
        scope === 'NEXUS-UK' && period === '2026-05' ? {scopeType: 'CONSOLIDATED_GROUP'} : {}),
    'wrong policy version': cells({gridPolicyRef: 'v99'}),
    'wrong delivery digest': cells({deliveryDigest: 'sha256:wrong'}),
    'wrong source digest': cells({sourceDigest: 'sha256:wrong'}),
    'ambiguous context': cells({contextState: 'AMBIGUOUS'}),
    'cell count mismatch': cells({expectedRowCount: 99}),
    'mixed claims': cells({}, (period) => period === '2026-04' ? {claimKey: 'OTHER'} : {}),
})) test(`${name} never presents a reviewed grid`, () => {
    assert.notEqual(parse(view(data)).state, 'REVIEWED');
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

test('DOM renders the grid, states carry text and stale cells clear', () => {
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
    visual.update({dataViews: [view()]} as any);
    assert.equal(root.querySelectorAll('table tbody tr').length, 3);
    assert.equal(root.querySelectorAll('table thead th').length, 4);
    // Every marker carries its initial and a symbol, not colour alone.
    assert.equal(root.querySelectorAll('.marker').length, 9 * 5 + 4);
    assert.match(root.textContent!, /No percent complete is computed/);
    assert.match(root.textContent!, /no reviewer sign-off identity/);

    const scripted = cells({}, () => ({closeStatus: '<img src=x onerror=alert(1)>'}));
    visual.update({dataViews: [view(scripted)]} as any);
    assert.equal(root.querySelectorAll('img').length, 0);

    visual.update({dataViews: []} as any);
    assert.doesNotMatch(root.textContent!, /NEXUS-UK/);
});
