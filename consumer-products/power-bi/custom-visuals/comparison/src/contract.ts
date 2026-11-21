import type powerbi from "powerbi-visuals-api";
import {missingText, readRow} from "../../shared/src/dataview";

const textRoles = ["mode", "key", "groupKey", "groupLabel", "label", "period", "scope", "currency",
    "direction", "baseRef", "middleRef", "endRef", "evidence", "adapterDigest"] as const;
type TextFields = Record<typeof textRoles[number], string>;
export type ComparisonRow = TextFields & {
    base: number; middle: number | null; end: number; firstDelta: number | null;
    secondDelta: number | null; netDelta: number; expected: number;
};

function minor(value: unknown): number {
    if (typeof value !== "number" || !Number.isSafeInteger(value)) throw new Error("An amount is missing or invalid.");
    return value;
}

export function parse(view: powerbi.DataView | undefined): ComparisonRow[] {
    const table = view?.table;
    if (!table?.rows?.length) throw new Error("No comparison rows are available for this selection.");
    if (view?.metadata.segment) throw new Error("Power BI supplied a partial comparison.");
    const rows = table.rows.map(row => {
        const {fields, values, duplicate} = readRow(table.columns, row);
        if (duplicate || missingText(fields, textRoles)) throw new Error("Bind each source and evidence field once.");
        const {mode, direction} = fields;
        const variance = mode === "variance";
        if ((!variance && mode !== "restatement") || fields.currency !== "GBP"
            || !/^sha256:[0-9a-f]{64}$/.test(fields.adapterDigest)
            || (variance ? !["higher", "lower"].includes(direction) : direction !== "neutral"))
            throw new Error("Unsupported comparison policy or currency.");
        const base = minor(values.base), end = minor(values.end), netDelta = minor(values.netDelta);
        const middle = variance ? minor(values.middle) : null;
        const firstDelta = variance ? minor(values.firstDelta) : null;
        const secondDelta = variance ? minor(values.secondDelta) : null;
        if (middle !== null && Math.min(base, middle, end) < 0)
            throw new Error("The account requires a positive-amount convention.");
        if (end - base !== netDelta || (middle !== null && (middle - base !== firstDelta || end - middle !== secondDelta)))
            throw new Error("The supplied movements do not reconcile to the anchors.");
        return {...fields as TextFields, base, middle, end, firstDelta, secondDelta, netDelta, expected: minor(values.expected)};
    });
    const first = rows[0];
    const mixed = rows.some(r => r.mode !== first.mode || r.period !== first.period || r.scope !== first.scope
        || r.adapterDigest !== first.adapterDigest || r.expected !== rows.length
        || (first.mode === "restatement" && (r.baseRef !== first.baseRef || r.endRef !== first.endRef
            || r.middleRef !== first.middleRef || r.groupKey !== first.groupKey)));
    if (mixed || new Set(rows.map(r => r.key)).size !== rows.length)
        throw new Error("The comparison has missing, duplicate or mixed rows.");
    const groups = new Map<string, ComparisonRow>();
    for (const row of rows) {
        const group = groups.get(row.groupKey);
        if (group && (group.groupLabel !== row.groupLabel || group.direction !== row.direction))
            throw new Error("The account has conflicting presentation policies.");
        groups.set(row.groupKey, row);
    }
    return rows;
}

export function money(amount: number, movement = false): string {
    const number = new Intl.NumberFormat("en-GB", {style: "currency", currency: "GBP"}).format(Math.abs(amount) / 100);
    return amount < 0 ? `(${number})` : movement && amount > 0 ? `+${number}` : number;
}

export function impact(delta: number, direction: string): string {
    if (delta === 0) return "On plan";
    return (delta > 0) === (direction === "higher") ? "Favourable" : "Adverse";
}

export function bridgeTotals(rows: ComparisonRow[]) {
    const total = (field: "base" | "middle" | "end" | "firstDelta" | "secondDelta" | "netDelta") =>
        rows.reduce((sum, row) => minor(sum + minor(row[field])), 0);
    const base = total("base"), middle = total("middle"), end = total("end");
    const firstDelta = total("firstDelta"), secondDelta = total("secondDelta"), netDelta = total("netDelta");
    if (middle - base !== firstDelta || end - middle !== secondDelta || end - base !== netDelta)
        throw new Error("Account totals fail to reconcile.");
    return {base, middle, end, firstDelta, secondDelta, netDelta};
}
