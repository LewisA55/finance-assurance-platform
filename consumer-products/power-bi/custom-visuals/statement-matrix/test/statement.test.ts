import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {parse} from '../src/contract';
import {Visual} from '../src/visual';
import policy from '../policy.json';

type Row = Record<string, unknown>;
const COLUMNS = [{key: '2026-06', label: 'Jun 2026', order: 1}, {key: '2026-05', label: 'May 2026', order: 2}];

// Real June 2026 Group figures, in minor units.
const AMOUNTS: Record<string, Record<string, number>> = {
    INCOME_STATEMENT: {
        subscription_revenue: 228800965, services_revenue: 0, cost_of_revenue: -15526594,
        research_and_development: -97899341, sales_and_marketing: -141227805,
        general_and_administrative: -151467824, depreciation_and_amortisation: -26436532,
        interest_expense: -2858118, income_tax_expense: 14971531, net_income: -191643718,
    },
    BALANCE_SHEET: {
        cash: 308230185, accounts_receivable: 0, intercompany_receivables: 0, prepayments: 0, inventory: 0,
        deferred_tax_asset: 0, property_plant_equipment: 0, accumulated_depreciation: 0, intangible_assets: 0,
        accumulated_amortisation: 0, goodwill: 0, right_of_use_assets: 0,
        accumulated_right_of_use_depreciation: 0, total_assets: 308230185,
        accounts_payable: 0, intercompany_payables: 0, deferred_revenue: 0, accrued_expenses: 0,
        unapplied_cash: 0, tax_payable: 0, long_term_debt: 0, lease_liabilities: 0, total_liabilities: 108230185,
        share_capital: 0, retained_earnings: 0, total_equity: 200000000,
        total_liabilities_and_equity: 308230185,
    },
    CASH_FLOW: {
        operating_cash_flow: -147938343, investing_cash_flow: 0, financing_cash_flow: -79779524,
        net_change_in_cash: -227717867, closing_cash: 308230185, net_income: -191643718,
    },
};

function cells(cls = 'INCOME_STATEMENT', columns = COLUMNS, patch: Row = {},
               perRow: (key: string, column: string) => Row = () => ({})): Row[] {
    const spec = (policy.statements as Record<string, any>)[cls];
    const values: Record<string, number> = {...AMOUNTS[cls]};
    for (const r of spec.rows)
        if (r.kind === 'DERIVED_SUBTOTAL')
            values[r.key] = r.formula.reduce((t: number, f: string) => t + values[f], 0);
    const out: Row[] = [];
    for (const column of columns)
        spec.rows.forEach((r: any, i: number) => {
            const valued = ['LINE', 'SUPPLIED_TOTAL', 'MEMO', 'DERIVED_SUBTOTAL'].includes(r.kind);
            out.push({
                claimKey: `${cls}|2026-06|${policy.scope}`, statementClass: cls,
                rowKey: r.key, rowLabel: r.label, rowOrder: i, rowKind: r.kind,
                indentLevel: r.indent, ruleStyle: r.rule,
                columnKey: column.key, columnLabel: column.label, columnOrder: column.order,
                amountMinor: valued ? values[r.key] : null,
                period: column.key, scope: policy.scope, version: `RV-NEXUS-GROUP-${column.key}@v1`,
                currency: policy.currency, signConvention: spec.signConvention,
                presentationPolicyRef: policy.version,
                lineEligibility: valued ? 'ELIGIBLE' : 'NOT_APPLICABLE', lineFailureReason: null,
                purpose: policy.purpose, authority: policy.authority, deliveryRef: policy.deliveryRef,
                deliveryDigest: policy.deliveryDigest, sourceDigest: policy.sourceDigest,
                evidenceRef: `${policy.table} / ${cls}`, evidenceDigest: 'sha256:tb', contextState: 'VALID',
                expectedRowCount: spec.rows.length * columns.length,
                ...patch, ...perRow(r.key, column.key),
            });
        });
    return out;
}

function view(data: Row[] = cells()) {
    const columns = Object.keys(data[0]).map(role => ({displayName: role, roles: {[role]: true}}));
    return {metadata: {columns}, table: {columns, rows: data.map(r => Object.values(r))}} as any;
}

test('all three statements present and cross-check', () => {
    for (const cls of Object.keys(policy.statements)) {
        const s = parse(view(cells(cls)));
        assert.equal(s.state, 'PRESENTED', `${cls}: ${s.reason}`);
        assert.ok(s.checks.every(c => c.state === 'TIED'), `${cls}: ${JSON.stringify(s.checks)}`);
        assert.equal(s.columns.length, 2);
    }
});

test('scaffold order, indentation and rules survive the round trip', () => {
    const s = parse(view(cells('INCOME_STATEMENT')));
    assert.deepEqual(s.lines.map(l => l.key).slice(0, 4),
        ['h_revenue', 'subscription_revenue', 'services_revenue', 'd_total_revenue']);
    assert.equal(s.lines[0].kind, 'HEADER');
    assert.equal(s.lines[1].indent, 1);
    assert.equal(s.lines.at(-1)!.rule, 'double');
    // Supplied net income is shown as delivered, not recomputed.
    assert.equal(s.lines.at(-1)!.cells[0].amount, -191643718);
});

test('a derived subtotal that does not replay is reported', () => {
    const s = parse(view(cells('INCOME_STATEMENT', COLUMNS, {},
        (key) => key === 'd_gross_profit' ? {amountMinor: 1} : {})));
    assert.equal(s.state, 'BROKEN');
    assert.ok(s.checks.some(c => c.label === 'Derived subtotals replayed' && c.state === 'BROKEN'));
});

