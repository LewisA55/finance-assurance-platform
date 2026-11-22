import type powerbi from "powerbi-visuals-api";
import {styles} from "./styles";

type Cell = powerbi.PrimitiveValue;
type Column = powerbi.DataViewMetadataColumn;
type VisibleTable = powerbi.DataViewTable & { rows: powerbi.DataViewTableRow[] };
const SVG = "http://www.w3.org/2000/svg";
const statusLabels: Record<string, [string, string]> = {
    HARD_CLOSED: ["Hard closed", "good"], PUBLISHED: ["Published", "good"],
    RECONCILED: ["Reconciled", "good"], PASS: ["Pass", "good"], PASSED: ["Passed", "good"],
    EXCEPTION: ["Exception", "bad"], FAIL: ["Fail", "bad"], FAILED: ["Failed", "bad"],
    OPEN: ["Open", "pending"], SOFT_CLOSED: ["Soft closed", "pending"], BLOCKED: ["Blocked", "pending"],
};

function el<K extends keyof HTMLElementTagNameMap>(parent: HTMLElement, tag: K, text = "", cls = "") {
    const node = document.createElement(tag);
    node.textContent = text;
    node.className = cls;
    parent.append(node);
    return node;
}

function svg(parent: SVGElement, tag: string, attrs: Record<string, string | number>, text = "") {
    const node = document.createElementNS(SVG, tag);
    Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, String(value)));
    node.textContent = text;
    parent.append(node);
    return node;
}

const hasGbp = (c: Column) => c.format?.includes("£") || c.queryName?.endsWith(" GBP");

function hasRows(table: powerbi.DataViewTable | undefined): table is VisibleTable {
    return Boolean(table?.rows?.length);
}

export function display(cell: Cell, column: Column): string {
    if (cell === null || cell === undefined) return "–";
    if (cell instanceof Date) return cell.toISOString().replace("T", " ").replace(".000Z", " UTC");
    if (typeof cell !== "number") return String(cell);
    if (column.format?.includes("%"))
        return new Intl.NumberFormat("en-GB", {style: "percent", maximumFractionDigits: 2}).format(cell);
    const gbp = hasGbp(column);
    const precision = gbp ? 2 : 0;
    const amount = new Intl.NumberFormat("en-GB", {minimumFractionDigits: precision,
        maximumFractionDigits: gbp ? 2 : 6}).format(Math.abs(cell));
    const value = gbp ? `£${amount}` : amount;
    return cell < 0 ? `(${value})` : value;
}

export class Visual implements powerbi.extensibility.visual.IVisual {
    private root: HTMLElement;
    private host: powerbi.extensibility.visual.IVisualHost;
    private selection: powerbi.extensibility.ISelectionManager;

    constructor(options?: powerbi.extensibility.visual.VisualConstructorOptions) {
        if (!options) throw new Error("Power BI host options are required.");
        this.root = options.element;
        this.host = options.host;
        this.selection = this.host.createSelectionManager();
        this.root.oncontextmenu = event => {
            event.preventDefault();
            const empty = this.host.createSelectionIdBuilder().createSelectionId();
            void this.selection.showContextMenu(empty, {x: event.clientX, y: event.clientY});
        };
    }

    public update(options: powerbi.extensibility.visual.VisualUpdateOptions): void {
        this.host.eventService?.renderingStarted(options);
        this.root.replaceChildren();
        el(this.root, "style", styles);
        const panel = el(this.root, "section", "", "nexus-detail");
        if (this.host.colorPalette.isHighContrast) {
            const foreground = this.host.colorPalette.foreground.value;
            for (const token of ["--ink", "--muted", "--line", "--accent", "--red", "--amber", "--series2", "--series3"])
                panel.style.setProperty(token, foreground);
            for (const token of ["--paper", "--wash"]) panel.style.setProperty(token, this.host.colorPalette.background.value);
        }
        try {
            const view = options.dataViews?.[0], table = view?.table;
            if (!hasRows(table)) el(panel, "p", "No rows in this selection.", "notice");
            else if (view?.metadata.segment) el(panel, "p", "This selection exceeds the display limit. Filter to a smaller scope.", "notice");
            else if (table.columns.some(c => c.roles?.period)) this.trend(panel, table, options.viewport);
            else this.table(panel, table);
            this.host.eventService?.renderingFinished(options);
        } catch {
            panel.replaceChildren();
            el(panel, "p", "The supplied fields could not be displayed.", "notice");
            this.host.eventService?.renderingFailed(options, "Invalid detail input");
        }
    }

