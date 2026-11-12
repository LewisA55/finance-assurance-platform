// Integer minor units throughout. Scale for display only. An amount that is not
// an exact safe integer is rejected rather than approximated into an assertion.

/** The value when it is an exact safe integer minor amount, else null. */
export function exactMinor(value: unknown): number | null {
    return typeof value === "number" && Number.isSafeInteger(value) ? value : null;
}

/** Sum that returns null if any term, or the running total, leaves safe range. */
export function sumExact(values: readonly number[]): number | null {
    let total = 0;
    for (const value of values) {
        if (!Number.isSafeInteger(value)) return null;
        total += value;
        if (!Number.isSafeInteger(total)) return null;
    }
    return total;
}

/** GBP from minor units; negatives in accounting brackets. */
export function formatMinor(value: number): string {
    const minor = BigInt(Math.abs(value));
    const text = new Intl.NumberFormat("en-GB").format(minor / 100n) + "." + (minor % 100n).toString().padStart(2, "0");
    return value < 0 ? `(GBP ${text})` : `GBP ${text}`;
}

/** Signed movement for bridge steps, where direction carries the meaning. */
export function formatSignedMinor(value: number): string {
    const minor = BigInt(Math.abs(value));
    const text = new Intl.NumberFormat("en-GB").format(minor / 100n) + "." + (minor % 100n).toString().padStart(2, "0");
    return `${value < 0 ? "-" : "+"}${text}`;
}
