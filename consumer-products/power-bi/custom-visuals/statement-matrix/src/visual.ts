import type powerbi from "powerbi-visuals-api";
import {parse, formatMinor, type Line, type Statement} from "./contract";
import {styles} from "./styles";

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
        // Clear prior DOM, tooltips and values before evaluating new input.
        this.root.replaceChildren();
        this.host.tooltipService?.hide({immediately: true, isTouchEvent: false});
        try {
            const statement = parse(options.dataViews?.[0]);
            const add = (tag: string, text: string, parent: HTMLElement, cls = "") => {
                const el = document.createElement(tag);
                el.textContent = text; el.className = cls; parent.appendChild(el); return el;
            };
            add("style", styles, this.root);
            const card = add("article", "", this.root, `nexus-statement ${statement.state.toLowerCase()}`);
            card.setAttribute("aria-live", "polite");
            if (this.host.colorPalette.isHighContrast) {
                const fore = this.host.colorPalette.foreground.value;
                for (const token of ["--ink", "--accent", "--muted", "--rule", "--heavy"]) card.style.setProperty(token, fore);
                card.style.setProperty("--paper", this.host.colorPalette.background.value);
            }
            add("div", "NEXUS / STATUTORY STATEMENT", card, "eyebrow");
            add("h2", statement.label, card);
            add("p", statement.reason, card, "status");
            add("p", [statement.fields.scope, statement.fields.currency].filter(Boolean).join(" / ")
                + (statement.fields.authority ? ` | ${statement.fields.authority.replaceAll("_", " ")}` : ""), card, "context");

            if (statement.lines.length) card.appendChild(this.table(statement));
            if (statement.columns.length === 1)
                add("p", "Prior period comparison is unavailable for the first supported month.", card, "note");
            this.checks(statement, card, add);
            if (statement.note) add("p", statement.note, card, "note");

            const details = add("details", "", card);
            add("summary", "Authority and evidence", details);
            for (const [label, key] of [["Presentation policy", "presentationPolicyRef"], ["Purpose", "purpose"],
                ["Source authority", "authority"], ["Sign convention", "signConvention"],
                ["Evidence relation", "evidenceRef"], ["Evidence digest (source trial balance)", "evidenceDigest"],
                ["Delivery", "deliveryRef"], ["Delivery digest (declared)", "deliveryDigest"], ["Source digest", "sourceDigest"]])
                add("p", `${label}: ${statement.fields[key] || "Not supplied"}`, details);
            for (const column of statement.columns)
                add("p", `Column ${column.label}: ${column.version}`, details);

            const table = options.dataViews?.[0]?.table;
            if (this.host.hostCapabilities?.allowInteractions && table?.rows?.length && statement.columns.length) {
                const id = this.host.createSelectionIdBuilder().withTable(table, 0).createSelectionId();
                const button = add("button", "Select reporting evidence", card, "evidence") as HTMLButtonElement;
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
            error.textContent = "Statement withheld. Unable to validate the visual input.";
            this.root.appendChild(error);
            this.host.eventService?.renderingFailed(options, "Unable to validate input");
        }
    }

    /** Finance layout: scaffold order, indentation, rules, aligned numerals. */
    private table(statement: Statement): HTMLTableElement {
        const table = document.createElement("table");
        const head = table.createTHead().insertRow();
        const corner = document.createElement("th");
        corner.className = "label";
        corner.scope = "col";
        corner.textContent = statement.label;
        head.appendChild(corner);
        for (const column of statement.columns) {
            const th = document.createElement("th");
            th.scope = "col";
            th.textContent = column.label;
            head.appendChild(th);
        }
        const body = table.createTBody();
        for (const line of statement.lines) body.appendChild(this.line(line, statement.columns.length));
        return table;
    }

    private line(line: Line, columns: number): HTMLTableRowElement {
        const tr = document.createElement("tr");
        tr.className = `${line.kind.toLowerCase()} rule-${line.rule}`;
        const label = tr.insertCell();
        label.textContent = line.label;
        if (line.indent) label.style.paddingLeft = `${line.indent * 16}px`;
        if (line.kind === "SPACER") {
            const filler = tr.insertCell();
            filler.colSpan = columns;
            return tr;
        }
        for (const cell of line.cells) {
            const td = tr.insertCell();
            td.className = "amount";
            if (line.kind === "HEADER") { td.textContent = ""; continue; }
            if (cell.eligibility !== "ELIGIBLE") {
                td.textContent = "Withheld";
                td.className = "amount gated";
                td.title = cell.failureReason || "This line is not eligible for the selected purpose.";
                continue;
            }
            td.textContent = cell.amount === null ? "–" : formatMinor(cell.amount).replace("GBP ", "");
        }
        return tr;
    }

    private checks(statement: Statement, card: HTMLElement,
                   add: (t: string, x: string, p: HTMLElement, c?: string) => HTMLElement): void {
        if (!statement.checks.length) return;
        const list = add("ul", "", card, "checks");
        for (const check of statement.checks) {
            const li = add("li", "", list);
            add("span", check.label, li, "name");
            add("span", check.detail, li, `result ${check.state.toLowerCase()}`);
        }
    }

    public getFormattingModel(): powerbi.visuals.FormattingModel { return {cards: []}; }
    public destroy(): void { this.root.replaceChildren(); }
}
