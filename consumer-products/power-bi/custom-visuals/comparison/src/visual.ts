import type powerbi from "powerbi-visuals-api";
import {bridgeTotals, impact, money, parse, type ComparisonRow} from "./contract";
import {styles} from "./styles";

const svgNamespace = "http://www.w3.org/2000/svg";

function element<K extends keyof HTMLElementTagNameMap>(parent: HTMLElement, tag: K, text = "", cls = "") {
    const node = document.createElement(tag);
    node.textContent = text;
    node.className = cls;
    parent.append(node);
    return node;
}

function svg(parent: SVGElement, tag: string, attrs: Record<string, string | number>, text = "") {
    const node = document.createElementNS(svgNamespace, tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
    node.textContent = text;
    parent.append(node);
    return node;
}

function evidence(parent: HTMLElement, label: string, fields: [string, string][]) {
    const detail = element(parent, "details");
    element(detail, "summary", label);
    const list = element(detail, "dl");
    for (const [key, value] of fields) {
        element(list, "dt", key);
        element(list, "dd", value);
    }
    return detail;
}

function grid(parent: HTMLElement, columns: string[]) {
    const table = element(element(parent, "div", "", "table-wrap"), "table");
    const row = element(element(table, "thead"), "tr");
    columns.forEach(label => { element(row, "th", label).scope = "col"; });
    return element(table, "tbody");
}

function bridge(parent: HTMLElement, totals: ReturnType<typeof bridgeTotals>, direction: string) {
    const {base, middle, end, firstDelta, secondDelta} = totals;
    const steps = [
        {label: "Budget", from: 0, to: base, amount: base, status: ""},
        {label: "Forecast vs budget", from: base, to: middle, amount: firstDelta, status: impact(firstDelta, direction)},
        {label: "May forecast", from: 0, to: middle, amount: middle, status: ""},
        {label: "Actual vs forecast", from: middle, to: end, amount: secondDelta, status: impact(secondDelta, direction)},
        {label: "Management actual", from: 0, to: end, amount: end, status: ""},
    ];
    const width = 920, height = 220, span = Math.max(base, middle, end, 1), baseline = 168;
    const y = (amount: number) => baseline - (amount / span) * 122;
    const chart = document.createElementNS(svgNamespace, "svg");
    chart.setAttribute("viewBox", `0 0 ${width} ${height}`);
    chart.setAttribute("role", "img");
    parent.append(chart);
    svg(chart, "title", {}, steps.map(s => `${s.label} ${money(s.amount, !!s.status)} ${s.status}`).join("; "));
    svg(chart, "line", {x1: 8, x2: width - 8, y1: baseline, y2: baseline, class: "axis"});
    const slot = width / steps.length, bar = 94;
    steps.forEach((step, i) => {
        const x = slot * (i + .5), top = Math.min(y(step.from), y(step.to));
        svg(chart, "rect", {x: x - bar / 2, y: top, width: bar,
            height: Math.max(2, Math.abs(y(step.to) - y(step.from))), rx: 3,
            class: step.status ? step.status.toLowerCase().replaceAll(" ", "-") : "anchor"});
        if (i < steps.length - 1)
            svg(chart, "line", {x1: x + bar / 2, x2: x + slot - bar / 2, y1: y(step.to), y2: y(step.to), class: "connector"});
        svg(chart, "text", {x, y: top - 9, class: "value"}, money(step.amount, Boolean(step.status)));
        svg(chart, "text", {x, y: 190}, step.label);
        if (step.status) svg(chart, "text", {x, y: 208, class: "status"}, step.status);
    });
}

export class Visual implements powerbi.extensibility.visual.IVisual {
    private root: HTMLElement;
    private host: powerbi.extensibility.visual.IVisualHost;
    private account = "";

    constructor(options?: powerbi.extensibility.visual.VisualConstructorOptions) {
        if (!options) throw new Error("Power BI host options are required.");
        this.root = options.element;
        this.host = options.host;
    }

    public update(options: powerbi.extensibility.visual.VisualUpdateOptions): void {
        this.host.eventService?.renderingStarted(options);
        this.root.replaceChildren();
        element(this.root, "style", styles);
        const panel = element(this.root, "article", "", "nexus-comparison");
        if (this.host.colorPalette.isHighContrast) {
            const foreground = this.host.colorPalette.foreground.value;
            for (const token of ["--ink", "--muted", "--rule", "--accent", "--bad"]) panel.style.setProperty(token, foreground);
            panel.style.setProperty("--paper", this.host.colorPalette.background.value);
        }
        try {
            const rows = parse(options.dataViews?.[0]);
            if (rows[0].mode === "variance") this.variance(panel, rows);
            else this.restatement(panel, rows);
            this.host.eventService?.renderingFinished(options);
        } catch (err) {
            panel.replaceChildren();
            element(panel, "h2", "Comparison unavailable");
            element(panel, "p", err instanceof Error ? err.message : "The supplied evidence could not be read.");
            this.host.eventService?.renderingFinished(options);
        }
    }

    private variance(panel: HTMLElement, rows: ComparisonRow[]) {
        const first = rows[0];
        element(panel, "p", `${first.period}  •  ${first.scope}  •  ${first.currency}`, "context");
        const head = element(panel, "div", "", "head");
        element(head, "h2", "Budget to forecast to actual");
        const label = element(head, "label", "Account ");
        const select = element(label, "select");
        const groups = new Map(rows.map(row => [row.groupKey, row.groupLabel]));
        for (const key of [...groups.keys()].sort()) {
            const option = element(select, "option", `${key} · ${groups.get(key)}`);
            option.value = key;
        }
        if (groups.has(this.account)) select.value = this.account;
        const body = element(panel, "section");
        const draw = () => {
            this.account = select.value;
            body.replaceChildren();
            const selected = rows.filter(r => r.groupKey === this.account).sort((a,b) => a.label.localeCompare(b.label));
            const total = bridgeTotals(selected);
            const result = impact(total.netDelta, selected[0].direction);
            element(body, "p", `${money(total.netDelta, true)} vs budget · ${result} · Both stages reconcile`, "result");
            bridge(body, total, selected[0].direction);
            const table = grid(body, ["Department", "Budget", "May forecast", "Actual", "Forecast vs budget", "Actual vs forecast"]);
            for (const r of selected) {
                const row = element(table, "tr");
                evidence(element(row, "td"), r.label, [["Budget line", r.baseRef], ["Forecast line", r.middleRef],
                    ["Management actual", r.endRef], ["Forecast derivation", r.evidence]]);
                [money(r.base), money(r.middle!), money(r.end), money(r.firstDelta!, true), money(r.secondDelta!, true)]
                    .forEach(n => element(row, "td", n, "num"));
            }
        };
        draw();
        select.onchange = draw;
        evidence(panel, "Comparison input digest", [["Adapter population", first.adapterDigest]]);
    }

    private restatement(panel: HTMLElement, rows: ComparisonRow[]) {
        const first = rows[0];
        element(panel, "p", `${first.period}  •  ${first.scope}  •  ${first.currency}`, "context");
        element(panel, "h2", first.groupLabel);
        const [original, revised] = [first.baseRef, first.endRef].map(ref => ref.split(" / ")[0]);
        element(panel, "p", `${original} → ${revised}  •  ${first.middleRef}`, "result");
        const table = grid(panel, ["Statement line", "Original", "Republished", "Delta", "Presentation adjustment"]);
        for (const r of [...rows].sort((a, b) => a.key.localeCompare(b.key))) {
            const row = element(table, "tr");
            element(row, "td", r.label);
            [money(r.base), money(r.end), money(r.netDelta, true)].forEach(n => element(row, "td", n, "num"));
            const [line, ledger, presented] = r.evidence.split(" | ");
            evidence(element(row, "td"), `${line} · ${ledger} · ${presented}`, [["Adjustment and replay proof", r.evidence]]);
        }
        const provenance = evidence(panel, "Publication and snapshot evidence", [["Original snapshot", first.baseRef],
            ["Republication", first.middleRef], ["Revised snapshot", first.endRef], ["Adapter population", first.adapterDigest]]);
        provenance.className = "snapshot-proof";
        provenance.open = true;
    }

    public getFormattingModel(): powerbi.visuals.FormattingModel { return {cards: []}; }
    public destroy(): void { this.root.replaceChildren(); }
}
