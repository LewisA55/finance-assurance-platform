import type powerbi from "powerbi-visuals-api";
import policy from "../policy.json";
import {readRow, missingText} from "../../shared/src/dataview";
import {exactMinor, formatMinor, sumExact} from "../../shared/src/money";

export {formatMinor};

export const requiredText = ["claimKey", "purpose", "authority", "deliveryRef", "deliveryDigest", "sourceDigest",
    "evidenceRef", "contextState", "statementClass", "rowKey", "rowKind", "ruleStyle", "columnKey", "columnLabel",
    "period", "scope", "version", "currency", "signConvention", "presentationPolicyRef", "lineEligibility"];

export type RowKind = "HEADER" | "LINE" | "DERIVED_SUBTOTAL" | "SUPPLIED_TOTAL" | "MEMO" | "SPACER";
export type RuleStyle = "none" | "single" | "double";
/** Kinds that carry a monetary value. A structural row has no amount at all. */
const VALUED: readonly RowKind[] = ["LINE", "DERIVED_SUBTOTAL", "SUPPLIED_TOTAL", "MEMO"];

type RegistryRow = {kind: string; key: string; label: string; indent: number; rule: string; formula?: string[]};
type StatementSpec = {
    label: string; signConvention: string; sourceLineCount: number; note: string;
    reconciliation: {label: string; expect: string; formula: string[]};
    rows: RegistryRow[];
};

export type Cell = {amount: number | null; eligibility: string; failureReason: string};
export type Line = {key: string; label: string; order: number; kind: RowKind; indent: number; rule: RuleStyle; cells: Cell[]};
export type Column = {key: string; label: string; order: number; period: string; version: string};
export type Check = {label: string; state: "TIED" | "BROKEN" | "UNASSESSED"; detail: string};

export type Statement = {
    state: "PRESENTED" | "BROKEN" | "BLOCKED";
    label: string; reason: string; note: string;
    columns: Column[]; lines: Line[]; checks: Check[];
    fields: Record<string, string>;
};

const blocked = (reason: string, fields: Record<string, string> = {}, label = "Financial statement"): Statement =>
    ({state: "BLOCKED", label, reason, note: "", columns: [], lines: [], checks: [], fields});

export function parse(view?: powerbi.DataView): Statement {
    const rows = view?.table?.rows;
    if (!rows?.length) return blocked("Select one statement and reporting period.");
    if (view!.metadata.segment) return blocked("Incomplete data was delivered. Narrow the selection.");

    const bound = rows.map(row => readRow(view!.table!.columns, row));
    const duplicate = bound.find(b => b.duplicate)?.duplicate;
    if (duplicate) return blocked(`Multiple fields bound to ${duplicate}.`);
    const first = bound[0];
    const missing = missingText(first.fields, requiredText);
    if (missing) return blocked(`Missing ${missing}.`, first.fields);

    // Period and version belong to the column, so they are deliberately not
    // required to be constant across the cell set.
    const constant = ["claimKey", "statementClass", "scope", "currency", "purpose", "authority",
        "deliveryRef", "deliveryDigest", "sourceDigest", "presentationPolicyRef", "contextState", "signConvention"];
    for (const b of bound)
        for (const role of constant)
            if (b.fields[role] !== first.fields[role])
                return blocked("The selection mixes more than one statement, scope or layout version.", first.fields);

    const fields = first.fields;
    const spec = (policy.statements as Record<string, StatementSpec>)[fields.statementClass];
    if (!spec || fields.presentationPolicyRef !== policy.version)
        return blocked("No supported presentation policy for this statement.", fields);
    const label = spec.label;
    if (fields.deliveryRef !== policy.deliveryRef || fields.deliveryDigest !== policy.deliveryDigest || fields.sourceDigest !== policy.sourceDigest)
        return blocked("Delivery or source identity differs from the supported policy.", fields, label);
    if (fields.scope !== policy.scope || fields.currency !== policy.currency || fields.signConvention !== spec.signConvention)
        return blocked("Unsupported scope, currency or sign convention.", fields, label);
    if (fields.contextState !== "VALID")
        return blocked("The model reports incomplete or ambiguous context.", fields, label);

    // Columns, in declared order, each with its own period and reporting version.
    const columns: Column[] = [];
    for (const b of bound) {
        const order = exactMinor(b.values.columnOrder);
        if (order === null) return blocked("A column has no exact integer order.", fields, label);
        const seen = columns.find(c => c.key === b.fields.columnKey);
        if (!seen) {
            if (columns.some(c => c.order === order)) return blocked("Two columns share one order.", fields, label);
            columns.push({key: b.fields.columnKey, label: b.fields.columnLabel, order,
                period: b.fields.period, version: b.fields.version});
        } else if (seen.order !== order || seen.label !== b.fields.columnLabel
            || seen.period !== b.fields.period || seen.version !== b.fields.version) {
            return blocked(`Column ${b.fields.columnKey} has inconsistent identity.`, fields, label);
        }
    }
    columns.sort((a, b) => a.order - b.order);
    for (const column of columns)
        if (column.version !== `RV-NEXUS-GROUP-${column.period}@v1` || column.key !== column.period
            || !/^\d{4}-(0[1-9]|1[0-2])$/.test(column.period)
            || column.period < policy.firstPeriod || column.period > policy.lastPeriod)
            return blocked(`Column ${column.key} has an unsupported period or reporting version.`, fields, label);

    // One cell per registry row per column, matching the pinned scaffold.
    const cellAt = new Map<string, typeof bound[number]>();
    for (const b of bound) {
        const id = `${b.fields.rowKey}\u0000${b.fields.columnKey}`;
        if (cellAt.has(id)) return blocked(`Duplicate cell for ${b.fields.rowKey}.`, fields, label);
        cellAt.set(id, b);
    }
    if (bound.length !== spec.rows.length * columns.length)
        return blocked(`Received ${bound.length} of ${spec.rows.length * columns.length} expected cells.`, fields, label);
    const expected = exactMinor(first.values.expectedRowCount);
    if (expected !== bound.length)
        return blocked("The delivered cell count does not match the expected count.", fields, label);

    const lines: Line[] = [];
    for (let order = 0; order < spec.rows.length; order++) {
        const registry = spec.rows[order];
        const cells: Cell[] = [];
        for (const column of columns) {
            const b = cellAt.get(`${registry.key}\u0000${column.key}`);
            if (!b) return blocked(`Missing cell for ${registry.key} in ${column.label}.`, fields, label);
            if (b.fields.rowKind !== registry.kind || (b.fields.rowLabel ?? "") !== registry.label
                || b.fields.ruleStyle !== registry.rule
                || exactMinor(b.values.indentLevel) !== registry.indent
                || exactMinor(b.values.rowOrder) !== order)
                return blocked(`Row ${registry.key} does not match the pinned presentation scaffold.`, fields, label);
            const valued = VALUED.includes(registry.kind as RowKind);
            const amount = exactMinor(b.values.amountMinor);
            if (!valued && amount !== null)
                return blocked(`Structural row ${registry.key} carries an amount.`, fields, label);
            if (valued && amount === null && b.fields.lineEligibility === "ELIGIBLE")
                return blocked(`Row ${registry.key} is eligible but supplied no exact amount.`, fields, label);
            cells.push({amount, eligibility: b.fields.lineEligibility,
                failureReason: b.fields.lineFailureReason ?? ""});
        }
        lines.push({key: registry.key, label: registry.label, order, kind: registry.kind as RowKind,
            indent: registry.indent, rule: registry.rule as RuleStyle, cells});
    }

    const checks = verify(spec, lines, columns);
    const broken = checks.find(c => c.state === "BROKEN");
    const blockedCell = lines.some(l => l.cells.some(c => c.eligibility !== "ELIGIBLE" && VALUED.includes(l.kind)));
    const state = broken ? "BROKEN" : "PRESENTED";
    const reason = broken ? broken.detail
        : blockedCell ? "Presented with one or more gated lines"
        : `Presented and cross-checked for ${columns.length === 1 ? "one period" : `${columns.length} periods`}`;
    return {state, label, reason, note: spec.note, columns, lines, checks, fields};
}

