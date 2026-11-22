import {test} from 'node:test';
import assert from 'node:assert/strict';
import {JSDOM} from 'jsdom';
import {parse,formatMinor} from '../src/contract';
import {Visual} from '../src/visual';
import policy from '../policy.json';

function view(changes:Record<string,unknown>={}) {
    const m=policy.metrics.REVENUE;
    const row={claimKey:'REVENUE|RV-NEXUS-GROUP-2026-06@v1',purpose:policy.purpose,authority:m.authority,
        deliveryRef:policy.deliveryRef,deliveryDigest:policy.deliveryDigest,sourceDigest:policy.sourceDigest,
        evidenceRef:'mart_financial_performance_monthly / RV-NEXUS-GROUP-2026-06@v1',contextState:'VALID',
        metricId:'REVENUE',metricLabel:'Revenue',unit:'GBP_MINOR',period:'2026-06',scope:'NEXUS-GROUP',version:'RV-NEXUS-GROUP-2026-06@v1',
        selectedPurpose:policy.purpose,reliabilityStatus:m.status,reliabilityPurpose:m.purpose,eligibilityState:'ELIGIBLE',
        policyVersion:policy.version,readinessStatus:'READY',displayValue:228800965,expectedRowCount:1,...changes};
    const columns=Object.keys(row).map(role=>({displayName:role,roles:{[role]:true}}));
    return {metadata:{columns},table:{columns,rows:[Object.values(row)]}} as any;
}
test('eligible and zero are values, blank is unavailable',()=>{
    assert.equal(parse(view()).value,228800965);
    assert.equal(parse(view({displayValue:0})).value,0);
    assert.equal(parse(view({displayValue:null})).state,'UNASSESSED');
    assert.equal(formatMinor(-101),'(GBP 1.01)');
});
for (const [name,fields] of Object.entries({
    purpose:{selectedPurpose:'STATUTORY_SIGN_OFF'},readiness:{readinessStatus:'NOT_READY',failureReason:'Missing evidence'},
    authority:{authority:'UNREVIEWED'},source:{sourceDigest:'sha256:wrong'},version:{version:'RV-NEXUS-GROUP-2026-06@v2'},
    scope:{scope:'NEXUS-US'},currency:{unit:'USD_MINOR'},policy:{policyVersion:'v99'},
    missing:{readinessStatus:null},blocked:{eligibilityState:'WITHHELD',failureReason:'C-001 recognition omitted'},
    reversal:{eligibilityState:'WITHHELD',failureReason:'CT-1 reversal not approved'},
    partial:{expectedRowCount:2},unsafe:{displayValue:Number.MAX_SAFE_INTEGER+1},conflict:{failureReason:'unexpected'}
})) test(`${name} fails closed even with a raw numeric value`,()=>{
    const r=parse(view(fields));assert.notEqual(r.state,'ELIGIBLE');assert.equal(r.value,undefined);
});
test('empty, duplicate, segmented and duplicate role input fail closed',()=>{
    assert.equal(parse().state,'NO_DATA');
    let v=view();v.table.rows.push(v.table.rows[0]);assert.equal(parse(v).value,undefined);
    v=view();v.metadata.segment={};assert.equal(parse(v).value,undefined);
    v=view();v.table.columns.push(v.table.columns[0]);v.table.rows[0].push('duplicate');assert.equal(parse(v).value,undefined);
});
test('all three controlled metric authority tuples pass',()=>{
    for(const [id,m] of Object.entries(policy.metrics)) assert.equal(parse(view({claimKey:`${id}|RV-NEXUS-GROUP-2026-06@v1`,metricId:id,metricLabel:m.label,authority:m.authority,reliabilityStatus:m.status,reliabilityPurpose:m.purpose})).state,'ELIGIBLE');
});
test('DOM clears stale value and never interprets labels as HTML',()=>{
    const dom=new JSDOM('<div id="root"></div>');
    globalThis.document=dom.window.document;
    const root=document.getElementById('root')!;
    let finished=0;
    const host:any={createSelectionManager:()=>({select:()=>Promise.resolve(),showContextMenu:()=>Promise.resolve()}),
        createSelectionIdBuilder:()=>({withTable(){return this;},createSelectionId(){return {};}}),
        colorPalette:{isHighContrast:false},tooltipService:{hide(){}},eventService:{renderingStarted(){},renderingFinished(){finished++;},renderingFailed(){throw new Error('Render failed');}}};
    const v=new Visual({element:root,host} as any);
    v.update({dataViews:[view()],viewport:{width:400,height:540}} as any);
    assert.match(root.textContent!,/2,288,009.65/);
    v.update({dataViews:[view({eligibilityState:'WITHHELD',failureReason:'Missing evidence',metricLabel:'<img src=x onerror=alert(1)>'})]} as any);
    assert.doesNotMatch(root.textContent!,/2,288,009.65/);
    assert.equal(root.querySelector('img'),null);
    assert.match(root.textContent!,/Metric identity or label/);
    v.update({dataViews:[]} as any);
    assert.doesNotMatch(root.textContent!,/Missing evidence|2,288,009.65/);
    assert.equal(finished,3);
});
