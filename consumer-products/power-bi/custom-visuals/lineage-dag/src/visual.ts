import type powerbi from "powerbi-visuals-api";
import {parse, neighbourhood, type Edge, type Graph, type Node} from "./contract";
import {styles} from "./styles";
import policy from "../policy.json";

const SVG = "http://www.w3.org/2000/svg";
const BOX_H = 26, GAP = 8, PAD = 12, MAX_SIDE = 14;

export class Visual implements powerbi.extensibility.visual.IVisual {
    private root: HTMLElement;
    private host: powerbi.extensibility.visual.IVisualHost;
    private selected = "";
    private query = "";
    constructor(options?: powerbi.extensibility.visual.VisualConstructorOptions) {
        if (!options) throw new Error("Power BI host options are required.");
        this.root = options.element;
        this.host = options.host;
    }

    public update(options: powerbi.extensibility.visual.VisualUpdateOptions): void {
        this.host.eventService?.renderingStarted(options);
        this.root.replaceChildren();
        this.host.tooltipService?.hide({immediately: true, isTouchEvent: false});
        try {
            const graph = parse(options.dataViews?.[0]);
            if (!graph.nodes.has(this.selected)) this.selected = "";
            const width = Math.max(320, (options.viewport?.width ?? 900) - 44);
            const add = (tag: string, text: string, parent: HTMLElement, cls = "") => {
                const el = document.createElement(tag);
                el.textContent = text; el.className = cls; parent.appendChild(el); return el;
            };
            add("style", styles, this.root);
            const card = add("article", "", this.root, `nexus-lineage ${graph.state.toLowerCase()}`);
            card.setAttribute("aria-live", "polite");
            if (this.host.colorPalette.isHighContrast) {
                const fore = this.host.colorPalette.foreground.value;
                for (const token of ["--ink", "--accent", "--muted", "--rule", "--bad", "--warn"])
                    card.style.setProperty(token, fore);
                card.style.setProperty("--paper", this.host.colorPalette.background.value);
            }
            add("div", "NEXUS / DATASET LINEAGE", card, "eyebrow");
            add("h2", "Delivery lineage", card);
            add("p", graph.reason, card, "status");
            add("p", policy.notes.scope, card, "context");

            if (graph.nodes.size) {
                add("h3", "Find a dataset", card);
                const search = add("input", "", card, "search") as HTMLInputElement;
                search.type = "search";
                search.placeholder = "Filter nodes by name";
                search.value = this.query;
                search.setAttribute("aria-label", "Filter lineage nodes by name");

                const list = add("ul", "", card, "nodes");
                const focus = add("div", "", card);
                const edgeHead = add("h3", "Declared edges", card);
                const edgeBox = add("div", "", card);

                const paint = () => {
                    this.nodeList(graph, list);
                    focus.replaceChildren();
                    if (this.selected) focus.appendChild(this.focusView(graph, width));
                    edgeHead.textContent = this.selected ? "Edges touching the selection" : "Declared edges";
                    edgeBox.replaceChildren(this.edgeTable(graph));
                };
                search.oninput = () => { this.query = search.value; paint(); };
                // Re-selecting is a view action, so only the dependent panels
                // are repainted and the search box keeps focus.
                list.addEventListener("click", (event) => {
                    const button = (event.target as HTMLElement).closest("button");
                    const id = button?.getAttribute("data-node");
                    if (!id) return;
                    this.selected = this.selected === id ? "" : id;
                    paint();
                });
                paint();
            }

            this.list(graph.tally.map(t => [t.label, t.detail] as const), card, add, "tally");
            this.list(graph.checks.map(c => [c.label, c.detail, c.state.toLowerCase()] as const), card, add, "checks");
            add("p", policy.notes.bronze, card, "note");
            add("p", `${policy.notes.symbolic} ${policy.notes.boundary}`, card, "note");

            const details = add("details", "", card);
            add("summary", "Authority and evidence", details);
            for (const [label, key] of [["Lineage policy", "lineagePolicyRef"], ["Purpose", "purpose"],
                ["Source authority", "authority"], ["Evidence relation", "evidenceRef"],
                ["Evidence depth", "evidenceDepth"], ["Delivery", "deliveryRef"],
                ["Delivery digest (declared)", "deliveryDigest"], ["Source digest", "sourceDigest"]])
                add("p", `${label}: ${graph.fields[key] || "Not supplied"}`, details);
            add("p", policy.notes.depth, details);

            this.host.eventService?.renderingFinished(options);
        } catch {
            this.root.replaceChildren();
            const error = document.createElement("p");
            error.textContent = "Lineage withheld. Unable to validate the visual input.";
            this.root.appendChild(error);
            this.host.eventService?.renderingFailed(options, "Unable to validate input");
        }
    }

