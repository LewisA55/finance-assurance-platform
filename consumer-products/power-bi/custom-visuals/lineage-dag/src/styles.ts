export const styles=`
.nexus-lineage{--ink:#162c43;--paper:#fff;--accent:#16776e;--muted:#566879;--rule:#dde3e9;--bad:#a43a3a;--warn:#8a6228;box-sizing:border-box;height:100%;overflow:auto;background:var(--paper);color:var(--ink);border:1px solid var(--muted);border-top:4px solid var(--accent);border-radius:8px;padding:22px;font:14px/1.4 'Segoe UI',sans-serif}
.nexus-lineage.incomplete{--accent:#a43a3a}
.nexus-lineage.blocked{--accent:#8a6228}
.nexus-lineage *{box-sizing:border-box}
.nexus-lineage .eyebrow{font-size:10px;letter-spacing:1.7px;color:var(--muted)}
.nexus-lineage h2{font-size:20px;font-weight:600;margin:8px 0}
.nexus-lineage h3{font-size:12px;font-weight:600;margin:14px 0 6px;color:var(--muted);text-transform:uppercase;letter-spacing:.8px}
.nexus-lineage .status{color:var(--accent);font-weight:600;margin:8px 0}
.nexus-lineage .context{color:var(--muted);font-size:12px;margin:0 0 12px}
.nexus-lineage .search{width:100%;padding:6px 9px;border:1px solid var(--muted);border-radius:4px;font:inherit;font-size:12px;background:var(--paper);color:var(--ink)}
.nexus-lineage .nodes{display:flex;flex-wrap:wrap;gap:5px;margin:8px 0 0;padding:0;list-style:none;max-height:150px;overflow:auto}
.nexus-lineage .node{border:1px solid var(--rule);border-radius:3px;padding:3px 7px;font-size:11px;background:var(--paper);color:var(--ink);cursor:pointer;font-family:inherit}
.nexus-lineage .node.gold_model{border-color:var(--accent);color:var(--accent)}
.nexus-lineage .node.symbolic_collection{border-color:var(--warn);color:var(--warn)}
.nexus-lineage .node.boundary{border-style:dashed;color:var(--muted)}
.nexus-lineage .node[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.nexus-lineage .empty{color:var(--muted);font-size:11px;margin:6px 0}
.nexus-lineage svg{display:block;max-width:100%;margin-top:6px}
.nexus-lineage svg text{font:11px 'Segoe UI',sans-serif;fill:var(--ink)}
.nexus-lineage svg text.kind{font-size:9px;fill:var(--muted)}
.nexus-lineage svg rect{fill:var(--paper);stroke:var(--rule)}
.nexus-lineage svg rect.gold_model{stroke:var(--accent)}
.nexus-lineage svg rect.symbolic_collection{stroke:var(--warn);stroke-dasharray:4 2}
.nexus-lineage svg rect.boundary{stroke:var(--muted);stroke-dasharray:3 2}
.nexus-lineage svg rect.focus{fill:#f2f7f6;stroke:var(--ink);stroke-width:2}
.nexus-lineage svg path{fill:none;stroke:var(--muted)}
.nexus-lineage .detail{margin:8px 0 0;padding:8px 10px;background:#f6f8f9;border-radius:4px;font-size:11px;overflow-wrap:anywhere}
.nexus-lineage .detail p{margin:0 0 3px}
.nexus-lineage .detail b{color:var(--ink)}
.nexus-lineage .detail .symbolic{color:var(--warn);font-weight:600}
.nexus-lineage table{width:100%;border-collapse:collapse;font-size:11px;margin-top:6px}
.nexus-lineage th{text-align:left;font-weight:600;padding:4px 10px 5px 0;border-bottom:1px solid var(--muted);white-space:nowrap}
.nexus-lineage td{padding:3px 10px 3px 0;border-bottom:1px solid var(--rule);vertical-align:top}
.nexus-lineage td.kind{color:var(--muted);white-space:nowrap}
.nexus-lineage .tally,.nexus-lineage .checks{list-style:none;padding:0;margin:14px 0 0;border-top:1px solid var(--rule)}
.nexus-lineage .tally li,.nexus-lineage .checks li{display:flex;gap:10px;justify-content:space-between;padding:5px 0;border-bottom:1px solid var(--rule);font-size:12px}
.nexus-lineage .name{color:var(--muted)}
.nexus-lineage .result{font-weight:600;text-align:right;overflow-wrap:anywhere}
.nexus-lineage .tied{color:var(--accent)}.nexus-lineage .broken{color:var(--bad)}.nexus-lineage .unassessed{color:var(--warn)}
.nexus-lineage .note{color:var(--muted);font-size:11px;margin:10px 0 0}
.nexus-lineage details{font-size:11px;border-top:1px solid var(--muted);padding-top:12px;margin-top:16px;overflow-wrap:anywhere}
.nexus-lineage summary{cursor:pointer;font-weight:600}
.nexus-lineage :focus-visible{outline:3px solid var(--accent);outline-offset:2px}
`;