    private table(panel: HTMLElement, model: VisibleTable) {
        const table = el(panel, "table");
        const head = el(el(table, "thead"), "tr");
        const measures = model.columns.map((c, i) => Boolean(c.isMeasure || c.type?.numeric
            || model.rows.some(row => typeof row[i] === "number")));
        model.columns.forEach((c, i) => {
            const heading = el(head, "th", c.displayName, measures[i] ? "numeric" : "");
            heading.scope = "col";
        });
        const body = el(table, "tbody");
        const version = model.columns.findIndex(c => c.queryName?.endsWith(".Reporting Version Ref"));
        const selectedRows = new Map<string, HTMLTableRowElement>();
        model.rows.forEach((data, i) => {
            const row = el(body, "tr");
            const identity = this.host.hostCapabilities?.allowInteractions
                ? this.host.createSelectionIdBuilder().withTable(model, i).createSelectionId() : undefined;
            const menu = (event: MouseEvent) => {
                if (!identity) return;
                event.preventDefault();
                event.stopPropagation();
                void this.selection.showContextMenu(identity, {x: event.clientX, y: event.clientY});
            };
            row.oncontextmenu = menu;
            if (identity) {
                selectedRows.set(identity.getKey(), row);
                row.onclick = event => {
                    void this.selection.select(identity, event.ctrlKey || event.metaKey).then(ids => {
                        const keys = new Set(ids.map(id => (id as powerbi.visuals.ISelectionId).getKey()));
                        for (const [key, selected] of selectedRows)
                            selected.classList.toggle("selected", keys.has(key));
                    });
                };
            }
            model.columns.forEach((c, index) => {
                const value = data[index];
                const label = display(value, c);
                const cell = el(row, "td", "", measures[index] ? "numeric" : "");
                cell.title = label;
                const state = typeof value === "string" ? statusLabels[value] : undefined;
                if (index === version && identity && typeof value === "string") {
                    const control = el(cell, "button", label, "version");
                    control.type = "button";
                    control.title = `${label} · Open evidence menu`;
                    control.onclick = event => {
                        event.stopPropagation();
                        const rect = control.getBoundingClientRect();
                        void this.selection.showContextMenu(identity, {x: rect.left, y: rect.bottom});
                    };
                } else if (state) {
                    el(cell, "span", state[0], `status ${state[1]}`);
                } else cell.textContent = label;
            });
        });
    }

