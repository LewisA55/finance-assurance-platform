import type powerbi from "powerbi-visuals-api";
import {parse, type Assertion, type Panel} from "./contract";
import {formatMinor} from "../../shared/src/money";
import {styles} from "./styles";
import policy from "../policy.json";

/** Counts are not money. Only a minor-unit claim is scaled for display. */
function value(amount: number | null, unit: string): string {
    if (amount === null) return "Not supplied";
    if (unit === "GBP_MINOR") return formatMinor(amount).replace("GBP ", "");
    return new Intl.NumberFormat("en-GB").format(amount);
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
    }

    public update(options: powerbi.extensibility.visual.VisualUpdateOptions): void {
        this.host.eventService?.renderingStarted(options);
        this.root.replaceChildren();
        this.host.tooltipService?.hide({immediately: true, isTouchEvent: false});
        try {
            const panel = parse(options.dataViews?.[0]);
            const add = (tag: string, text: string, parent: HTMLElement, cls = "") => {
                const el = document.createElement(tag);
                el.textContent = text; el.className = cls; parent.appendChild(el); return el;
            };
            add("style", styles, this.root);
            const card = add("article", "", this.root, `nexus-tieout ${panel.state.toLowerCase()}`);
            card.setAttribute("aria-live", "polite");
            if (this.host.colorPalette.isHighContrast) {
                const fore = this.host.colorPalette.foreground.value;
                for (const token of ["--ink", "--accent", "--muted", "--rule", "--bad", "--warn"])
                    card.style.setProperty(token, fore);
                card.style.setProperty("--paper", this.host.colorPalette.background.value);
            }
            add("div", "NEXUS / RECONCILIATION TIE-OUT", card, "eyebrow");
            add("h2", panel.label, card);
            add("p", panel.reason, card, "status");
            if (panel.grain) add("p", panel.grain, card, "grain");

            if (panel.byType.length) {
                const types = add("ul", "", card, "types");
                for (const entry of panel.byType) {
                    const li = add("li", "", types, entry.count ? "" : "none");
                    add("b", String(entry.count), li);
                    li.appendChild(document.createTextNode(entry.type.replaceAll("_", " ").toLowerCase()));
                }
            }
            if (panel.assertions.length) card.appendChild(this.table(panel));
            this.checks(panel, card, add);
            if (panel.note) add("p", panel.note, card, "note");
            if (panel.assertions.length) add("p", policy.independentReconciliationNote, card, "note");

            const details = add("details", "", card);
            add("summary", "Authority and evidence", details);
            for (const [label, key] of [["Assertion policy", "assertionPolicyRef"], ["Purpose", "purpose"],
                ["Source authority", "authority"], ["Delivery", "deliveryRef"],
                ["Delivery digest (declared)", "deliveryDigest"], ["Source digest", "sourceDigest"]])
                add("p", `${label}: ${panel.fields[key] || "Not supplied"}`, details);
            add("p", `Expected-operand evidence: not supplied for any assertion in this source`, details);

            const table = options.dataViews?.[0]?.table;
            if (this.host.hostCapabilities?.allowInteractions && table?.rows?.length) {
                const id = this.host.createSelectionIdBuilder().withTable(table, 0).createSelectionId();
                const button = add("button", "Select control evidence", card, "evidence") as HTMLButtonElement;
                button.type = "button";
                button.onclick = () => {void this.selection.select(id);};
                const menu = (x: number, y: number) => {void this.selection.showContextMenu(id, {x, y});};
                button.oncontextmenu = (e) => {e.preventDefault(); menu(e.clientX, e.clientY);};
                button.onkeydown = (e) => {
                    if (e.key === "ContextMenu" || (e.shiftKey && e.key === "F10")) {
                        e.preventDefault(); const b = button.getBoundingClientRect(); menu(b.x, b.y);
                    }
                };
            }
            this.host.eventService?.renderingFinished(options);
        } catch {
            this.root.replaceChildren();
            const error = document.createElement("p");
            error.textContent = "Panel withheld. Unable to validate the visual input.";
            this.root.appendChild(error);
            this.host.eventService?.renderingFailed(options, "Unable to validate input");
        }
    }

    private table(panel: Panel): HTMLTableElement {
        const table = document.createElement("table");
        const head = table.createTHead().insertRow();
        for (const [text, num] of [["Control", false], ["Type", false], ["Actual", true],
            ["Expected", true], ["Diff", true], ["Published", false], ["Replay", false]] as [string, boolean][]) {
            const th = document.createElement("th");
            th.scope = "col"; th.textContent = text; th.className = num ? "num" : "";
            head.appendChild(th);
        }
        const body = table.createTBody();
        for (const a of panel.assertions) body.appendChild(this.row(a));
        return table;
    }

    private row(a: Assertion): HTMLTableRowElement {
        const tr = document.createElement("tr");
        if (a.agrees === false) tr.className = "disagree";
        const cell = (text: string, cls = "") => {
            const td = tr.insertCell(); td.textContent = text; td.className = cls; return td;
        };
        const under = (parent: HTMLElement, text: string) => {
            const line = document.createElement("div");
            line.textContent = text;
            line.style.color = "var(--muted)";
            parent.appendChild(line);
        };
        const id = cell(a.id, "label");
        id.title = a.evidence;
        under(id, a.label);
        // The operator belongs with the type: it is what makes a nonzero
        // difference diagnostic rather than a failure.
        under(cell(a.type.replaceAll("_", " ").toLowerCase(), "type"), a.operator.replaceAll("_", " ").toLowerCase());
        cell(value(a.actual, a.unit), "num");
        cell(value(a.expected, a.unit), "num");
        // A threshold's nonzero difference is diagnostic, never a failure.
        cell(a.replayDifference === null ? "–" : value(a.replayDifference, a.unit), "num");
        cell(a.published, `result ${a.published === "PASS" ? "pass" : "fail"}`);
        cell(a.replay === "PASS" ? "PASS" : a.replay === "FAIL" ? "FAIL" : "UNASSESSED",
            `result ${a.replay === "PASS" ? "pass" : a.replay === "FAIL" ? "fail" : "unassessed"}`);
        return tr;
    }

    private checks(panel: Panel, card: HTMLElement,
                   add: (t: string, x: string, p: HTMLElement, c?: string) => HTMLElement): void {
        if (!panel.checks.length) return;
        const list = add("ul", "", card, "checks");
        for (const check of panel.checks) {
            const li = add("li", "", list);
            add("span", check.label, li, "name");
            add("span", check.detail, li, `result ${check.state.toLowerCase()}`);
        }
    }

    public getFormattingModel(): powerbi.visuals.FormattingModel { return {cards: []}; }
    public destroy(): void { this.root.replaceChildren(); }
}
