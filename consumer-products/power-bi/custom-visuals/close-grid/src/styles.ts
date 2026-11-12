export const styles=`
.nexus-close{--ink:#162c43;--paper:#fff;--accent:#16776e;--muted:#566879;--rule:#dde3e9;--bad:#a43a3a;--warn:#8a6228;box-sizing:border-box;height:100%;overflow:auto;background:var(--paper);color:var(--ink);border:1px solid var(--muted);border-top:4px solid var(--accent);border-radius:8px;padding:22px;font:14px/1.4 'Segoe UI',sans-serif}
.nexus-close.incomplete{--accent:#8a6228}
.nexus-close.blocked{--accent:#8a6228}
.nexus-close *{box-sizing:border-box}
.nexus-close .eyebrow{font-size:10px;letter-spacing:1.7px;color:var(--muted)}
.nexus-close h2{font-size:20px;font-weight:600;margin:8px 0}
.nexus-close .status{color:var(--accent);font-weight:600;margin:8px 0}
.nexus-close .context{color:var(--muted);font-size:12px;margin:0 0 12px}
.nexus-close .legend{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 12px;padding:0;list-style:none;font-size:11px;color:var(--muted)}
.nexus-close .legend li{display:flex;align-items:center;gap:5px}
.nexus-close table{width:100%;border-collapse:collapse;font-size:11px}
.nexus-close th{text-align:left;font-weight:600;padding:4px 10px 6px 0;border-bottom:1px solid var(--muted);white-space:nowrap}
.nexus-close th small{display:block;font-weight:400;color:var(--muted)}
.nexus-close td{padding:5px 10px 5px 0;border-bottom:1px solid var(--rule);vertical-align:top}
.nexus-close td.period{white-space:nowrap;font-variant-numeric:tabular-nums;font-weight:600}
.nexus-close .markers{display:flex;gap:4px;margin-bottom:3px}
.nexus-close .marker{display:inline-flex;align-items:center;gap:1px;border:1px solid var(--rule);border-radius:3px;padding:1px 4px;font-size:10px;line-height:1.3;background:var(--paper)}
.nexus-close .marker.satisfied{border-color:var(--accent);color:var(--accent)}
.nexus-close .marker.not_applicable{border-color:var(--rule);color:var(--muted)}
.nexus-close .marker.attention{border-color:var(--bad);color:var(--bad);font-weight:600}
.nexus-close .marker.unclassified{border-color:var(--warn);color:var(--warn);font-weight:600}
.nexus-close .close-state{color:var(--muted);font-size:10px;white-space:nowrap}
.nexus-close .close-state b{color:var(--ink);font-weight:600}
.nexus-close .evidence-flag{color:var(--bad);font-weight:600;font-size:10px}
.nexus-close button.cell{display:block;width:100%;text-align:left;background:none;border:0;padding:0;font:inherit;color:inherit;cursor:pointer}
.nexus-close .detail{margin:4px 0 0;padding:6px 8px;background:#f6f8f9;border-radius:4px;font-size:10px;color:var(--muted);overflow-wrap:anywhere}
.nexus-close .detail b{color:var(--ink)}
.nexus-close .tally{list-style:none;padding:0;margin:14px 0 0;border-top:1px solid var(--rule)}
.nexus-close .tally li{display:flex;gap:10px;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--rule);font-size:11px}
.nexus-close .tally .name{color:var(--muted)}
.nexus-close .checks{list-style:none;padding:0;margin:14px 0 0;border-top:1px solid var(--rule)}
.nexus-close .checks li{display:flex;gap:10px;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--rule);font-size:12px}
.nexus-close .checks .name{color:var(--muted)}
.nexus-close .checks .result{font-weight:600;text-align:right;overflow-wrap:anywhere}
.nexus-close .checks .tied{color:var(--accent)}.nexus-close .checks .broken{color:var(--bad)}.nexus-close .checks .unassessed{color:var(--warn)}
.nexus-close .note{color:var(--muted);font-size:11px;margin:10px 0 0}
.nexus-close details{font-size:11px;border-top:1px solid var(--muted);padding-top:12px;margin-top:16px;overflow-wrap:anywhere}
.nexus-close summary{cursor:pointer;font-weight:600}
.nexus-close :focus-visible{outline:3px solid var(--accent);outline-offset:2px}
`;
