// Shared rollforward assertion core, specification section 5.
//
// The renderer replays the component equation itself. A supplied status is a
// separate claim and never stands in for closure. Offsetting breaks stay
// visible because components are counted, not just netted. Subtotals are
// running checkpoints and are never added as another movement.

import {sumExact} from "./money";

export type StepKind = "OPENING" | "MOVEMENT" | "SUBTOTAL" | "CLOSING";
export const STEP_KINDS: readonly string[] = ["OPENING", "MOVEMENT", "SUBTOTAL", "CLOSING"];

export type Step = {key: string; label: string; order: number; kind: StepKind; amount: number};

export type Closure =
    | {state: "TIED" | "BROKEN"; expected: number; supplied: number; difference: number}
    | {state: "UNASSESSED"; reason: string};

export type Coverage = {state: "COMPLETE"} | {state: "INCOMPLETE"; reason: string};

/** Sort by declared order. Duplicate orders or keys are an invalid schedule. */
export function ordered(steps: readonly Step[]): Step[] | null {
    const orders = new Set<number>();
    const keys = new Set<string>();
    for (const step of steps) {
        if (!Number.isSafeInteger(step.order) || orders.has(step.order) || keys.has(step.key)) return null;
        orders.add(step.order);
        keys.add(step.key);
    }
    return [...steps].sort((a, b) => a.order - b.order);
}

/** Replay opening + movements and compare with the supplied closing anchor. */
export function closure(steps: readonly Step[], tolerance: number): Closure {
    const anchors = (kind: StepKind) => steps.filter(step => step.kind === kind);
    const opening = anchors("OPENING");
    const closing = anchors("CLOSING");
    const movements = anchors("MOVEMENT");
    if (opening.length !== 1 || closing.length !== 1)
        return {state: "UNASSESSED", reason: "A bridge needs exactly one opening and one closing anchor."};
    if (!movements.length)
        return {state: "UNASSESSED", reason: "No movements were supplied between the anchors."};
    if (opening[0].order >= closing[0].order)
        return {state: "UNASSESSED", reason: "The closing anchor does not follow the opening anchor."};
    if (!Number.isSafeInteger(tolerance) || tolerance < 0)
        return {state: "UNASSESSED", reason: "The supplied tolerance is not an exact non-negative integer."};
    const expected = sumExact([opening[0].amount, ...movements.map(step => step.amount)]);
    if (expected === null)
        return {state: "UNASSESSED", reason: "An amount or running total left the exact integer range."};
    const supplied = closing[0].amount;
    const difference = expected - supplied;
    if (!Number.isSafeInteger(difference))
        return {state: "UNASSESSED", reason: "The difference left the exact integer range."};
    return {state: Math.abs(difference) <= tolerance ? "TIED" : "BROKEN", expected, supplied, difference};
}

/**
 * Component coverage. A net tie-out is not evidence on its own: an aggregated
 * schedule must also report how many of its components failed, so two
 * offsetting errors cannot present as a clean bridge.
 */
export function coverage(delivered: number, expected: number, failedComponents: number, segmented: boolean): Coverage {
    if (segmented) return {state: "INCOMPLETE", reason: "The host delivered a partial segment. Narrow the selection."};
    if (!Number.isSafeInteger(expected) || expected < 1)
        return {state: "INCOMPLETE", reason: "No exact expected step count was supplied."};
    if (delivered !== expected)
        return {state: "INCOMPLETE", reason: `Received ${delivered} of ${expected} expected steps.`};
    if (!Number.isSafeInteger(failedComponents) || failedComponents < 0)
        return {state: "INCOMPLETE", reason: "No exact failed-component count was supplied."};
    if (failedComponents > 0)
        return {state: "INCOMPLETE", reason: `${failedComponents} component schedule${failedComponents === 1 ? "" : "s"} did not close.`};
    return {state: "COMPLETE"};
}

/** Running balance per step, for waterfall geometry. Anchors are absolute. */
export function running(steps: readonly Step[]): {step: Step; from: number; to: number}[] {
    let balance = 0;
    return steps.map(step => {
        if (step.kind === "OPENING" || step.kind === "CLOSING") {
            balance = step.amount;
            return {step, from: 0, to: step.amount};
        }
        if (step.kind === "SUBTOTAL") return {step, from: 0, to: balance};
        const from = balance;
        balance += step.amount;
        return {step, from, to: balance};
    });
}
