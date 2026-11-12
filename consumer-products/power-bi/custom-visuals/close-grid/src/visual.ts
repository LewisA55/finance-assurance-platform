import type powerbi from "powerbi-visuals-api";
import {parse, cellKey, type Cell, type Grid, type MarkerState} from "./contract";
import {styles} from "./styles";
import policy from "../policy.json";

const SYMBOL: Record<MarkerState, string> = {
    SATISFIED: "●", NOT_APPLICABLE: "–", ATTENTION: "!", UNCLASSIFIED: "?",
};

export class Visual implements powerbi.extensibility.visual.IVisual {
    private root: HTMLElement;
    private host: powerbi.extensibility.visual.IVisualHost;
    private selection: powerbi.extensibility.ISelectionManager;
    private open = new Set<string>();
    constructor(options?: powerbi.extensibility.visual.VisualConstructorOptions) {
        if (!options) throw new Error("Power BI host options are required.");
        this.root = options.element;
        this.host = options.host;
        this.selection = this.host.createSelectionManager();
    }

    public update(options: powerbi.extensibility.visual.VisualUpdateOptions): void {
        this.host.eventService?.renderingStarted(options);
        this.root.replaceChildren();
        this.host.tooltipService?.hide({immediately: true, isTouchEvent: false});
        try {
            const grid = parse(options.dataViews?.[0]);
            const add = (tag: string, text: string, parent: HTMLElement, cls = "") => {
                const el = document.createElement(tag);
                el.textContent = text; el.className = cls; parent.appendChild(el); return el;
            };
            add("style", styles, this.root);
            const card = add("article", "", this.root, `nexus-close ${grid.state.toLowerCase()}`);
            card.setAttribute("aria-live", "polite");
            if (this.host.colorPalette.isHighContrast) {
                const fore = this.host.colorPalette.foreground.value;
                for (const token of ["--ink", "--accent", "--muted", "--rule", "--bad", "--warn"])
                    card.style.setProperty(token, fore);
                card.style.setProperty("--paper", this.host.colorPalette.background.value);
            }
            add("div", "NEXUS / CLOSE GOVERNANCE", card, "eyebrow");
            add("h2", grid.label, card);
            add("p", grid.reason, card, "status");
            add("p", `Read-only review surface. Close decision authority stays in the platform. Timestamps in ${policy.timezone}.`,
                card, "context");

            const legend = add("ul", "", card, "legend");
            for (const [state, text] of [["SATISFIED", "satisfied"], ["NOT_APPLICABLE", "not applicable"],
                ["UNCLASSIFIED", "unclassified"], ["ATTENTION", "attention"]] as [MarkerState, string][]) {
                const li = add("li", "", legend);
                add("span", SYMBOL[state], li, `marker ${state.toLowerCase()}`);
                li.appendChild(document.createTextNode(text));
            }
            const key = add("li", policy.dimensions.map(d => `${d.initial} ${d.label.toLowerCase()}`).join(" · "), legend);
            key.style.color = "var(--muted)";

            if (grid.cells.size) card.appendChild(this.table(grid, options));
            this.list(grid.tally.map(t => [t.label, t.counts] as const), card, add, "tally");
            this.list(grid.checks.map(c => [c.label, c.detail, c.state.toLowerCase()] as const), card, add, "checks");
            add("p", policy.notes.consolidated, card, "note");
            add("p", `${policy.notes.progress} ${policy.notes.signOff}`, card, "note");

            const details = add("details", "", card);
            add("summary", "Authority and evidence", details);
            for (const [label, k] of [["Governance policy", "gridPolicyRef"], ["Purpose", "purpose"],
                ["Source authority", "authority"], ["Evidence relation", "evidenceRef"],
                ["Delivery", "deliveryRef"], ["Delivery digest (declared)", "deliveryDigest"],
                ["Source digest", "sourceDigest"]])
                add("p", `${label}: ${grid.fields[k] || "Not supplied"}`, details);
            add("p", policy.notes.fixtures, details);

            this.host.eventService?.renderingFinished(options);
        } catch {
            this.root.replaceChildren();
            const error = document.createElement("p");
            error.textContent = "Grid withheld. Unable to validate the visual input.";
            this.root.appendChild(error);
            this.host.eventService?.renderingFailed(options, "Unable to validate input");
        }
    }