test('a reconciliation break is reported against the supplied total', () => {
    const s = parse(view(cells('INCOME_STATEMENT', COLUMNS, {},
        (key) => key === 'net_income' ? {amountMinor: -191643719} : {})));
    assert.equal(s.state, 'BROKEN');
    assert.ok(s.checks.some(c => c.state === 'BROKEN' && c.detail.includes('0.01')));
});

test('the cash flow summary keeps net income out of the movement total', () => {
    const s = parse(view(cells('CASH_FLOW')));
    assert.equal(s.state, 'PRESENTED');
    const memo = s.lines.find(l => l.key === 'net_income')!;
    assert.equal(memo.kind, 'MEMO');
    assert.ok(s.note.includes('not a complete statutory cash-flow statement'));
});

test('one supported period presents a single column', () => {
    const s = parse(view(cells('INCOME_STATEMENT', [{key: '2021-01', label: 'Jan 2021', order: 1}])));
    assert.equal(s.state, 'PRESENTED');
    assert.equal(s.columns.length, 1);
});

test('a gated line withholds its amount without blocking the statement', () => {
    const s = parse(view(cells('INCOME_STATEMENT', COLUMNS, {},
        (key) => key === 'interest_expense'
            ? {lineEligibility: 'BLOCKED', amountMinor: null, lineFailureReason: 'Not assessed'} : {})));
    assert.equal(s.state, 'PRESENTED');
    const gated = s.lines.find(l => l.key === 'interest_expense')!;
    assert.equal(gated.cells[0].amount, null);
    assert.equal(gated.cells[0].eligibility, 'BLOCKED');
});

for (const [name, data] of Object.entries({
    'structural row with an amount': cells('INCOME_STATEMENT', COLUMNS, {},
        (key) => key === 'h_revenue' ? {amountMinor: 5} : {}),
    'relabelled row': cells('INCOME_STATEMENT', COLUMNS, {}, (key) => key === 'cost_of_revenue' ? {rowLabel: 'Costs'} : {}),
    'reordered row': cells('INCOME_STATEMENT', COLUMNS, {}, (key) => key === 'cost_of_revenue' ? {rowOrder: 99} : {}),
    'changed indent': cells('INCOME_STATEMENT', COLUMNS, {}, (key) => key === 'cost_of_revenue' ? {indentLevel: 3} : {}),
    'changed rule': cells('INCOME_STATEMENT', COLUMNS, {}, (key) => key === 'net_income' ? {ruleStyle: 'none'} : {}),
    'changed kind': cells('INCOME_STATEMENT', COLUMNS, {}, (key) => key === 'net_income' ? {rowKind: 'LINE'} : {}),
    'eligible with no amount': cells('INCOME_STATEMENT', COLUMNS, {},
        (key) => key === 'cost_of_revenue' ? {amountMinor: null} : {}),
    'fractional amount': cells('INCOME_STATEMENT', COLUMNS, {},
        (key) => key === 'cost_of_revenue' ? {amountMinor: 1.5} : {}),
    'wrong policy version': cells('INCOME_STATEMENT', COLUMNS, {presentationPolicyRef: 'v99'}),
    'wrong delivery digest': cells('INCOME_STATEMENT', COLUMNS, {deliveryDigest: 'sha256:wrong'}),
    'wrong source digest': cells('INCOME_STATEMENT', COLUMNS, {sourceDigest: 'sha256:wrong'}),
    'wrong scope': cells('INCOME_STATEMENT', COLUMNS, {scope: 'NEXUS-UK'}),
    'wrong sign convention': cells('INCOME_STATEMENT', COLUMNS, {signConvention: 'POSITIVE_PRESENTED_BALANCE'}),
    'ambiguous context': cells('INCOME_STATEMENT', COLUMNS, {contextState: 'AMBIGUOUS'}),
    'mixed statements': cells('INCOME_STATEMENT', COLUMNS, {},
        (key) => key === 'net_income' ? {statementClass: 'CASH_FLOW'} : {}),
    'column version mismatch': cells('INCOME_STATEMENT', COLUMNS, {},
        (_k, column) => column === '2026-05' ? {version: 'RV-NEXUS-GROUP-2026-05@v2'} : {}),
    'columns sharing an order': cells('INCOME_STATEMENT',
        [{key: '2026-06', label: 'Jun 2026', order: 1}, {key: '2026-05', label: 'May 2026', order: 1}]),
    'cell count mismatch': cells('INCOME_STATEMENT', COLUMNS, {expectedRowCount: 99}),
    'missing cell': cells('INCOME_STATEMENT').slice(1),
})) test(`${name} never presents an affirmative statement`, () => {
    assert.notEqual(parse(view(data)).state, 'PRESENTED');
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

test('DOM renders a finance table, brackets negatives and clears between updates', () => {
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
    visual.update({dataViews: [view()], viewport: {width: 600, height: 760}} as any);
    assert.equal(root.querySelectorAll('table thead th').length, 3);
    assert.equal(root.querySelectorAll('table tbody tr').length, policy.statements.INCOME_STATEMENT.rows.length);
    assert.match(root.textContent!, /\(1,514,678\.24\)/);
    assert.match(root.textContent!, /Supplied totals preserved/);

    const scripted = cells('INCOME_STATEMENT', COLUMNS, {},
        (key) => key === 'h_revenue' ? {rowLabel: '<img src=x onerror=alert(1)>'} : {});
    visual.update({dataViews: [view(scripted)], viewport: {width: 600, height: 760}} as any);
    assert.equal(root.querySelectorAll('img').length, 0);

    visual.update({dataViews: []} as any);
    assert.doesNotMatch(root.textContent!, /1,916,437\.18/);
});
