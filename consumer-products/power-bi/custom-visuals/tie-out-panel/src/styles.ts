export const styles=`
.nexus-tieout{--ink:#162c43;--paper:#fff;--accent:#16776e;--muted:#566879;--rule:#dde3e9;--bad:#a43a3a;--warn:#8a6228;box-sizing:border-box;height:100%;overflow:auto;background:var(--paper);color:var(--ink);border:1px solid var(--muted);border-top:4px solid var(--accent);border-radius:8px;padding:22px;font:14px/1.4 'Segoe UI',sans-serif}
.nexus-tieout.disagreed{--accent:#a43a3a}
.nexus-tieout.blocked{--accent:#8a6228}
.nexus-tieout *{box-sizing:border-box}
.nexus-tieout .eyebrow{font-size:10px;letter-spacing:1.7px;color:var(--muted)}
.nexus-tieout h2{font-size:20px;font-weight:600;margin:8px 0}
.nexus-tieout .status{color:var(--accent);font-weight:600;margin:8px 0}
.nexus-tieout .grain{color:var(--muted);font-size:12px;margin:0 0 12px}
.nexus-tieout .types{display:flex;flex-wrap:wrap;gap:8px;margin:0 0 14px;padding:0;list-style:none}
.nexus-tieout .types li{border:1px solid var(--rule);border-radius:4px;padding:5px 9px;font-size:11px;color:var(--muted)}
.nexus-tieout .types b{color:var(--ink);font-size:13px;margin-right:6px;font-variant-numeric:tabular-nums}
.nexus-tieout .types li.none b{color:var(--warn)}
.nexus-tieout table{width:100%;border-collapse:collapse;font-size:11px}
.nexus-tieout th{text-align:left;font-weight:600;padding:4px 8px 6px 0;border-bottom:1px solid var(--muted);white-space:nowrap}
.nexus-tieout th.num,.nexus-tieout td.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;padding-right:0;padding-left:12px}
.nexus-tieout th.num+th:not(.num),.nexus-tieout td.num+td:not(.num){padding-left:12px}
.nexus-tieout td{padding:4px 8px 4px 0;border-bottom:1px solid var(--rule);vertical-align:top}
.nexus-tieout td.label{min-width:140px}
.nexus-tieout td.type{color:var(--muted);white-space:nowrap}
.nexus-tieout td.result{font-weight:600;white-space:nowrap}
.nexus-tieout .pass{color:var(--accent)}.nexus-tieout .fail{color:var(--bad)}.nexus-tieout .unassessed{color:var(--warn)}
.nexus-tieout tr.disagree td{background:#fbf2f2}
.nexus-tieout .checks{list-style:none;padding:0;margin:16px 0 0;border-top:1px solid var(--rule)}
.nexus-tieout .checks li{display:flex;gap:10px;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--rule);font-size:12px}
.nexus-tieout .checks .name{color:var(--muted)}
.nexus-tieout .checks .result{font-weight:600;text-align:right;overflow-wrap:anywhere}
.nexus-tieout .checks .tied{color:var(--accent)}.nexus-tieout .checks .broken{color:var(--bad)}.nexus-tieout .checks .unassessed{color:var(--warn)}
.nexus-tieout .note{color:var(--muted);font-size:11px;margin:12px 0 0}
.nexus-tieout details{font-size:11px;border-top:1px solid var(--muted);padding-top:12px;margin-top:16px;overflow-wrap:anywhere}
.nexus-tieout summary{cursor:pointer;font-weight:600}
.nexus-tieout .evidence{background:var(--paper);color:var(--ink);border:1px solid var(--muted);padding:7px 10px;margin-top:14px;border-radius:4px;cursor:pointer;font:inherit;font-size:12px}
.nexus-tieout :focus-visible{outline:3px solid var(--accent);outline-offset:3px}
`;