    private table(grid: Grid, options: powerbi.extensibility.visual.VisualUpdateOptions): HTMLTableElement {
        const table = document.createElement("table");
        const head = table.createTHead().insertRow();
        const corner = document.createElement("th");
        corner.scope = "col"; corner.textContent = "Period";
        head.appendChild(corner);
        for (const scope of grid.scopes) {
            const th = document.createElement("th");
            th.scope = "col";
            th.textContent = scope.id;
            const sub = document.createElement("small");
            sub.textContent = scope.type.replaceAll("_", " ").toLowerCase();
            th.appendChild(sub);
            head.appendChild(th);
        }
        const body = table.createTBody();
        const dataTable = options.dataViews?.[0]?.table;
        let index = 0;
        for (const period of grid.periods) {
            const tr = body.insertRow();
            const label = tr.insertCell();
            label.className = "period";
            label.textContent = period;
            for (const scope of grid.scopes) {
                const td = tr.insertCell();
                const cell = grid.cells.get(cellKey(period, scope.id));
                if (!cell) { td.textContent = "–"; continue; }
                td.appendChild(this.cell(cell, dataTable, index++));
            }
        }
        return table;
    }

    private cell(cell: Cell, dataTable: powerbi.DataViewTable | undefined, index: number): HTMLElement {
        const wrap = document.createElement("div");
        const button = document.createElement("button");
        button.type = "button";
        button.className = "cell";
        const markers = document.createElement("div");
        markers.className = "markers";
        for (const marker of cell.markers) {
            const chip = document.createElement("span");
            chip.className = `marker ${marker.state.toLowerCase()}`;
            chip.textContent = `${marker.initial}${SYMBOL[marker.state]}`;
            chip.title = `${marker.label}: ${marker.raw}`;
            markers.appendChild(chip);
        }
        button.appendChild(markers);
        const state = document.createElement("div");
        state.className = "close-state";
        const strong = document.createElement("b");
        strong.textContent = cell.closeLabel;
        state.appendChild(strong);
        state.appendChild(document.createTextNode(` · ${cell.closedAt}`));
        button.appendChild(state);
        if (cell.evidence.state === "INCOMPLETE") {
            const flag = document.createElement("div");
            flag.className = "evidence-flag";
            flag.textContent = `Missing ${cell.evidence.missing.join(", ")}`;
            button.appendChild(flag);
        }
        button.setAttribute("aria-expanded", String(this.open.has(cell.version)));
        button.onclick = () => {
            if (this.open.has(cell.version)) this.open.delete(cell.version);
            else this.open.add(cell.version);
            wrap.querySelector(".detail")?.remove();
            if (this.open.has(cell.version)) wrap.appendChild(this.detail(cell));
            button.setAttribute("aria-expanded", String(this.open.has(cell.version)));
            if (dataTable && this.host.hostCapabilities?.allowInteractions) {
                const id = this.host.createSelectionIdBuilder().withTable(dataTable, index).createSelectionId();
                void this.selection.select(id);
            }
        };
        wrap.appendChild(button);
        if (this.open.has(cell.version)) wrap.appendChild(this.detail(cell));
        return wrap;
    }

    private detail(cell: Cell): HTMLElement {
        const detail = document.createElement("div");
        detail.className = "detail";
        const line = (label: string, text: string) => {
            const p = document.createElement("p");
            p.style.margin = "0";
            const b = document.createElement("b");
            b.textContent = `${label}: `;
            p.appendChild(b);
            p.appendChild(document.createTextNode(text));
            detail.appendChild(p);
        };
        line("Reporting version", cell.version);
        line("Publication", cell.publicationState);
        for (const event of cell.events) line(event.label, event.ref || "Not supplied");
        for (const marker of cell.markers) line(marker.label, marker.raw);
        return detail;
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
    public destroy(): void { this.root.replaceChildren(); this.open.clear(); }
}
