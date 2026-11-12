import type powerbi from "powerbi-visuals-api";
import {parse,formatMinor} from "./contract";
import {styles} from "./styles";

export class Visual implements powerbi.extensibility.visual.IVisual {
    private root: HTMLElement;
    private host: powerbi.extensibility.visual.IVisualHost;
    private selection: powerbi.extensibility.ISelectionManager;
    constructor(options?:powerbi.extensibility.visual.VisualConstructorOptions) {
        if (!options) throw new Error("Power BI host options are required.");
        this.root=options.element;
        this.host=options.host;
        this.selection=this.host.createSelectionManager();
    }
    public update(options:powerbi.extensibility.visual.VisualUpdateOptions):void {
        this.host.eventService?.renderingStarted(options);
        // Remove prior DOM, tooltip closures and value before evaluating new input.
        this.root.replaceChildren();
        this.host.tooltipService?.hide({immediately:true,isTouchEvent:false});
        try {
            const tile=parse(options.dataViews?.[0]);
            const add=(tag:string,text:string,parent:HTMLElement,cls="")=>{
                const el=document.createElement(tag);el.textContent=text;el.className=cls;parent.appendChild(el);return el;
            };
            add("style",styles,this.root);
            const card=add("article","",this.root,`nexus-tile ${tile.state.toLowerCase()}`);
            card.setAttribute("aria-live","polite");
            if (this.host.colorPalette.isHighContrast) {
                card.style.setProperty("--ink",this.host.colorPalette.foreground.value);
                card.style.setProperty("--paper",this.host.colorPalette.background.value);
                card.style.setProperty("--accent",this.host.colorPalette.foreground.value);
                card.style.setProperty("--muted",this.host.colorPalette.foreground.value);
            }
            add("div","NEXUS / GOVERNED METRIC",card,"eyebrow");
            add("h2",tile.label,card);
            add("div",tile.state==="ELIGIBLE"?formatMinor(tile.value!):"Value withheld",card,"amount");
            add("p",tile.reason,card,"status");
            add("p",[tile.fields.period,tile.fields.scope].filter(Boolean).join(" / "),card,"context");
            add("p",tile.fields.authority?.replaceAll("_"," ") || "Authority unavailable",card,"authority");
            const details=add("details","",card);
            add("summary","Authority and evidence",details);
            for (const [label,key] of [["Selected purpose","selectedPurpose"],["Source purpose","reliabilityPurpose"],["Readiness","readinessStatus"],["Reporting version","version"],["Policy","policyVersion"],["Evidence relation / row","evidenceRef"],["Evidence digest","evidenceDigest"],["Delivery","deliveryRef"],["Delivery digest (declared)","deliveryDigest"],["Source digest","sourceDigest"]])
                add("p",`${label}: ${tile.fields[key] || "Not supplied"}`,details);
            const table=options.dataViews?.[0]?.table;
            if (this.host.hostCapabilities?.allowInteractions && table?.rows?.length===1 && tile.fields.version) {
                const id=this.host.createSelectionIdBuilder().withTable(table,0).createSelectionId();
                const button=add("button","Select reporting evidence",card,"evidence") as HTMLButtonElement;
                button.type="button";
                button.onclick=()=>{void this.selection.select(id);};
                const menu=(x:number,y:number)=>{void this.selection.showContextMenu(id,{x,y});};
                button.oncontextmenu=(e)=>{e.preventDefault();menu(e.clientX,e.clientY);};
                button.onkeydown=(e)=>{if(e.key==="ContextMenu" || e.shiftKey&&e.key==="F10"){e.preventDefault();const b=button.getBoundingClientRect();menu(b.x,b.y);}};
            }
            this.host.eventService?.renderingFinished(options);
        } catch {
            this.root.replaceChildren();
            const error=document.createElement("p");error.textContent="Value withheld. Unable to validate the visual input.";this.root.appendChild(error);
            this.host.eventService?.renderingFailed(options,"Unable to validate input");
        }
    }
    public getFormattingModel():powerbi.visuals.FormattingModel { return {cards:[]}; }
    public destroy():void {this.root.replaceChildren();}
}
