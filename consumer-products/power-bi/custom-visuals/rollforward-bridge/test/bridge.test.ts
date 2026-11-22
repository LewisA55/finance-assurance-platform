import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {parse} from '../src/contract';
import {Visual} from '../src/visual';
import {closure, ordered, running, type Step} from '../../shared/src/bridge';
import policy from '../policy.json';

const VERSION = 'RV-NEXUS-GROUP-2026-06@v1';
const CASH = policy.bridges.CASH;
// June 2026 Nexus Group cash, in minor units: 5,359,480.52 - 1,479,383.43 - 797,795.24 = 3,082,301.85.
const AMOUNT: Record<string, number> = {
    opening_cash_minor: 535948052, operating_cash_flow_minor: -147938343, investing_cash_flow_minor: 0,
    financing_cash_flow_minor: -79779524, fx_and_other_movement_minor: 0, closing_cash_minor: 308230185,
};

type Row = Record<string, unknown>;
const shared = {
    claimKey: `CASH|${VERSION}`, bridgeKey: 'CASH', period: '2026-06', scope: CASH.scope, version: VERSION,
    currency: policy.currency, purpose: policy.purpose, authority: CASH.authority, assertionPolicyRef: policy.version,
    deliveryRef: policy.deliveryRef, deliveryDigest: policy.deliveryDigest, sourceDigest: policy.sourceDigest,
    evidenceRef: 'mart_cash_flow_liquidity_monthly / CASH / ' + VERSION, evidenceDigest: null, contextState: 'VALID',
    sourceDifferenceMinor: 0, sourceStatus: 'RECONCILED', toleranceMinor: policy.toleranceMinor,
    failedComponentCount: 0, expectedRowCount: 6,
};

function rows(patch: Row = {}, perStep: Record<number, Row> = {}): Row[] {
    const defs = [
        {stepKey: CASH.opening.field, stepLabel: CASH.opening.label, stepKind: 'OPENING'},
        ...CASH.movements.map(m => ({stepKey: m.field, stepLabel: m.label, stepKind: 'MOVEMENT'})),
        {stepKey: CASH.closing.field, stepLabel: CASH.closing.label, stepKind: 'CLOSING'},
    ];
    return defs.map((d, i) => ({...shared, ...d, stepOrder: i, amountMinor: AMOUNT[d.stepKey], ...patch, ...perStep[i]}));
}

function view(data: Row[] = rows()) {
    const columns = Object.keys(data[0]).map(role => ({displayName: role, roles: {[role]: true}}));
    return {metadata: {columns}, table: {columns, rows: data.map(r => Object.values(r))}} as any;
}

test('a closing schedule asserts and reports its own replayed arithmetic', () => {
    const bridge = parse(view());
    assert.equal(bridge.state, 'ASSERTED');
    assert.equal(bridge.closure.state, 'TIED');
    assert.equal(bridge.closure.state === 'TIED' && bridge.closure.difference, 0);
    assert.equal(bridge.steps.length, 6);
    assert.equal(bridge.source.agrees, true);
});

test('a one minor unit break is reported, never absorbed', () => {
    const bridge = parse(view(rows({}, {5: {amountMinor: AMOUNT.closing_cash_minor + 1}})));
    assert.equal(bridge.state, 'BROKEN');
    assert.equal(bridge.closure.state, 'BROKEN');
    assert.equal(bridge.closure.state === 'BROKEN' && bridge.closure.difference, -1);
    // The published closing stays the final bar; no balancing plug is created.
    assert.equal(bridge.steps[5].amount, AMOUNT.closing_cash_minor + 1);
});

test('offsetting component breaks survive a clean net tie-out', () => {
    const bridge = parse(view(rows({failedComponentCount: 2})));
    assert.equal(bridge.closure.state, 'TIED');
    assert.equal(bridge.state, 'BROKEN');
    assert.equal(bridge.coverage.state, 'INCOMPLETE');
});

test('a supplied assertion that disagrees with the replay is shown, not resolved', () => {
    const bridge = parse(view(rows({sourceDifferenceMinor: 500})));
    assert.equal(bridge.closure.state, 'TIED');
    assert.equal(bridge.source.agrees, false);
    assert.equal(bridge.state, 'BROKEN');
});

