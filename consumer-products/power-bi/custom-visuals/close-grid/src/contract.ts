import type powerbi from "powerbi-visuals-api";
import policy from "../policy.json";
import {readRow, missingText} from "../../shared/src/dataview";
import {exactMinor} from "../../shared/src/money";

export const requiredText = ["claimKey", "purpose", "authority", "deliveryRef", "deliveryDigest", "sourceDigest",
    "evidenceRef", "contextState", "period", "scope", "scopeType", "version", "closeStatus", "closedAt",
    "gridPolicyRef", ...policy.dimensions.map(d => d.key)];

/** Marker states. Not applicable is a declared outcome, never a failure. */
export type MarkerState = "SATISFIED" | "NOT_APPLICABLE" | "ATTENTION" | "UNCLASSIFIED";
export type Marker = {key: string; initial: string; label: string; raw: string; state: MarkerState};
export type Evidence = {state: "COMPLETE" | "INCOMPLETE"; missing: string[]};
export type Cell = {
    period: string; scope: string; scopeType: string; version: string;
    closeStatus: string; closeLabel: string; closedAt: string;
    publicationState: string; markers: Marker[]; evidence: Evidence;
    events: {label: string; ref: string}[];
};
export type Check = {label: string; state: "TIED" | "BROKEN" | "UNASSESSED"; detail: string};
export type Grid = {
    state: "REVIEWED" | "INCOMPLETE" | "BLOCKED";
    label: string; reason: string;
    periods: string[]; scopes: {id: string; type: string}[];
    cells: Map<string, Cell>; checks: Check[]; tally: {label: string; counts: string}[];
    fields: Record<string, string>;
};

const blocked = (reason: string, fields: Record<string, string> = {}): Grid =>
    ({state: "BLOCKED", label: "Close governance", reason, periods: [], scopes: [],
      cells: new Map(), checks: [], tally: [], fields});

export const cellKey = (period: string, scope: string) => `${period}\u0000${scope}`;

/** Map a raw status through the per-dimension dictionary. Unknown stays visible. */
export function classify(dimension: string, raw: string): MarkerState {
    const table = (policy.dictionary as Record<string, Record<string, string>>)[dimension];
    const mapped = table?.[raw];
    return mapped === "SATISFIED" || mapped === "NOT_APPLICABLE" || mapped === "ATTENTION"
        ? mapped : "UNCLASSIFIED";
}