    private matches(node: Node): boolean {
        const q = this.query.trim().toLowerCase();
        return !q || node.id.toLowerCase().includes(q) || node.label.toLowerCase().includes(q);
    }

    private nodeList(graph: Graph, list: HTMLElement): void {
        list.replaceChildren();
        const shown = [...graph.nodes.values()].filter(n => this.matches(n))
            .sort((a, b) => a.kind.localeCompare(b.kind) || a.id.localeCompare(b.id));
        if (!shown.length) {
            const li = document.createElement("li");
            li.className = "empty";
            li.textContent = "No node matches that filter.";
            list.appendChild(li);
            return;
        }
        for (const node of shown) {
            const li = document.createElement("li");
            const button = document.createElement("button");
            button.type = "button";
            button.className = `node ${node.kind.toLowerCase()}`;
            button.textContent = node.label;
            button.title = `${node.id} — ${node.kind.replaceAll("_", " ").toLowerCase()}`;
            button.setAttribute("data-node", node.id);
            button.setAttribute("aria-pressed", String(this.selected === node.id));
            li.appendChild(button);
            list.appendChild(li);
        }
    }

    /** Neighbourhood of the selection: direct upstream and downstream only. */
    private focusView(graph: Graph, width: number): HTMLElement {
        const wrap = document.createElement("div");
        const node = graph.nodes.get(this.selected)!;
        const {upstream, downstream} = neighbourhood(graph, this.selected);
        const left = upstream.slice(0, MAX_SIDE);
        const right = downstream.slice(0, MAX_SIDE);
        const rows = Math.max(left.length, right.length, 1);
        const height = rows * (BOX_H + GAP) + PAD * 2;
        const colW = Math.max(120, (width - PAD * 2) / 3 - 16);

        const el = <T extends SVGElement>(name: string, attrs: Record<string, string | number>, text?: string): T => {
            const n = document.createElementNS(SVG, name) as T;
            for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, String(v));
            if (text !== undefined) n.textContent = text;
            return n;
        };
        const svg = el<SVGSVGElement>("svg", {width, height, viewBox: `0 0 ${width} ${height}`, role: "img"});
        svg.appendChild(el("title", {}, `Direct dependencies of ${node.label}`));

        const box = (id: string, x: number, y: number, focus = false) => {
            const target = graph.nodes.get(id)!;
            const cls = `${target.kind.toLowerCase()}${focus ? " focus" : ""}`;
            svg.appendChild(el("rect", {class: cls, x, y, width: colW, height: BOX_H, rx: 3}));
            const label = target.label.length > Math.floor(colW / 6.2)
                ? target.label.slice(0, Math.floor(colW / 6.2) - 1) + "…" : target.label;
            const text = el<SVGTextElement>("text", {x: x + 7, y: y + 13});
            text.textContent = label;
            svg.appendChild(text);
            svg.appendChild(el("text", {class: "kind", x: x + 7, y: y + 22},
                target.kind.replaceAll("_", " ").toLowerCase()));
            return {x, y, cx: x + colW, cy: y + BOX_H / 2};
        };

