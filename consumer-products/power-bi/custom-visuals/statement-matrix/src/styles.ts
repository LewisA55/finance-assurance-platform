export const styles=`
.nexus-statement{--ink:#162c43;--paper:#fff;--accent:#16776e;--muted:#566879;--rule:#dde3e9;--heavy:#9aa7b4;box-sizing:border-box;height:100%;overflow:auto;background:var(--paper);color:var(--ink);border:1px solid var(--muted);border-top:4px solid var(--accent);border-radius:8px;padding:22px;font:14px/1.4 'Segoe UI',sans-serif}
.nexus-statement.broken{--accent:#a43a3a}
.nexus-statement.blocked{--accent:#8a6228}
.nexus-statement *{box-sizing:border-box}
.nexus-statement .eyebrow{font-size:10px;letter-spacing:1.7px;color:var(--muted)}
.nexus-statement h2{font-size:20px;font-weight:600;margin:8px 0}
.nexus-statement .status{color:var(--accent);font-weight:600;margin:8px 0}
.nexus-statement .context{color:var(--muted);font-size:12px;margin:0 0 12px}
.nexus-statement table{width:100%;border-collapse:collapse;font-size:12px}
.nexus-statement th{font-weight:600;text-align:right;padding:4px 0 6px;border-bottom:1px solid var(--heavy);white-space:nowrap}
.nexus-statement th.label{text-align:left}
.nexus-statement td{padding:3px 0;vertical-align:baseline}
.nexus-statement td.amount{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;padding-left:18px}
.nexus-statement tr.header td{font-weight:600;padding-top:10px;color:var(--ink)}
.nexus-statement tr.spacer td{padding:5px 0}
.nexus-statement tr.memo td{color:var(--muted);font-style:italic}
.nexus-statement tr.derived_subtotal td,.nexus-statement tr.supplied_total td{font-weight:600}
.nexus-statement tr.rule-single td{border-top:1px solid var(--rule)}
.nexus-statement tr.rule-double td{border-top:1px solid var(--heavy);box-shadow:inset 0 -3px 0 -2px var(--heavy)}
.nexus-statement td.gated{color:#a43a3a;font-weight:600}
.nexus-statement .checks{list-style:none;padding:0;margin:16px 0 0;border-top:1px solid var(--rule)}
.nexus-statement .checks li{display:flex;gap:10px;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--rule);font-size:12px}
.nexus-statement .checks .name{color:var(--muted)}
.nexus-statement .checks .result{font-weight:600;text-align:right;overflow-wrap:anywhere}
.nexus-statement .checks .tied{color:var(--accent)}.nexus-statement .checks .broken{color:#a43a3a}.nexus-statement .checks .unassessed{color:#8a6228}
.nexus-statement .note{color:var(--muted);font-size:11px;margin:12px 0 0}
.nexus-statement details{font-size:11px;border-top:1px solid var(--muted);padding-top:12px;margin-top:16px;overflow-wrap:anywhere}
.nexus-statement summary{cursor:pointer;font-weight:600}
.nexus-statement .evidence{background:var(--paper);color:var(--ink);border:1px solid var(--muted);padding:7px 10px;margin-top:14px;border-radius:4px;cursor:pointer;font:inherit;font-size:12px}
.nexus-statement :focus-visible{outline:3px solid var(--accent);outline-offset:3px}
`;
