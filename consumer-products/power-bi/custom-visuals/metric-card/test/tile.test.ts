import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {parse, abbreviate, exact} from '../src/contract';
import {Visual} from '../src/visual';
import policy from '../policy.json';

type Row = Record<string, unknown>;

function tileRow(key = 'FP_LTM_REVENUE', patch: Row = {}): Row[] {
    const spec = (policy.tiles as Record<string, any>)[key];
    return [{
        tileKey: key, tileLabel: spec.label, caption: spec.caption, contextLine: spec.context,
        authority: spec.authority, unit: spec.unit, deliveryRef: policy.deliveryRef,
        tilePolicyRef: policy.version, value: 27650000, ...patch,
    }];
}

function view(data: Row[] = tileRow()) {
    const columns = Object.keys(data[0]).map(role => ({displayName: role, roles: {[role]: true}}));
    return {metadata: {columns}, table: {columns, rows: data.map(r => Object.values(r))}} as any;
}

test('the headline abbreviates and the exact figure is kept alongside', () => {
    const tile = parse(view());
    assert.equal(tile.state, 'PRESENTED');
    assert.equal(tile.display, '£27.65M');
    assert.equal(tile.exact, '£27,650,000.00');
    assert.equal(tile.label, 'LTM revenue');
});

test('scales and signs match the accepted page reading', () => {
    assert.equal(abbreviate(27650000, 'GBP'), '£27.65M');
    assert.equal(abbreviate(3082301.85, 'GBP'), '£3.08M');
    assert.equal(abbreviate(-1770000, 'GBP'), '(£1.77M)');
    assert.equal(abbreviate(487289.04, 'GBP'), '£487.29k');
    assert.equal(abbreviate(12.5, 'GBP'), '£12.50');
    assert.equal(exact(-93629822.89, 'GBP'), '(£93,629,822.89)');
    assert.equal(exact(957, 'COUNT'), '957');
    assert.equal(abbreviate(.9914, 'PCT'), '99.14%');
});

test('every registered tile round-trips', () => {
    const keys = Object.keys(policy.tiles);
    assert.equal(keys.length, 16);
    for (const key of keys) {
        const tile = parse(view(tileRow(key)));
        assert.equal(tile.state, 'PRESENTED', key);
        assert.equal(tile.authority, (policy.tiles as Record<string, any>)[key].authority);
    }
});

test('blank is unavailable and zero is a value', () => {
    const blank = parse(view(tileRow('CC_NET_DEBT', {value: null})));
    assert.equal(blank.state, 'BLOCKED');
    assert.equal(blank.value, null);
    assert.match(blank.reason, /No value/);
    // Context is still stated, so a missing figure is not a blank card.
    assert.equal(blank.label, 'Net debt');

    const zero = parse(view(tileRow('CC_NET_DEBT', {value: 0})));
    assert.equal(zero.state, 'PRESENTED');
    assert.equal(zero.value, 0);
    assert.equal(zero.display, '£0.00');
});

for (const [name, patch] of Object.entries({
    'relabelled tile': {tileLabel: 'Something else'},
    'rewritten context': {contextLine: 'All periods'},
    'overstated authority': {authority: 'INDEPENDENTLY_RECONCILED'},
    'changed caption': {caption: 'EXECUTIVE'},
    'changed unit': {unit: 'USD'},
    'wrong policy version': {tilePolicyRef: 'v99'},
    'wrong delivery': {deliveryRef: 'Q-FINANCE-C2@v2'},
    'unknown tile key': {tileKey: 'INVENTED'},
    'non-finite value': {value: Number.POSITIVE_INFINITY},
    'text value': {value: '27650000'},
})) test(`${name} never presents a figure`, () => {
    const tile = parse(view(tileRow('FP_LTM_REVENUE', patch)));
    assert.equal(tile.state, 'BLOCKED');
    assert.equal(tile.value, null);
});

test('empty, multi-row, segmented and duplicate role input fail closed', () => {
    assert.equal(parse().state, 'BLOCKED');
    assert.equal(parse(view([...tileRow(), ...tileRow('CC_NET_DEBT')])).state, 'BLOCKED');
    const segmented = view(); segmented.metadata.segment = {};
    assert.equal(parse(segmented).state, 'BLOCKED');
    const duplicated = view();
    duplicated.table.columns.push(duplicated.table.columns[0]);
    duplicated.table.rows.forEach((r: unknown[]) => r.push('duplicate'));
    assert.equal(parse(duplicated).state, 'BLOCKED');
});

test('DOM renders text only, carries the exact figure and clears between updates', () => {
    const dom = new JSDOM('<div id="root"></div>');
    const g: any = globalThis;
    g.document = dom.window.document;
    const root = dom.window.document.getElementById('root')!;
    const host: any = {
        colorPalette: {isHighContrast: false}, hostCapabilities: {allowInteractions: true},
        eventService: {renderingStarted: () => {}, renderingFinished: () => {}, renderingFailed: () => {}},
        tooltipService: {hide: () => {}},
    };
    const visual = new Visual({element: root, host} as any);
    visual.update({dataViews: [view()]} as any);
    assert.match(root.textContent!, /£27\.65M/);
    assert.match(root.querySelector('article')!.title, /GOVERNED ACTUALS/);
    assert.match(root.textContent!, /STATUTORY STATEMENT/);
    const card = root.querySelector('article') as HTMLElement;
    assert.match(card.title, /Exact: £27,650,000\.00/);
    assert.match(card.title, /makes no eligibility or assurance claim/);

    const scripted = tileRow('FP_LTM_REVENUE', {});
    visual.update({dataViews: [view(scripted)]} as any);
    assert.equal(root.querySelectorAll('img').length, 0);

    visual.update({dataViews: []} as any);
    assert.doesNotMatch(root.textContent!, /27\.65M/);
});
