import type powerbi from "powerbi-visuals-api";
import policy from "../policy.json";
import {readRow, missingText} from "../../shared/src/dataview";
import {exactMinor} from "../../shared/src/money";

export const requiredText = ["claimKey", "purpose", "authority", "deliveryRef", "deliveryDigest", "sourceDigest",
    "evidenceRef", "contextState", "assertionId", "assertionLabel", "assertionType", "assertionSource",
    "operator", "unit", "publishedResult", "assertionPolicyRef"];

/** Presentation classifications. They do not substitute for control authority. */
export const TYPES = ["ARITHMETIC", "THRESHOLD", "INDEPENDENT_RECONCILIATION", "DELIVERY_PARITY", "SOURCE_BINDING"];
type SourceSpec = {label: string; expectedCount: number; grain: string; operatorDeclared: boolean; note: string};

export type Result = "PASS" | "FAIL" | "UNASSESSED";
export type Assertion = {
    id: string; label: string; type: string; operator: string; unit: string;
    actual: number | null; expected: number | null; sourceDifference: number | null; replayDifference: number | null;
    published: string; replay: Result; agrees: boolean | null; evidence: string; failureRef: string;
};
export type Check = {label: string; state: "TIED" | "BROKEN" | "UNASSESSED"; detail: string};
export type Panel = {
    state: "AGREED" | "DISAGREED" | "BLOCKED";
    label: string; reason: string; grain: string; note: string;
    assertions: Assertion[]; byType: {type: string; count: number}[]; checks: Check[];
    fields: Record<string, string>;
};

const blocked = (reason: string, fields: Record<string, string> = {}, label = "Assertion panel"): Panel =>
    ({state: "BLOCKED", label, reason, grain: "", note: "", assertions: [], byType: [], checks: [], fields});

/** Replay the comparison. A threshold is never failed by a nonzero difference. */
export function replay(operator: string, actual: number | null, expected: number | null): Result {
    if (actual === null || expected === null) return "UNASSESSED";
    if (operator === "EQUAL") return actual === expected ? "PASS" : "FAIL";
    if (operator === "GREATER_THAN_OR_EQUAL") return actual >= expected ? "PASS" : "FAIL";
    return "UNASSESSED";
}

