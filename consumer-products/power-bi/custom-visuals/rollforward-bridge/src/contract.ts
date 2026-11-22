import type powerbi from "powerbi-visuals-api";
import policy from "../policy.json";
import {readRow, missingText} from "../../shared/src/dataview";
import {exactMinor, formatMinor, formatSignedMinor} from "../../shared/src/money";
import {closure, coverage, ordered, running, STEP_KINDS, type Closure, type Coverage, type Step, type StepKind} from "../../shared/src/bridge";

export {formatMinor, formatSignedMinor, running};

export const requiredText = ["claimKey", "purpose", "authority", "deliveryRef", "deliveryDigest", "sourceDigest",
    "evidenceRef", "contextState", "bridgeKey", "stepKey", "stepLabel", "stepKind", "period", "scope", "version",
    "currency", "assertionPolicyRef"];

type BridgeSpec = {
    label: string; scope: string; authority: string; status: string; sourcePurpose: string;
    opening: {field: string; label: string};
    movements: {field: string; label: string; sign: number}[];
    closing: {field: string; label: string};
    differenceField: string | null; statusField: string | null; assertionNote: string;
};

/** The supplied source assertion, kept separate from the replayed arithmetic. */
export type SourceClaim = {status: string | null; difference: number | null; agrees: boolean | null};

export type Bridge = {
    state: "ASSERTED" | "BROKEN" | "BLOCKED";
    label: string;
    reason: string;
    note: string;
    steps: Step[];
    closure: Closure;
    coverage: Coverage;
    source: SourceClaim;
    fields: Record<string, string>;
};

const blocked = (reason: string, fields: Record<string, string> = {}, label = "Rollforward schedule"): Bridge => ({
    state: "BLOCKED", label, reason, note: "",
    steps: [], closure: {state: "UNASSESSED", reason}, coverage: {state: "INCOMPLETE", reason},
    source: {status: null, difference: null, agrees: null}, fields,
});

