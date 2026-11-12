// Local renderer acceptance harness. Host services are mocked, never a Desktop pass.
import {Visual} from '../src/visual';
import policy from '../policy.json';
const values={REVENUE:228800965,CLOSING_CASH:308230185,ENDING_ARR:2680056468};
const host:any={hostCapabilities:{allowInteractions:true},createSelectionManager:()=>({select:()=>Promise.resolve(),showContextMenu:()=>Promise.resolve()}),
 createSelectionIdBuilder:()=>({withTable(){return this;},createSelectionId(){return {};}}),colorPalette:{isHighContrast:false},tooltipService:{hide(){}},eventService:{renderingStarted(){},renderingFinished(){},renderingFailed(){throw Error('Render failed');}}};
const tiles=Object.entries(policy.metrics).map(([id,m])=>{
 const root=document.createElement('div');root.style.height='540px';document.getElementById('tiles')!.appendChild(root);
 return {id,m,visual:new Visual({element:root,host} as any)};
});
function render(mode:string) {
 for(const {id,m,visual} of tiles){
  const row:Record<string,unknown>={claimKey:`${id}|RV-NEXUS-GROUP-2026-06@v1`,purpose:policy.purpose,authority:m.authority,deliveryRef:policy.deliveryRef,deliveryDigest:policy.deliveryDigest,sourceDigest:policy.sourceDigest,evidenceRef:`${m.table} / ${id} / RV-NEXUS-GROUP-2026-06@v1`,contextState:'VALID',metricId:id,metricLabel:m.label,unit:'GBP_MINOR',period:'2026-06',scope:'NEXUS-GROUP',version:'RV-NEXUS-GROUP-2026-06@v1',selectedPurpose:mode==='purpose'?'STATUTORY_SIGN_OFF':policy.purpose,reliabilityStatus:m.status,reliabilityPurpose:m.purpose,eligibilityState:mode==='eligible'?'ELIGIBLE':'WITHHELD',policyVersion:policy.version,readinessStatus:mode==='missing'?null:'READY',displayValue:mode==='eligible'?values[id as keyof typeof values]:null,expectedRowCount:1,failureReason:mode==='blocked'?'TEST FIXTURE: required evidence is incomplete.':null};
  const columns=Object.keys(row).map(role=>({displayName:role,roles:{[role]:true}}));
  visual.update({dataViews:[{metadata:{columns},table:{columns,rows:[Object.values(row)]}}],viewport:{width:400,height:540}} as any);
 }
}
document.querySelectorAll<HTMLButtonElement>('button[data-mode]').forEach(b=>b.onclick=()=>render(b.dataset.mode!));
render('eligible');
