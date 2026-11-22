import type powerbi from "powerbi-visuals-api";
import policy from "../policy.json";
import {readRow, missingText} from "../../shared/src/dataview";
import {exactMinor} from "../../shared/src/money";

export const requiredText = ["claimKey", "purpose", "authority", "deliveryRef", "deliveryDigest", "sourceDigest",
    "evidenceRef", "contextState", "edgeId", "fromNodeId", "toNodeId", "fromLabel", "toLabel", "fromKind",
    "toKind", "edgeKind", "transformationClass", "datasetId", "evidenceDepth", "lineagePolicyRef"];

export type NodeKind = "GOLD_MODEL" | "SYMBOLIC_COLLECTION" | "BOUNDARY";
export type Node = {
    id: string; label: string; kind: NodeKind;
    datasetId: string; transformationClass: string; bronze: string[]; evidenceDepth: string;
};
export type Edge = {id: string; from: string; to: string; kind: string};
export type Check = {label: string; state: "TIED" | "BROKEN" | "UNASSESSED"; detail: string};
export type Graph = {
    state: "RESOLVED" | "INCOMPLETE" | "BLOCKED";
    reason: string;
    nodes: Map<string, Node>; edges: Edge[]; checks: Check[];
    tally: {label: string; detail: string}[];
    fields: Record<string, string>;
};

const blocked = (reason: string, fields: Record<string, string> = {}): Graph =>
    ({state: "BLOCKED", reason, nodes: new Map(), edges: [], checks: [], tally: [], fields});

/** Nodes reaching into `id`, and nodes it reaches. Neighbourhood only. */
export function neighbourhood(graph: Graph, id: string): {upstream: Edge[]; downstream: Edge[]} {
    return {
        upstream: graph.edges.filter(e => e.to === id),
        downstream: graph.edges.filter(e => e.from === id),
    };
}

/** A cycle is a metadata error for this view; the edges are still kept. */
export function findCycle(edges: readonly Edge[]): string[] | null {
    const adjacency = new Map<string, string[]>();
    for (const edge of edges) adjacency.set(edge.from, [...(adjacency.get(edge.from) ?? []), edge.to]);
    const colour = new Map<string, number>();
    const stack: string[] = [];
    let found: string[] | null = null;
    const walk = (node: string): void => {
        if (found) return;
        colour.set(node, 1);
        stack.push(node);
        for (const next of adjacency.get(node) ?? []) {
            if (found) break;
            const seen = colour.get(next) ?? 0;
            if (seen === 1) found = [...stack.slice(stack.indexOf(next)), next];
            else if (seen === 0) walk(next);
        }
        colour.set(node, 2);
        stack.pop();
    };
    for (const node of adjacency.keys()) if ((colour.get(node) ?? 0) === 0) walk(node);
    return found;
}

