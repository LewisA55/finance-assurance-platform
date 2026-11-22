import type powerbi from "powerbi-visuals-api";
import policy from "../policy.json";
import {readRow, missingText} from "../../shared/src/dataview";
import {exactMinor, formatMinor} from "../../shared/src/money";

export {formatMinor};

export const requiredText = ["claimKey","purpose","authority","deliveryRef","deliveryDigest","sourceDigest","evidenceRef","contextState","metricId","metricLabel","unit","period","scope","version","selectedPurpose","reliabilityStatus","reliabilityPurpose","eligibilityState","policyVersion","readinessStatus"];
export type Tile = { state: string; label: string; reason: string; value?: number; fields: Record<string,string> };
export function parse(view?: powerbi.DataView): Tile {
    const fail = (state: string, reason: string, fields: Record<string,string> = {}): Tile => ({state,reason,label:fields.metricLabel || "Governed metric",fields});
    if (!view?.table?.rows?.length) return fail("NO_DATA", "Select one metric and reporting period.");
    if (view.metadata.segment) return fail("INVALID_CONTEXT", "Incomplete data. Narrow the selection.");
    const {columns,rows} = view.table;
    if (rows.length !== 1) return fail("INVALID_CONTEXT", "Select exactly one metric, period and reporting version.");
    const {values,fields,duplicate} = readRow(columns, rows[0]);
    if (duplicate) return fail("INVALID_CONTEXT", `Multiple fields bound to ${duplicate}.`);
    const missing = missingText(fields, requiredText);
    if (missing) return fail("UNASSESSED", `Missing ${missing}.`,fields);
    const metric=policy.metrics[fields.metricId as keyof typeof policy.metrics];
    if (!metric || fields.policyVersion!==policy.version) return fail("UNASSESSED","No supported eligibility policy.",fields);
    if (fields.deliveryRef!==policy.deliveryRef || fields.deliveryDigest!==policy.deliveryDigest || fields.sourceDigest!==policy.sourceDigest)
        return fail("INVALID_CONTEXT","Delivery or source identity differs from the supported policy.",fields);
    if (fields.scope!=="NEXUS-GROUP" || fields.unit!=="GBP_MINOR" || !/^\d{4}-(0[1-9]|1[0-2])$/.test(fields.period) || fields.period<"2021-01" || fields.period>"2026-06" || fields.version!==`RV-NEXUS-GROUP-${fields.period}@v1`)
        return fail("INVALID_CONTEXT","Unsupported scope, unit or reporting version.",fields);
    if (fields.claimKey!==`${fields.metricId}|${fields.version}` || fields.metricLabel!==metric.label)
        return fail("INVALID_CONTEXT","Metric identity or label does not match the claim.",fields);
    if (fields.contextState!=="VALID") return fail("INVALID_CONTEXT",fields.failureReason || "The model reports incomplete or ambiguous context.",fields);
    if (fields.selectedPurpose!==policy.purpose || fields.purpose!==policy.purpose)
        return fail("WITHHELD","This metric is not assessed for the selected purpose.",fields);
    if (fields.authority!==metric.authority || fields.reliabilityStatus!==metric.status || fields.reliabilityPurpose!==metric.purpose)
        return fail("WITHHELD","Source authority or reliability does not meet this purpose's policy.",fields);
    if (fields.readinessStatus!=="READY") return fail("WITHHELD",fields.failureReason || "Required readiness assessment has not passed.",fields);
    if (fields.eligibilityState!=="ELIGIBLE") return fail(["WITHHELD","UNASSESSED","INVALID_CONTEXT","NO_DATA"].includes(fields.eligibilityState)?fields.eligibilityState:"UNASSESSED",fields.failureReason || "Eligibility was not established by the model.",fields);
    if (fields.failureReason) return fail("INVALID_CONTEXT","Eligible state conflicts with a failure reason.",fields);
    if (values.expectedRowCount!==1) return fail("INVALID_CONTEXT","The selection does not contain exactly one claim.",fields);
    const amount=exactMinor(values.displayValue);
    if (amount===null) return fail("UNASSESSED",`No exact eligible value was supplied (received ${typeof values.displayValue}).`,fields);
    return {state:"ELIGIBLE",label:fields.metricLabel,reason:"Eligible for CFO executive review",value:amount,fields};
}
