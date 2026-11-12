import type powerbi from "powerbi-visuals-api";
import {parse, formatMinor, formatSignedMinor, running} from "./contract";
import {styles} from "./styles";

const SVG = "http://www.w3.org/2000/svg";
// The chart is drawn in real pixels for the delivered viewport, so label and
// value type stays at its intended size instead of scaling with a fixed box.
const CARD_PADDING = 44, MIN_WIDTH = 280, HEIGHT = 200, PAD_TOP = 24, PAD_BOTTOM = 44;

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
            const bridge = parse(options.dataViews?.[0]);
            const add = (tag: string, text: string, parent: HTMLElement, cls = "") => {
                const el = document.createElement(tag);
                el.textContent = text; el.className = cls; parent.appendChild(el); return el;
            };
            add("style", styles, this.root);
            const card = add("article", "", this.root, `nexus-bridge ${bridge.state.toLowerCase()}`);
            card.setAttribute("aria-live", "polite");
            if (this.host.colorPalette.isHighContrast) {
                const fore = this.host.colorPalette.foreground.value;
                for (const token of ["--ink", "--accent", "--muted", "--up", "--down"]) card.style.setProperty(token, fore);
                card.style.setProperty("--paper", this.host.colorPalette.background.value);
            }
            add("div", "NEXUS / ROLLFORWARD ASSURANCE", card, "eyebrow");
            add("h2", bridge.label, card);
            add("p", bridge.reason, card, "status");
            add("p", [bridge.fields.period, bridge.fields.scope, bridge.fields.currency].filter(Boolean).join(" / ")
                + (bridge.fields.authority ? ` | ${bridge.fields.authority.replaceAll("_", " ")}` : ""), card, "context");

            if (bridge.steps.length)
                card.appendChild(this.chart(bridge, Math.max(MIN_WIDTH, (options.viewport?.width ?? 640) - CARD_PADDING)));
            this.assertions(bridge, card, add);
            if (bridge.note) add("p", bridge.note, card, "note");

            const details = add("details", "", card);
            add("summary", "Authority and evidence", details);
            for (const [label, key] of [["Assertion policy", "assertionPolicyRef"], ["Purpose", "purpose"],
                ["Source authority", "authority"], ["Reporting version", "version"],
                ["Evidence relation / row", "evidenceRef"], ["Evidence digest", "evidenceDigest"],
                ["Delivery", "deliveryRef"], ["Delivery digest (declared)", "deliveryDigest"], ["Source digest", "sourceDigest"]])
                add("p", `${label}: ${bridge.fields[key] || "Not supplied"}`, details);

            const table = options.dataViews?.[0]?.table;
            if (this.host.hostCapabilities?.allowInteractions && table?.rows?.length && bridge.fields.version) {
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
            error.textContent = "Assertion withheld. Unable to validate the visual input.";
            this.root.appendChild(error);
            this.host.eventService?.renderingFailed(options, "Unable to validate input");
        }
    }

    /** Waterfall geometry. The closing bar is the published anchor, never a plug. */
    private chart(bridge: ReturnType<typeof parse>, width: number): SVGSVGElement {
        const bars = running(bridge.steps);
        const values = [0, ...bars.flatMap(b => [b.from, b.to])];
        const low = Math.min(...values), high = Math.max(...values);
        const span = high - low || 1;
        const plot = HEIGHT - PAD_TOP - PAD_BOTTOM;
        const y = (value: number) => PAD_TOP + ((high - value) / span) * plot;
        const slot = width / bars.length;
        const barWidth = Math.min(64, slot * 0.56);
        const wrapAt = Math.max(6, Math.floor(slot / 6));

        const node = <T extends SVGElement>(name: string, attrs: Record<string, string | number>, text?: string): T => {
            const el = document.createElementNS(SVG, name) as T;
            for (const [k, v] of Object.entries(attrs)) el.setAttribute(k, String(v));
            if (text !== undefined) el.textContent = text;
            return el;
        };
        const svg = node<SVGSVGElement>("svg", {width, height: HEIGHT, viewBox: `0 0 ${width} ${HEIGHT}`,
            role: "img", preserveAspectRatio: "xMidYMid meet"});
        svg.appendChild(node("title", {}, `${bridge.label}, ${bridge.steps.length} steps, ${bridge.reason}`));
        svg.appendChild(node("line", {class: "zero", x1: 0, x2: width, y1: y(0), y2: y(0)}));

        bars.forEach((bar, i) => {
            const centre = slot * (i + 0.5);
            const x = centre - barWidth / 2;
            const top = Math.min(y(bar.from), y(bar.to));
            const height = Math.max(2, Math.abs(y(bar.to) - y(bar.from)));
            const anchor = bar.step.kind === "OPENING" || bar.step.kind === "CLOSING" || bar.step.kind === "SUBTOTAL";
            const cls = anchor ? "bar-anchor" : bar.step.amount < 0 ? "bar-down" : "bar-up";
            svg.appendChild(node("rect", {class: cls, x, y: top, width: barWidth, height, rx: 1}));
            if (i < bars.length - 1)
                svg.appendChild(node("line", {class: "connector", x1: x + barWidth, x2: centre + slot - barWidth / 2, y1: y(bar.to), y2: y(bar.to)}));
            svg.appendChild(node("text", {class: "value", x: centre, y: top - 6, "text-anchor": "middle"},
                anchor ? formatMinor(bar.step.amount).replace("GBP ", "") : formatSignedMinor(bar.step.amount)));
            const label = node<SVGTextElement>("text", {class: "label", x: centre, y: HEIGHT - PAD_BOTTOM + 18, "text-anchor": "middle"});
            // Wrap the step label rather than overflow the slot.
            bar.step.label.split(" ").reduce<string[]>((lines, word) => {
                const last = lines[lines.length - 1];
                if (last && (last + " " + word).length <= wrapAt) lines[lines.length - 1] = last + " " + word;
                else lines.push(word);
                return lines;
            }, []).slice(0, 2).forEach((line, n) => label.appendChild(node("tspan", {x: centre, dy: n ? 12 : 0}, line)));
            svg.appendChild(label);
        });
        return svg;
    }

    /** Three claims, kept separate: replayed arithmetic, coverage, supplied source. */
    private assertions(bridge: ReturnType<typeof parse>, card: HTMLElement,
                       add: (t: string, x: string, p: HTMLElement, c?: string) => HTMLElement): void {
        const list = add("ul", "", card, "assertions");
        const row = (name: string, result: string, tone: "pass" | "fail" | "none") => {
            const li = add("li", "", list);
            add("span", name, li, "name");
            add("span", result, li, `result ${tone}`);
        };
        const tie = bridge.closure;
        row("Arithmetic tie-out",
            tie.state === "UNASSESSED" ? tie.reason
                : tie.state === "TIED" ? `Closes at ${formatMinor(tie.supplied)}`
                : `Breaks by ${formatSignedMinor(tie.difference)}`,
            tie.state === "TIED" ? "pass" : tie.state === "BROKEN" ? "fail" : "none");
        row("Component coverage",
            bridge.coverage.state === "COMPLETE" ? `${bridge.steps.length} steps, no failed components` : bridge.coverage.reason,
            bridge.coverage.state === "COMPLETE" ? "pass" : "fail");
        const source = bridge.source;
        row("Supplied source assertion",
            source.difference !== null ? `${source.status ? source.status + ", " : ""}difference ${formatSignedMinor(source.difference)}`
                : source.status ? source.status : "Not supplied for this schedule",
            source.agrees === null ? "none" : source.agrees ? "pass" : "fail");
        if (source.agrees === false)
            row("Disagreement", "Replayed arithmetic and the supplied assertion differ. Neither overwrites the other.", "fail");
    }

    public getFormattingModel(): powerbi.visuals.FormattingModel { return {cards: []}; }
    public destroy(): void { this.root.replaceChildren(); }
}