export function parse(view?: powerbi.DataView): Grid {
    const rows = view?.table?.rows;
    if (!rows?.length) return blocked("Select the reporting-version register.");
    if (view!.metadata.segment) return blocked("Incomplete data was delivered. Narrow the selection.");

    const bound = rows.map(row => readRow(view!.table!.columns, row));
    const duplicate = bound.find(b => b.duplicate)?.duplicate;
    if (duplicate) return blocked(`Multiple fields bound to ${duplicate}.`);
    const first = bound[0];
    const missing = missingText(first.fields, requiredText);
    if (missing) return blocked(`Missing ${missing}.`, first.fields);

    const constant = ["claimKey", "purpose", "authority", "deliveryRef", "deliveryDigest", "sourceDigest",
        "gridPolicyRef", "contextState"];
    for (const b of bound)
        for (const role of constant)
            if (b.fields[role] !== first.fields[role])
                return blocked("The selection mixes more than one register claim.", first.fields);

    const fields = first.fields;
    if (fields.gridPolicyRef !== policy.version)
        return blocked("No supported close-governance policy.", fields);
    if (fields.deliveryRef !== policy.deliveryRef || fields.deliveryDigest !== policy.deliveryDigest || fields.sourceDigest !== policy.sourceDigest)
        return blocked("Delivery or source identity differs from the supported policy.", fields);
    if (fields.contextState !== "VALID")
        return blocked("The model reports incomplete or ambiguous context.", fields);

    const cells = new Map<string, Cell>();
    const periods: string[] = [];
    const scopes: {id: string; type: string}[] = [];
    let unclassified = 0;
    let incomplete = 0;

    for (const b of bound) {
        const f = b.fields;
        const id = cellKey(f.period, f.scope);
        // A second version never silently replaces the first.
        if (cells.has(id))
            return blocked(`More than one reporting version for ${f.scope} ${f.period}. Add a version filter.`, fields);
        if (f.version !== `RV-${f.scope}-${f.period}@v1`)
            return blocked(`Version ${f.version} does not match its period and scope.`, fields);
        if (!periods.includes(f.period)) periods.push(f.period);
        const known = scopes.find(s => s.id === f.scope);
        if (!known) scopes.push({id: f.scope, type: f.scopeType});
        else if (known.type !== f.scopeType) return blocked(`Scope ${f.scope} has two scope types.`, fields);

        const markers = policy.dimensions.map(d => {
            const raw = f[d.key];
            const state = classify(d.key, raw);
            if (state === "UNCLASSIFIED") unclassified++;
            return {key: d.key, initial: d.initial, label: d.label, raw, state};
        });

        const events = [["Soft close", "softCloseEvent"], ["Hard close", "hardCloseEvent"],
            ["Publication", "publicationEvent"]].map(([label, key]) => ({label, ref: f[key] ?? ""}));
        const closeSpec = (policy.closeStates as Record<string, {label: string; requires: string[]}>)[f.closeStatus];
        const pubSpec = (policy.publicationStates as Record<string, {label: string; requires: string[]}>)[f.statementStatus];
        const required = [...(closeSpec?.requires ?? []), ...(pubSpec?.requires ?? [])];
        const missingEvents = required.filter(key => !f[key]?.trim());
        const evidence: Evidence = missingEvents.length
            ? {state: "INCOMPLETE", missing: missingEvents} : {state: "COMPLETE", missing: []};
        if (evidence.state === "INCOMPLETE") incomplete++;

        cells.set(id, {period: f.period, scope: f.scope, scopeType: f.scopeType, version: f.version,
            closeStatus: f.closeStatus, closeLabel: closeSpec?.label ?? f.closeStatus, closedAt: f.closedAt,
            publicationState: f.statementStatus, markers, evidence, events});
    }
    periods.sort().reverse();
    scopes.sort((a, b) => (a.type === b.type ? a.id.localeCompare(b.id)
        : a.type === "CONSOLIDATED_GROUP" ? -1 : 1));

    const expected = exactMinor(first.values.expectedRowCount);
    if (expected !== bound.length)
        return blocked("The delivered cell count does not match the expected count.", fields);
    const complete = periods.length * scopes.length === bound.length;

    // Counts per dimension, never a single percentage: a satisfied-marker tally
    // would not describe how far a close has progressed.
    const tally = policy.dimensions.map(d => {
        const states = [...cells.values()].map(c => c.markers.find(m => m.key === d.key)!.state);
        const counts = (["SATISFIED", "NOT_APPLICABLE", "ATTENTION", "UNCLASSIFIED"] as MarkerState[])
            .map(s => [s, states.filter(x => x === s).length] as const)
            .filter(([, n]) => n > 0)
            .map(([s, n]) => `${n} ${s.replaceAll("_", " ").toLowerCase()}`)
            .join(" · ");
        return {label: d.label, counts};
    });

    const checks: Check[] = [
        {label: "One reporting version per period and scope",
            state: complete ? "TIED" : "BROKEN",
            detail: complete ? `${periods.length} periods across ${scopes.length} scopes`
                : `${bound.length} cells for ${periods.length} periods and ${scopes.length} scopes`},
        {label: "Required lifecycle event references",
            state: incomplete ? "BROKEN" : "TIED",
            detail: incomplete ? `${incomplete} cell${incomplete === 1 ? "" : "s"} missing a required reference`
                : "Present wherever the lifecycle state requires them"},
        {label: "Status values in the dictionary",
            state: unclassified ? "UNASSESSED" : "TIED",
            detail: unclassified ? `${unclassified} unclassified marker${unclassified === 1 ? "" : "s"} shown unstyled`
                : "Every delivered value is classified"},
        {label: "Declared register size",
            state: bound.length === policy.expectedCellCount ? "TIED" : "BROKEN",
            detail: `${bound.length} of ${policy.expectedCellCount} declared rows`},
    ];

    const state = incomplete || !complete ? "INCOMPLETE" : "REVIEWED";
    const reason = !complete ? "The register does not cover every period and scope"
        : incomplete ? `${incomplete} cell${incomplete === 1 ? "" : "s"} lack a required event reference`
        : `${bound.length} reporting versions reviewed across ${scopes.length} scopes`;
    return {state, label: "Close governance", reason, periods, scopes, cells, checks, tally, fields};
}