    private trend(panel: HTMLElement, table: VisibleTable, viewport: powerbi.IViewport) {
        const period = table.columns.findIndex(column => column.roles?.period);
        const series = table.columns.map((column, index) => ({column, index})).filter(s => s.column.roles?.series);
        const sorted = table.rows.map((row, index) => ({row, index}))
            .sort((a, b) => String(a.row[period]).localeCompare(String(b.row[period])));
        const rows = sorted.map(item => item.row);
        if (!series.length || new Set(rows.map(row => row[period])).size !== rows.length)
            throw new Error("Expected one observation per period and series.");
        const values = rows.flatMap(row => series.map(s => row[s.index]))
            .filter((value): value is number => typeof value === "number" && Number.isFinite(value));
        if (!values.length) {
            el(panel, "p", "No amounts in this selection.", "notice");
            return;
        }
        const legend = el(panel, "ul", "", "legend");
        const current = rows[rows.length - 1];
        for (const [i, {column, index}] of series.entries()) {
            const item = el(legend, "li", "", `series${i}`);
            el(item, "span", column.displayName);
            el(item, "strong", display(current[index], column));
        }
        const chart = document.createElementNS(SVG, "svg");
        const width = Math.max(300, viewport.width - 20), height = Math.max(108, viewport.height - 84);
        chart.setAttribute("viewBox", `0 0 ${width} ${height}`);
        chart.setAttribute("role", "img");
        panel.append(chart);
        const firstMonth = String(rows[0][period]), lastMonth = String(current[period]);
        svg(chart, "title", {}, `${series.map(s => s.column.displayName).join(", ")} from ${firstMonth} to ${lastMonth}`);
        const low = Math.min(0, ...values), high = Math.max(0, ...values), span = high - low || 1;
        const x = (i: number) => 58 + i * (width - 72) / Math.max(1, rows.length - 1);
        const y = (value: number) => 12 + (high - value) * (height - 34) / span;
        const axis = new Intl.NumberFormat("en-GB", {notation: "compact", maximumFractionDigits: 1});
        for (const tick of new Set([low, low < 0 ? 0 : high / 2, high])) {
            svg(chart, "line", {x1: 58, y1: y(tick), x2: width - 14, y2: y(tick), class: "axis"});
            const label = `${hasGbp(series[0].column) ? "£" : ""}${axis.format(Math.abs(tick))}`;
            svg(chart, "text", {x: 50, y: y(tick) + 4, "text-anchor": "end"}, tick < 0 ? `(${label})` : label);
        }
        const labelEvery = Math.max(1, Math.ceil(rows.length / (width / 74)));
        for (let i = 0; i < rows.length; i++) {
            const month = String(rows[i][period]);
            if (i === rows.length - 1 || (i % labelEvery === 0 && i < rows.length - labelEvery))
                svg(chart, "text", {x: x(i), y: height - 3, "text-anchor": i === rows.length - 1 ? "end" : "middle"}, month);
        }
        series.forEach(({index, column}, s) => {
            let path = "", connected = false;
            const markers: [number, number][] = [];
            rows.forEach((row, i) => {
                const value = row[index];
                if (typeof value !== "number" || !Number.isFinite(value)) {
                    connected = false;
                    return;
                }
                path += `${connected ? "L" : "M"}${x(i)},${y(value)} `;
                connected = true;
                markers.push([i, value]);
            });
            svg(chart, "path", {d: path, class: `trend series${s}`});
            markers.forEach(([i, value]) => {
                const point = svg(chart, "circle", {cx: x(i), cy: y(value), r: 3, class: `point series${s}`});
                const title = `${rows[i][period]} · ${column.displayName} · ${display(value, column)}`;
                svg(point, "title", {}, title);
                if (this.host.hostCapabilities?.allowInteractions) {
                    const id = this.host.createSelectionIdBuilder().withTable(table, sorted[i].index).createSelectionId();
                    point.setAttribute("tabindex", "0");
                    point.setAttribute("role", "button");
                    point.setAttribute("aria-label", title);
                    const select = (multiple: boolean) => { void this.selection.select(id, multiple); };
                    point.addEventListener("click", event => {
                        const click = event as MouseEvent;
                        select(click.ctrlKey || click.metaKey);
                    });
                    point.addEventListener("keydown", event => {
                        const key = event as KeyboardEvent;
                        if (key.key === "Enter" || key.key === " ") {
                            key.preventDefault();
                            select(key.ctrlKey || key.metaKey);
                        }
                    });
                    point.addEventListener("contextmenu", event => {
                        const click = event as MouseEvent;
                        click.preventDefault();
                        click.stopPropagation();
                        void this.selection.showContextMenu(id, {x: click.clientX, y: click.clientY});
                    });
                }
            });
        });
    }

    public getFormattingModel(): powerbi.visuals.FormattingModel { return {cards: []}; }
    public destroy(): void { this.root.oncontextmenu = null; this.root.replaceChildren(); }
}
