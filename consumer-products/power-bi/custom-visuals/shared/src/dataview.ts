// Shared DataView role binding. The renderer never trusts column order and
// never silently accepts two fields bound to the same role.

export type RoleColumn = { roles?: Record<string, boolean | undefined> };
export type Bound = { values: Record<string, unknown>; fields: Record<string, string>; duplicate?: string };

/** Bind one DataView table row to its roles. `fields` holds the text roles. */
export function readRow(columns: readonly RoleColumn[], row: readonly unknown[]): Bound {
    const values: Record<string, unknown> = {};
    const fields: Record<string, string> = {};
    for (let i = 0; i < columns.length; i++) {
        for (const role of Object.keys(columns[i].roles || {}).filter(k => columns[i].roles![k])) {
            if (role in values) return { values, fields, duplicate: role };
            values[role] = row[i];
            if (typeof values[role] === "string") fields[role] = values[role] as string;
        }
    }
    return { values, fields };
}

/** First role name in `required` with no non-blank text value, else null. */
export function missingText(fields: Record<string, string>, required: readonly string[]): string | null {
    for (const role of required) if (!fields[role]?.trim()) return role;
    return null;
}