export function parse(view?: powerbi.DataView): Graph {
    const rows = view?.table?.rows;
    if (!rows?.length) return blocked("Select the delivery lineage edges.");
    if (view!.metadata.segment) return blocked("Incomplete edge delivery. Narrow the selection.");

    const bound = rows.map(row => readRow(view!.table!.columns, row));
    const duplicate = bound.find(b => b.duplicate)?.duplicate;
    if (duplicate) return blocked(`Multiple fields bound to ${duplicate}.`);
    const first = bound[0];
    const missing = missingText(first.fields, requiredText);
    if (missing) return blocked(`Missing ${missing}.`, first.fields);

    const constant = ["claimKey", "purpose", "authority", "deliveryRef", "deliveryDigest", "sourceDigest",
        "lineagePolicyRef", "contextState", "evidenceDepth"];
    for (const b of bound)
        for (const role of constant)
            if (b.fields[role] !== first.fields[role])
                return blocked("The selection mixes more than one lineage claim.", first.fields);

    const fields = first.fields;
    if (fields.lineagePolicyRef !== policy.version)
        return blocked("No supported lineage policy.", fields);
    if (fields.deliveryRef !== policy.deliveryRef || fields.deliveryDigest !== policy.deliveryDigest || fields.sourceDigest !== policy.sourceDigest)
        return blocked("Delivery or source identity differs from the supported policy.", fields);
    if (fields.contextState !== "VALID")
        return blocked("The model reports incomplete or ambiguous context.", fields);
    // Row-level depth would need a different authoritative edge feed.
    if (fields.evidenceDepth !== policy.evidenceDepth)
        return blocked(`Unsupported evidence depth ${fields.evidenceDepth}.`, fields);

    const nodes = new Map<string, Node>();
    const edges: Edge[] = [];
    const seen = new Set<string>();
    const kinds = policy.nodeKinds as readonly string[];

    const note = (id: string, label: string, kind: string, row: typeof first): string | null => {
        if (!kinds.includes(kind)) return `Unknown node kind ${kind} for ${id}.`;
        const target = row.fields.toNodeId === id;
        const existing = nodes.get(id);
        if (existing) {
            // One node, one identity: a kind or label that changes between
            // edges would make the same dataset two different things.
            if (existing.kind !== kind || existing.label !== label) return `Node ${id} has more than one identity.`;
            if (!target) return null;
            if (existing.datasetId && existing.datasetId !== row.fields.datasetId)
                return `Node ${id} is declared by more than one dataset.`;
            // A gold model may be met first as someone else's dependency, so
            // its own dataset row fills the detail in whenever it arrives.
            existing.datasetId = row.fields.datasetId;
            existing.transformationClass = row.fields.transformationClass;
            existing.bronze = row.fields.declaredBronzeSources
                ? row.fields.declaredBronzeSources.split("|").map(s => s.trim()).filter(Boolean) : [];
            return null;
        }
        nodes.set(id, {
            id, label, kind: kind as NodeKind,
            datasetId: target ? row.fields.datasetId : "",
            transformationClass: target ? row.fields.transformationClass : "",
            bronze: target && row.fields.declaredBronzeSources
                ? row.fields.declaredBronzeSources.split("|").map(s => s.trim()).filter(Boolean) : [],
            evidenceDepth: row.fields.evidenceDepth,
        });
        return null;
    };

    for (const b of bound) {
        const f = b.fields;
        if (seen.has(f.edgeId)) return blocked(`Duplicate edge identity ${f.edgeId}.`, fields);
        seen.add(f.edgeId);
        if (f.edgeKind !== policy.edgeKind) return blocked(`Unsupported edge kind ${f.edgeKind}.`, fields);
        const problem = note(f.toNodeId, f.toLabel, f.toKind, b) ?? note(f.fromNodeId, f.fromLabel, f.fromKind, b);
        if (problem) return blocked(problem, fields);
        edges.push({id: f.edgeId, from: f.fromNodeId, to: f.toNodeId, kind: f.edgeKind});
    }

    const expected = exactMinor(first.values.expectedRowCount);
    if (expected !== edges.length)
        return blocked("The delivered edge count does not match the expected count.", fields);

    const selfEdges = edges.filter(e => e.from === e.to);
    const cycle = findCycle(edges);
    const datasets = [...nodes.values()].filter(n => n.datasetId).length;
    const byKind = (kind: NodeKind) => [...nodes.values()].filter(n => n.kind === kind).length;

    const checks: Check[] = [
        {label: "Edge identities are unique", state: "TIED", detail: `${edges.length} deduplicated edges`},
        {label: "No self-edges", state: selfEdges.length ? "BROKEN" : "TIED",
            detail: selfEdges.length ? `${selfEdges.length} node${selfEdges.length === 1 ? "" : "s"} depend on themselves`
                : "No dataset depends on itself"},
        {label: "Acyclic", state: cycle ? "BROKEN" : "TIED",
            detail: cycle ? `Metadata error: ${cycle.join(" → ")}` : "No cycle in the declared dependencies"},
        {label: "Declared edge and dataset counts",
            state: edges.length === policy.expectedEdgeCount && datasets === policy.expectedDatasetCount ? "TIED" : "BROKEN",
            detail: `${edges.length} of ${policy.expectedEdgeCount} edges, ${datasets} of ${policy.expectedDatasetCount} datasets`},
        {label: "Evidence depth", state: "UNASSESSED",
            detail: `${policy.evidenceDepth.replaceAll("_", " ").toLowerCase()}; no row-level proof`},
    ];

    const tally = [
        {label: "Gold models", detail: `${byKind("GOLD_MODEL")} with a dataset row`},
        {label: "Boundary nodes", detail: `${byKind("BOUNDARY")} with no lineage of their own here`},
        {label: "Symbolic collections", detail: `${byKind("SYMBOLIC_COLLECTION")} left unresolved by design`},
    ];

    const state = selfEdges.length || cycle ? "INCOMPLETE" : "RESOLVED";
    const reason = cycle ? "A cycle is declared in the dependency metadata"
        : selfEdges.length ? "A dataset declares itself as a dependency"
        : `${edges.length} declared dependencies across ${nodes.size} nodes`;
    return {state, reason, nodes, edges, checks, tally, fields};
}