for (const [name, data] of Object.entries({
    'missing movement': rows().filter((_, i) => i !== 2),
    'short step count': rows({expectedRowCount: 7}),
    'duplicate order': rows({}, {2: {stepOrder: 1}}),
    'unknown step': rows({}, {2: {stepKey: 'invented_minor'}}),
    'relabelled step': rows({}, {2: {stepLabel: 'Something else'}}),
    'wrong kind': rows({}, {2: {stepKind: 'CLOSING'}}),
    'unsafe amount': rows({}, {1: {amountMinor: Number.MAX_SAFE_INTEGER}}),
    'fractional amount': rows({}, {1: {amountMinor: 1.5}}),
    'mixed period': rows({}, {3: {period: '2026-05'}}),
    'mixed claim': rows({}, {3: {claimKey: `CASH|RV-NEXUS-GROUP-2026-05@v1`}}),
    'ambiguous context': rows({contextState: 'AMBIGUOUS'}),
    'wrong policy': rows({assertionPolicyRef: 'NEXUS-ROLLFORWARD-ASSERTION@v99'}),
    'wrong delivery digest': rows({deliveryDigest: 'sha256:wrong'}),
    'wrong source digest': rows({sourceDigest: 'sha256:wrong'}),
    'wrong authority': rows({authority: 'UNREVIEWED'}),
    'wrong purpose': rows({purpose: 'STATUTORY_SIGN_OFF'}),
    'wrong scope': rows({scope: 'NEXUS-US'}),
    'wrong currency': rows({currency: 'USD'}),
    'unsupported version': rows({version: 'RV-NEXUS-GROUP-2026-06@v2'}),
    'tolerance widened': rows({toleranceMinor: 100}),
})) test(`${name} never presents an affirmative assertion`, () => {
    const bridge = parse(view(data));
    assert.notEqual(bridge.state, 'ASSERTED');
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

/** Synthetic but pinned-shape rows for any schedule in the policy. */
function bridgeRows(key: string): Row[] {
    const b = (policy.bridges as Record<string, any>)[key];
    const version = `RV-${b.scope}-2026-06@v1`;
    const defs: Row[] = [
        {stepKey: b.opening.field, stepLabel: b.opening.label, stepKind: 'OPENING', amountMinor: 1_000_000},
        ...b.movements.map((m: any, i: number) => ({
            stepKey: m.field, stepLabel: m.label, stepKind: 'MOVEMENT', amountMinor: (i + 1) * 1000 * m.sign,
        })),
        {stepKey: b.closing.field, stepLabel: b.closing.label, stepKind: 'CLOSING', amountMinor: 0},
    ];
    defs[defs.length - 1].amountMinor = defs.slice(0, -1).reduce((t, d) => t + (d.amountMinor as number), 0);
    return defs.map((d, i) => ({
        ...shared, ...d, stepOrder: i, claimKey: `${key}|${version}`, bridgeKey: key, version,
        scope: b.scope, authority: b.authority, expectedRowCount: defs.length,
        sourceDifferenceMinor: b.differenceField ? 0 : null,
        sourceStatus: b.statusField ? 'RECONCILED' : null,
    }));
}

test('all nine pinned schedules assert through the same renderer', () => {
    const keys = Object.keys(policy.bridges);
    assert.equal(keys.length, 9);
    for (const key of keys) {
        const bridge = parse(view(bridgeRows(key)));
        assert.equal(bridge.state, 'ASSERTED', `${key}: ${bridge.reason}`);
    }
});

test('reporting version must match the schedule\'s own scope', () => {
    // Fixed assets are NEXUS-UK; presenting them under the Group version is a
    // scope claim the source does not support.
    const asGroup = bridgeRows('GROSS_ASSETS').map(r => ({...r, version: 'RV-NEXUS-GROUP-2026-06@v1',
        claimKey: 'GROSS_ASSETS|RV-NEXUS-GROUP-2026-06@v1'}));
    assert.equal(parse(view(asGroup)).state, 'BLOCKED');
    const asEntity = bridgeRows('CASH').map(r => ({...r, version: 'RV-NEXUS-UK-2026-06@v1',
        claimKey: 'CASH|RV-NEXUS-UK-2026-06@v1'}));
    assert.equal(parse(view(asEntity)).state, 'BLOCKED');
    const wrongScope = bridgeRows('GROSS_ASSETS').map(r => ({...r, scope: 'NEXUS-GROUP'}));
    assert.equal(parse(view(wrongScope)).state, 'BLOCKED');
});

test('subtotals are checkpoints, never a second movement', () => {
    const steps: Step[] = [
        {key: 'o', label: 'Opening', order: 0, kind: 'OPENING', amount: 1000},
        {key: 'm', label: 'Movement', order: 1, kind: 'MOVEMENT', amount: -250},
        {key: 's', label: 'Subtotal', order: 2, kind: 'SUBTOTAL', amount: 750},
        {key: 'c', label: 'Closing', order: 3, kind: 'CLOSING', amount: 750},
    ];
    const tie = closure(steps, 0);
    assert.equal(tie.state, 'TIED');
    const bars = running(steps);
    assert.deepEqual(bars[2], {step: steps[2], from: 0, to: 750});
    assert.deepEqual(bars[3], {step: steps[3], from: 0, to: 750});
    assert.equal(ordered([steps[0], steps[0]]), null);
});

test('an anchorless or out of order schedule is unassessed, not zero', () => {
    const movement: Step = {key: 'm', label: 'M', order: 1, kind: 'MOVEMENT', amount: 5};
    assert.equal(closure([movement], 0).state, 'UNASSESSED');
    assert.equal(closure([
        {key: 'c', label: 'C', order: 0, kind: 'CLOSING', amount: 5}, movement,
        {key: 'o', label: 'O', order: 2, kind: 'OPENING', amount: 0},
    ], 0).state, 'UNASSESSED');
});

test('DOM renders text only and clears a stale bridge between updates', () => {
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
    assert.match(root.textContent!, /Cash rollforward/);
    assert.match(root.textContent!, /Arithmetic tie-out/);
    assert.equal(root.querySelectorAll('svg rect').length, 6);

    const scripted = rows({}, {0: {stepLabel: '<img src=x onerror=alert(1)>'}});
    visual.update({dataViews: [view(scripted)]} as any);
    assert.equal(root.querySelectorAll('img').length, 0);

    visual.update({dataViews: []} as any);
    assert.doesNotMatch(root.textContent!, /3,082,301\.85/);
});