export function parse(view?: powerbi.DataView): Panel {
    const rows = view?.table?.rows;
    if (!rows?.length) return blocked("Select one assertion source.");
    if (view!.metadata.segment) return blocked("Incomplete data was delivered. Narrow the selection.");

    const bound = rows.map(row => readRow(view!.table!.columns, row));
    const duplicate = bound.find(b => b.duplicate)?.duplicate;
    if (duplicate) return blocked(`Multiple fields bound to ${duplicate}.`);
    const first = bound[0];
    const missing = missingText(first.fields, requiredText);
    if (missing) return blocked(`Missing ${missing}.`, first.fields);

    const constant = ["claimKey", "assertionSource", "purpose", "authority", "deliveryRef", "deliveryDigest",
        "sourceDigest", "assertionPolicyRef", "contextState"];
    for (const b of bound)
        for (const role of constant)
            if (b.fields[role] !== first.fields[role])
                return blocked("The selection mixes more than one assertion source.", first.fields);

    const fields = first.fields;
    const spec = (policy.sources as Record<string, SourceSpec>)[fields.assertionSource];
    if (!spec || fields.assertionPolicyRef !== policy.version)
        return blocked("No supported assertion policy for this source.", fields);
    const label = spec.label;
    if (fields.deliveryRef !== policy.deliveryRef || fields.deliveryDigest !== policy.deliveryDigest || fields.sourceDigest !== policy.sourceDigest)
        return blocked("Delivery or source identity differs from the supported policy.", fields, label);
    if (fields.contextState !== "VALID")
        return blocked("The model reports incomplete or ambiguous context.", fields, label);
    // A delivery-wide control has no period. Binding one would relabel a
    // package result as a selected-month result.
    if (fields.period !== undefined || fields.scope !== undefined || fields.version !== undefined)
        return blocked("These controls are delivery-wide and must not carry a period, scope or version.", fields, label);

    const seen = new Set<string>();
    const assertions: Assertion[] = [];
    for (const b of bound) {
        const f = b.fields;
        if (seen.has(f.assertionId)) return blocked(`Duplicate assertion ${f.assertionId}.`, fields, label);
        seen.add(f.assertionId);
        if (!TYPES.includes(f.assertionType)) return blocked(`Unknown assertion type ${f.assertionType}.`, fields, label);
        // Two independent operand references are required to claim one.
        if (f.assertionType === "INDEPENDENT_RECONCILIATION" && !(f.actualEvidenceRef && f.expectedEvidenceRef))
            return blocked(`${f.assertionId} claims an independent reconciliation without two operand references.`, fields, label);
        const actual = exactMinor(b.values.actualValue);
        const expected = exactMinor(b.values.expectedValue);
        const supplied = b.values.sourceDifference === undefined || b.values.sourceDifference === null
            ? null : exactMinor(b.values.sourceDifference);
        const outcome = replay(f.operator, actual, expected);
        const replayDifference = actual === null || expected === null ? null : actual - expected;
        const published = f.publishedResult;
        const agrees = outcome === "UNASSESSED" ? null
            : published === "PASS" ? outcome === "PASS"
            : published === "FAIL" ? outcome === "FAIL"
            : null;
        assertions.push({id: f.assertionId, label: f.assertionLabel, type: f.assertionType, operator: f.operator,
            unit: f.unit, actual, expected, sourceDifference: supplied, replayDifference, published,
            replay: outcome, agrees, evidence: f.evidenceRef, failureRef: f.failureRef ?? ""});
    }
    assertions.sort((a, b) => a.id.localeCompare(b.id));

    const expectedCount = exactMinor(first.values.expectedRowCount);
    if (expectedCount !== assertions.length)
        return blocked("The delivered assertion count does not match the expected count.", fields, label);

    const byType = TYPES.map(type => ({type, count: assertions.filter(a => a.type === type).length}))
        .filter(t => t.count > 0 || t.type === "INDEPENDENT_RECONCILIATION");
    const disagreements = assertions.filter(a => a.agrees === false).length;
    const unassessed = assertions.filter(a => a.replay === "UNASSESSED").length;
    const mismatchedDiff = assertions.filter(a =>
        a.sourceDifference !== null && a.replayDifference !== null && a.sourceDifference !== a.replayDifference).length;

    const checks: Check[] = [
        {label: "Published and replayed results agree",
            state: disagreements ? "BROKEN" : unassessed ? "UNASSESSED" : "TIED",
            detail: disagreements ? `${disagreements} disagreement${disagreements === 1 ? "" : "s"}; neither result overwrites the other`
                : unassessed ? `${unassessed} could not be replayed` : `${assertions.length} replayed and agreed`},
        {label: "Supplied diagnostic differences match the replay",
            state: mismatchedDiff ? "BROKEN" : "TIED",
            detail: mismatchedDiff ? `${mismatchedDiff} differ from actual minus expected`
                : "Consistent where supplied"},
        {label: "Independent reconciliations",
            state: "UNASSESSED",
            detail: `0 of ${assertions.length}; two independent operand references are not supplied`},
        {label: "Declared count",
            state: assertions.length === spec.expectedCount ? "TIED" : "BROKEN",
            detail: `${assertions.length} of ${spec.expectedCount} declared for this source`},
    ];

    const state = disagreements ? "DISAGREED" : "AGREED";
    const reason = disagreements
        ? `${disagreements} published result${disagreements === 1 ? "" : "s"} disagree with the replay`
        : `${assertions.length} assertions replayed against their published result`;
    return {state, label, reason, grain: spec.grain, note: spec.note, assertions, byType, checks, fields};
}