/**
 * Replay the registered arithmetic rather than trusting the model's own
 * subtotals, then the statement's declared reconciliation. A derived subtotal
 * is checked per column, so one bad period cannot hide behind another.
 */
function verify(spec: StatementSpec, lines: Line[], columns: Column[]): Check[] {
    const at = (key: string, i: number): number | null => lines.find(l => l.key === key)?.cells[i]?.amount ?? null;
    const checks: Check[] = [];

    const derived = spec.rows.filter(r => r.kind === "DERIVED_SUBTOTAL");
    if (derived.length) {
        let failures = 0;
        let unassessed = 0;
        for (let i = 0; i < columns.length; i++)
            for (const row of derived) {
                const parts = (row.formula ?? []).map(f => at(f, i));
                const supplied = at(row.key, i);
                if (parts.some(p => p === null) || supplied === null) { unassessed++; continue; }
                const total = sumExact(parts as number[]);
                if (total === null || total !== supplied) failures++;
            }
        checks.push({label: "Derived subtotals replayed",
            state: failures ? "BROKEN" : unassessed ? "UNASSESSED" : "TIED",
            detail: failures ? `${failures} derived subtotal${failures === 1 ? "" : "s"} did not replay`
                : unassessed ? "A derived subtotal had no exact operands"
                : `${derived.length * columns.length} replayed exactly`});
    }

    const rec = spec.reconciliation;
    let recFailures = 0;
    let recUnassessed = 0;
    let worst = 0;
    for (let i = 0; i < columns.length; i++) {
        const parts = rec.formula.map(f => at(f, i));
        const target = at(rec.expect, i);
        if (parts.some(p => p === null) || target === null) { recUnassessed++; continue; }
        const total = sumExact(parts as number[]);
        if (total === null) { recUnassessed++; continue; }
        const difference = total - target;
        if (difference !== 0) { recFailures++; worst = Math.abs(difference) > Math.abs(worst) ? difference : worst; }
    }
    checks.push({label: rec.label,
        state: recFailures ? "BROKEN" : recUnassessed ? "UNASSESSED" : "TIED",
        detail: recFailures ? `Out by ${formatMinor(worst)}`
            : recUnassessed ? "Operands were not all available"
            : "Exact in every presented period"});

    // Supplied totals overlap their components, so the renderer states that it
    // never sums the displayed rows rather than quietly doing it.
    const supplied = spec.rows.filter(r => r.kind === "SUPPLIED_TOTAL").length;
    checks.push({label: "Supplied totals preserved", state: "TIED",
        detail: `${supplied} source total${supplied === 1 ? "" : "s"} shown as delivered, never recomputed`});
    return checks;
}
