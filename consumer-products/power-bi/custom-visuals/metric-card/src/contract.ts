import type powerbi from "powerbi-visuals-api";
import policy from "../policy.json";
import {readRow, missingText} from "../../shared/src/dataview";

export const requiredText = ["tileKey", "tileLabel", "caption", "contextLine", "authority", "unit",
    "deliveryRef", "tilePolicyRef"];

type TileSpec = {label: string; caption: string; context: string; authority: string; unit: string};

export type Tile = {
    state: "PRESENTED" | "BLOCKED";
    key: string; label: string; caption: string; context: string; authority: string; unit: string;
    value: number | null; display: string; exact: string; reason: string;
};

const blocked = (reason: string): Tile => ({
    state: "BLOCKED", key: "", label: "Measure", caption: "NEXUS", context: "", authority: "",
    unit: "", value: null, display: "–", exact: "", reason,
});

/** Exact amount, full precision, negatives in accounting brackets. */
export function exact(value: number, unit: string): string {
    if (unit === "COUNT") return new Intl.NumberFormat("en-GB", {maximumFractionDigits: 0}).format(value);
    if (unit === "PCT") return new Intl.NumberFormat("en-GB", {
        style: "percent", minimumFractionDigits: 2, maximumFractionDigits: 2,
    }).format(value);
    const text = new Intl.NumberFormat("en-GB", {minimumFractionDigits: 2, maximumFractionDigits: 2})
        .format(Math.abs(value));
    const symbol = unit === "GBP" ? "£" : "";
    return value < 0 ? `(${symbol}${text})` : `${symbol}${text}`;
}

/**
 * Headline scale. The native card abbreviated at display time, so the tile
 * keeps that reading and carries the exact figure alongside it.
 */
export function abbreviate(value: number, unit: string): string {
    if (unit === "COUNT" || unit === "PCT") return exact(value, unit);
    const symbol = unit === "GBP" ? "£" : "";
    const size = Math.abs(value);
    const [divisor, suffix] = size >= 1_000_000 ? [1_000_000, "M"]
        : size >= 1_000 ? [1_000, "k"] : [1, ""];
    const text = new Intl.NumberFormat("en-GB", {minimumFractionDigits: 2, maximumFractionDigits: 2})
        .format(size / divisor) + suffix;
    return value < 0 ? `(${symbol}${text})` : `${symbol}${text}`;
}

export function parse(view?: powerbi.DataView): Tile {
    const rows = view?.table?.rows;
    if (!rows?.length) return blocked("Bind one governed measure and its tile definition.");
    if (view!.metadata.segment) return blocked("Incomplete data was delivered.");
    if (rows.length !== 1) return blocked("Select exactly one tile definition.");

    const {values, fields, duplicate} = readRow(view!.table!.columns, rows[0]);
    if (duplicate) return blocked(`Multiple fields bound to ${duplicate}.`);
    const missing = missingText(fields, requiredText);
    if (missing) return blocked(`Missing ${missing}.`);

    const spec = (policy.tiles as Record<string, TileSpec>)[fields.tileKey];
    if (!spec || fields.tilePolicyRef !== policy.version) return blocked("No supported tile definition.");
    if (fields.deliveryRef !== policy.deliveryRef) return blocked("Delivery identity differs from the policy.");
    // The tile's wording is pinned, so it cannot be repointed without a
    // policy change that a reviewer can see.
    if (fields.tileLabel !== spec.label || fields.caption !== spec.caption
        || fields.contextLine !== spec.context || fields.authority !== spec.authority
        || fields.unit !== spec.unit)
        return blocked("Tile wording does not match the pinned definition.");

    const raw = values.value;
    const common = {state: "PRESENTED" as const, key: fields.tileKey, label: spec.label, caption: spec.caption,
        context: spec.context, authority: spec.authority, unit: spec.unit};
    // A blank measure is unavailable, which is not the same as zero.
    if (raw === null || raw === undefined)
        return {...common, state: "BLOCKED", value: null, display: "–", exact: "",
            reason: "No value for this context."};
    if (typeof raw !== "number" || !Number.isFinite(raw))
        return {...common, state: "BLOCKED", value: null, display: "–", exact: "",
            reason: "The supplied value is not a finite number."};

    return {...common, value: raw,
        display: policy.abbreviate ? abbreviate(raw, spec.unit) : exact(raw, spec.unit),
        exact: exact(raw, spec.unit), reason: ""};
}
