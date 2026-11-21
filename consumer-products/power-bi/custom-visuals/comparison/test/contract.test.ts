import assert from "node:assert/strict";
import test from "node:test";
import type powerbi from "powerbi-visuals-api";
import {bridgeTotals, impact, parse} from "../src/contract";

const planning = {
    mode: "variance", key: "5000|DEP-A", groupKey: "5000", groupLabel: "Hosting",
    label: "Department A", period: "2026-06", scope: "Management planning extract", currency: "GBP",
    direction: "lower", base: 10500, middle: 10300, end: 11000, firstDelta: -200, secondDelta: 700,
    netDelta: 500, expected: 1, baseRef: "AOP@v1", middleRef: "SYNTHETIC-RF@v1", endRef: "SOURCE-ROW",
    evidence: "Previous actual and factor", adapterDigest: "sha256:" + "a".repeat(64),
};
const restatement = {...planning, mode: "restatement", direction: "neutral", groupKey: "RC-001",
    base: 0, end: 1000000, netDelta: 1000000, middle: null, firstDelta: null, secondDelta: null,
    baseRef: "RV-2026-06@v1", middleRef: "AE-C001-011 / RC-001", endRef: "RV-2026-06@v2"};

function view(...rows: Record<string, unknown>[]): powerbi.DataView {
    const keys = Object.keys(rows[0]);
    return {metadata: {}, table: {columns: keys.map(name => ({roles: {[name]: true}})),
        rows: rows.map(row => keys.map(key => row[key]))}} as powerbi.DataView;
}

test("keeps both stages and evaluates cost direction independently of sign", () => {
    const totals = bridgeTotals(parse(view(planning)));
    assert.deepEqual(totals, {base: 10500, middle: 10300, end: 11000, firstDelta: -200, secondDelta: 700, netDelta: 500});
    assert.equal(impact(totals.firstDelta, "lower"), "Favourable");
    assert.equal(impact(totals.secondDelta, "lower"), "Adverse");
    assert.equal(impact(totals.secondDelta, "higher"), "Favourable");
});

test("preserves a genuine zero in the original publication", () => {
    const [line] = parse(view(restatement));
    assert.equal(line.base, 0);
    assert.equal(line.netDelta, 1000000);
    assert.equal(line.middleRef, "AE-C001-011 / RC-001");
});

test("withholds incomplete and unreconciled comparisons", () => {
    assert.throws(() => parse(view({...planning, middle: null})), /missing or invalid/);
    assert.throws(() => parse(view({...planning, expected: 2})), /missing, duplicate or mixed/);
    assert.throws(() => parse(view({...restatement, netDelta: 999999})), /do not reconcile/);
    assert.throws(() => parse(view({...planning, expected: 2}, {...planning, expected: 2})), /duplicate/);
});
