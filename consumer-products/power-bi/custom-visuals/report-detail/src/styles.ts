export const styles = `
.nexus-detail{--ink:#162c43;--muted:#566879;--line:#dce5ec;--paper:#fff;--wash:#f3f7fa;--accent:#16776e;--red:#a43a3a;--amber:#8a6228;--series2:#285881;--series3:#8a6228;box-sizing:border-box;height:100%;overflow:auto;background:var(--paper);color:var(--ink);border:1px solid var(--line);border-top:3px solid var(--accent);border-radius:6px;font:12px/1.45 'Segoe UI',sans-serif}
.nexus-detail table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
.nexus-detail th,.nexus-detail td{padding:8px 9px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
.nexus-detail th{position:sticky;top:0;z-index:1;background:var(--wash);color:var(--ink);white-space:nowrap;font-weight:600}
.nexus-detail td{overflow-wrap:anywhere}
.nexus-detail tr:nth-child(even){background:var(--wash)}
.nexus-detail tr:hover{box-shadow:inset 3px 0 var(--accent)}
.nexus-detail tr.selected{box-shadow:inset 3px 0 var(--accent),inset 0 -2px var(--accent)}
.nexus-detail .numeric{text-align:right;white-space:nowrap}
.nexus-detail button{background:none;border:0;padding:0;text-align:left;color:var(--accent);font:inherit;text-decoration:underline;text-underline-offset:2px;cursor:pointer}
.nexus-detail button:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.nexus-detail .status{display:inline-block;border:1px solid currentColor;border-radius:10px;padding:0 7px;font-size:10px;font-weight:600}
.nexus-detail .good{color:var(--accent)} .nexus-detail .bad{color:var(--red)} .nexus-detail .pending{color:var(--amber)}
.nexus-detail .notice{padding:8px 14px;color:var(--muted)}
.nexus-detail .legend{display:flex;list-style:none;margin:8px 10px;padding:0;gap:14px;font-variant-numeric:tabular-nums}
.nexus-detail .legend li{padding-left:7px;border-left:3px solid var(--series)}
.nexus-detail .legend strong{color:var(--ink);display:block;font-size:13px}
.nexus-detail svg{width:calc(100% - 16px);margin:0 8px;display:block;font-variant-numeric:tabular-nums}
.nexus-detail svg text{fill:var(--muted);font-size:10px}
.nexus-detail .axis{stroke:var(--line)}
.nexus-detail .series0{--series:var(--accent)}
.nexus-detail .series1{--series:var(--series2)}
.nexus-detail .series2{--series:var(--series3)}
.nexus-detail .trend{stroke:var(--series);fill:none;stroke-width:2}
.nexus-detail .trend.series1{stroke-dasharray:6 3}.nexus-detail .trend.series2{stroke-dasharray:2 2}
.nexus-detail .point{fill:var(--series);stroke:var(--paper);stroke-width:1}
.nexus-detail .point[tabindex]{cursor:pointer}
.nexus-detail .point:hover,.nexus-detail .point:focus-visible{stroke-width:3;stroke:var(--ink)}
`;