export function parse(view?: powerbi.DataView): Bridge {
    const rows = view?.table?.rows;
    if (!rows?.length) return blocked("Select one schedule and reporting period.");
    if (view!.metadata.segment) return blocked("Incomplete data was delivered. Narrow the selection.");
    const columns = view!.table!.columns;

    // Bind every row, then require one identical context across all of them.
    const bound = rows.map(row => readRow(columns, row));
    const duplicate = bound.find(b => b.duplicate)?.duplicate;
    if (duplicate) return blocked(`Multiple fields bound to ${duplicate}.`);
    const first = bound[0];
    const missing = missingText(first.fields, requiredText);
    if (missing) return blocked(`Missing ${missing}.`, first.fields);

    const context = ["claimKey", "bridgeKey", "period", "scope", "version", "currency", "authority", "purpose",
        "deliveryRef", "deliveryDigest", "sourceDigest", "assertionPolicyRef", "contextState"];
    for (const b of bound)
        for (const role of context)
            if (b.fields[role] !== first.fields[role])
                return blocked("The selection mixes more than one schedule, period or reporting version.", first.fields);

    const fields = first.fields;
    const spec = (policy.bridges as Record<string, BridgeSpec>)[fields.bridgeKey];
    if (!spec || fields.assertionPolicyRef !== policy.version)
        return blocked("No supported assertion policy for this schedule.", fields);
    const label = `${spec.label} rollforward`;
    if (fields.deliveryRef !== policy.deliveryRef || fields.deliveryDigest !== policy.deliveryDigest || fields.sourceDigest !== policy.sourceDigest)
        return blocked("Delivery or source identity differs from the supported policy.", fields, label);
    // Scope is per schedule: the fixed-asset marts are entity-scoped, and their
    // reporting version is the entity's, never the Group's.
    if (fields.scope !== spec.scope || fields.currency !== policy.currency)
        return blocked("Unsupported reporting scope or currency.", fields, label);
    if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(fields.period) || fields.period < policy.firstPeriod || fields.period > policy.lastPeriod
        || fields.version !== `RV-${spec.scope}-${fields.period}@v1`)
        return blocked("Unsupported reporting period or version.", fields, label);
    if (fields.claimKey !== `${fields.bridgeKey}|${fields.version}`)
        return blocked("Schedule identity does not match the claim key.", fields, label);
    if (fields.purpose !== policy.purpose)
        return blocked("This schedule is not asserted for the selected purpose.", fields, label);
    if (fields.authority !== spec.authority)
        return blocked("Source authority does not match the asserted schedule.", fields, label);
    if (fields.contextState !== "VALID")
        return blocked("The model reports incomplete or ambiguous context.", fields, label);

    // Steps. Labels and kinds must match the pinned equation, not arrive freely.
    const expected = new Map<string, {label: string; kind: StepKind}>([
        [spec.opening.field, {label: spec.opening.label, kind: "OPENING"}],
        [spec.closing.field, {label: spec.closing.label, kind: "CLOSING"}],
        ...spec.movements.map(m => [m.field, {label: m.label, kind: "MOVEMENT" as StepKind}] as const),
    ]);
    const steps: Step[] = [];
    for (const b of bound) {
        const {fields: f, values: v} = b;
        if (!STEP_KINDS.includes(f.stepKind)) return blocked(`Unknown step kind ${f.stepKind}.`, fields, label);
        const want = expected.get(f.stepKey);
        if (!want) return blocked(`Step ${f.stepKey} is not part of the pinned equation.`, fields, label);
        if (want.kind !== f.stepKind || want.label !== f.stepLabel)
            return blocked(`Step ${f.stepKey} does not match its pinned kind or label.`, fields, label);
        const amount = exactMinor(v.amountMinor);
        const order = exactMinor(v.stepOrder);
        if (amount === null || order === null)
            return blocked(`Step ${f.stepKey} has no exact integer amount and order.`, fields, label);
        steps.push({key: f.stepKey, label: f.stepLabel, order, kind: f.stepKind as StepKind, amount});
    }
    const sorted = ordered(steps);
    if (!sorted) return blocked("Duplicate step keys or ordering in the schedule.", fields, label);
    if (sorted.length !== expected.size)
        return blocked(`Received ${sorted.length} of ${expected.size} steps in the pinned equation.`, fields, label);

    const tolerance = exactMinor(first.values.toleranceMinor);
    if (tolerance === null || tolerance !== policy.toleranceMinor)
        return blocked("Supplied tolerance differs from the versioned policy.", fields, label);
    const tie = closure(sorted, tolerance);
    const cover = coverage(sorted.length, exactMinor(first.values.expectedRowCount) ?? -1,
        exactMinor(first.values.failedComponentCount) ?? -1, Boolean(view!.metadata.segment));

    // The supplied difference and status are a second, independent claim.
    const suppliedDifference = spec.differenceField ? exactMinor(first.values.sourceDifferenceMinor) : null;
    const suppliedStatus = spec.statusField ? (fields.sourceStatus ?? null) : null;
    const agrees = tie.state === "UNASSESSED" ? null
        : suppliedDifference !== null ? suppliedDifference === tie.difference
        : suppliedStatus !== null ? (suppliedStatus === "RECONCILED") === (tie.state === "TIED")
        : null;

    const state = tie.state === "TIED" && cover.state === "COMPLETE" && agrees !== false ? "ASSERTED"
        : tie.state === "UNASSESSED" ? "BLOCKED" : "BROKEN";
    const reason = state === "ASSERTED" ? "Arithmetic tie-out at zero tolerance"
        : tie.state === "UNASSESSED" ? tie.reason
        : tie.state === "BROKEN" ? `Bridge does not close by ${formatSignedMinor(tie.difference)}`
        : cover.state === "INCOMPLETE" ? cover.reason
        : "Replayed arithmetic disagrees with the supplied source assertion";
    return {state, label, reason, note: spec.assertionNote, steps: sorted, closure: tie, coverage: cover,
        source: {status: suppliedStatus, difference: suppliedDifference, agrees}, fields};
}
