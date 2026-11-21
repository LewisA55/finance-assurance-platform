import assert from "node:assert/strict";
import test from "node:test";
import type powerbi from "powerbi-visuals-api";
import {JSDOM} from "jsdom";
import {display, Visual} from "../src/visual";

test("preserves accounting currency, zero, missing, and percentages", () => {
    assert.equal(display(-2300, {displayName: "Revenue", format: "£#,##0.00"}), "(£2,300.00)");
    assert.equal(display(0, {displayName: "Count"}), "0");
    assert.equal(display(null, {displayName: "Count"}), "–");
    assert.equal(display(.9914, {displayName: "NRR", format: "0.00%"}), "99.14%");
});

test("opens the evidence context menu using the original table identity", () => {
    const {window} = new JSDOM("<main></main>");
    globalThis.document = window.document;
    const element = document.querySelector("main")!;
    const identity = {getKey: () => "row-0"};
    const seen: unknown[] = [];
    const host = {
        colorPalette: {isHighContrast: false}, hostCapabilities: {allowInteractions: true},
        createSelectionManager: () => ({showContextMenu: (id: unknown) => { seen.push(id); }}),
        createSelectionIdBuilder: () => ({
            withTable: (_: unknown, index: number) => {
                assert.equal(index, 0);
                return {createSelectionId: () => identity};
            },
        }),
    };
    const visual = new Visual({element, host} as unknown as powerbi.extensibility.visual.VisualConstructorOptions);
    const columns = [{displayName: "Reporting version", queryName: "Reporting Version.Reporting Version Ref"},
        {displayName: "Close status"}];
    visual.update({viewport: {width: 500, height: 250},
        dataViews: [{metadata: {columns}, table: {columns, rows: [["RV-2026-06@v1", "HARD_CLOSED"]]}}],
    } as powerbi.extensibility.visual.VisualUpdateOptions);
    element.querySelector("button")!.click();
    assert.deepEqual(seen, [identity]);
    assert.equal(element.querySelector(".status")?.textContent, "Hard closed");
});