        const midY = PAD + ((rows * (BOX_H + GAP)) - BOX_H) / 2;
        const centre = box(this.selected, PAD + colW + 16, midY, true);
        left.forEach((edge, i) => {
            const b = box(edge.from, PAD, PAD + i * (BOX_H + GAP));
            svg.appendChild(el("path", {d: `M${b.cx} ${b.cy} C${b.cx + 10} ${b.cy} ${centre.x - 10} ${centre.cy} ${centre.x} ${centre.cy}`}));
        });
        right.forEach((edge, i) => {
            const x = PAD + (colW + 16) * 2;
            const b = box(edge.to, x, PAD + i * (BOX_H + GAP));
            svg.appendChild(el("path", {d: `M${centre.cx} ${centre.cy} C${centre.cx + 10} ${centre.cy} ${b.x - 10} ${b.cy} ${b.x} ${b.cy}`}));
        });
        wrap.appendChild(svg);

        const detail = document.createElement("div");
        detail.className = "detail";
        const line = (label: string, text: string, symbolic = false) => {
            const p = document.createElement("p");
            const b = document.createElement("b");
            b.textContent = `${label}: `;
            p.appendChild(b);
            const span = document.createElement("span");
            span.textContent = text;
            if (symbolic) span.className = "symbolic";
            p.appendChild(span);
            detail.appendChild(p);
        };
        line("Node", `${node.id} (${node.kind.replaceAll("_", " ").toLowerCase()})`);
        if (node.datasetId) line("Dataset", node.datasetId);
        if (node.transformationClass) line("Transformation", node.transformationClass);
        if (node.bronze.length)
            for (const source of node.bronze)
                line("Declared A24 source", source,
                    (policy.symbolicBronzeSources as string[]).includes(source));
        if (node.kind === "BOUNDARY") line("Lineage", "Outside this metadata; boundary node.");
        if (node.kind === "SYMBOLIC_COLLECTION") line("Collection", "Stands for a set of datasets; not resolved.", true);
        line("Direct dependencies", String(upstream.length));
        line("Direct dependants", String(downstream.length));
        if (upstream.length > left.length || downstream.length > right.length)
            line("Shown", `first ${MAX_SIDE} on each side`);
        wrap.appendChild(detail);
        return wrap;
    }

    /** The accessible edge list, filtered to the search and any selection. */
    private edgeTable(graph: Graph): HTMLTableElement {
        const table = document.createElement("table");
        const head = table.createTHead().insertRow();
        for (const text of ["From", "Kind", "To", "Transformation"]) {
            const th = document.createElement("th");
            th.scope = "col"; th.textContent = text;
            head.appendChild(th);
        }
        const relevant = (edge: Edge) => this.selected
            ? edge.from === this.selected || edge.to === this.selected
            : this.matches(graph.nodes.get(edge.from)!) || this.matches(graph.nodes.get(edge.to)!);
        const body = table.createTBody();
        for (const edge of graph.edges.filter(relevant)) {
            const tr = body.insertRow();
            const from = graph.nodes.get(edge.from)!;
            const to = graph.nodes.get(edge.to)!;
            tr.insertCell().textContent = from.label;
            const kind = tr.insertCell();
            kind.className = "kind";
            kind.textContent = from.kind.replaceAll("_", " ").toLowerCase();
            tr.insertCell().textContent = to.label;
            const transform = tr.insertCell();
            transform.className = "kind";
            transform.textContent = to.transformationClass || "–";
        }
        return table;
    }

    private list(entries: readonly (readonly [string, string] | readonly [string, string, string])[],
                 card: HTMLElement,
                 add: (t: string, x: string, p: HTMLElement, c?: string) => HTMLElement, cls: string): void {
        if (!entries.length) return;
        const list = add("ul", "", card, cls);
        for (const entry of entries) {
            const li = add("li", "", list);
            add("span", entry[0], li, "name");
            add("span", entry[1], li, `result ${entry[2] ?? ""}`.trim());
        }
    }

    public getFormattingModel(): powerbi.visuals.FormattingModel { return {cards: []}; }
    public destroy(): void { this.root.replaceChildren(); this.selected = ""; this.query = ""; }
}
