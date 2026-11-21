import type powerbi from "powerbi-visuals-api";
import {parse} from "./contract";
import {styles} from "./styles";
import policy from "../policy.json";

export class Visual implements powerbi.extensibility.visual.IVisual {
    private root: HTMLElement;
    private host: powerbi.extensibility.visual.IVisualHost;
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
            const tile = parse(options.dataViews?.[0]);
            const add = (tag: string, text: string, parent: HTMLElement, cls = "") => {
                const el = document.createElement(tag);
                el.textContent = text; el.className = cls; parent.appendChild(el); return el;
            };
            add("style", styles, this.root);
            const card = add("article", "", this.root, `nexus-tile-card ${tile.state.toLowerCase()}`);
            card.setAttribute("aria-live", "polite");
            if (this.host.colorPalette.isHighContrast) {
                const fore = this.host.colorPalette.foreground.value;
                for (const token of ["--ink", "--accent", "--muted", "--rule"]) card.style.setProperty(token, fore);
                card.style.setProperty("--paper", this.host.colorPalette.background.value);
            }
            add("div", tile.label, card, "label");
            const value = add("div", tile.display, card, "value");
            if (tile.reason) add("div", tile.reason, card, "reason");
            if (tile.context) add("div", tile.context, card, "context");
            if (tile.authority) add("div", tile.authority.replaceAll("_", " "), card, "authority");

            // The headline is abbreviated, so the exact figure and the tile's
            // standing stay one hover away rather than being lost.
            const detail = [tile.exact ? `Exact: ${tile.exact}` : "", tile.caption, tile.context, tile.authority.replaceAll("_", " "),
                policy.disclaimer].filter(Boolean).join("\n");
            card.title = detail;
            value.setAttribute("aria-label", `${tile.label}: ${tile.exact || tile.display}`);

            this.host.eventService?.renderingFinished(options);
        } catch {
            this.root.replaceChildren();
            const error = document.createElement("p");
            error.textContent = "Value withheld. Unable to validate the tile input.";
            this.root.appendChild(error);
            this.host.eventService?.renderingFailed(options, "Unable to validate input");
        }
    }

    public getFormattingModel(): powerbi.visuals.FormattingModel { return {cards: []}; }
    public destroy(): void { this.root.replaceChildren(); }
}
