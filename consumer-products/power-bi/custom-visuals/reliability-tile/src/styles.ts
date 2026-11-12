export const styles=`
.nexus-tile{--ink:#162c43;--paper:#fff;--accent:#16776e;--muted:#566879;box-sizing:border-box;height:100%;overflow:auto;background:var(--paper);color:var(--ink);border:1px solid var(--muted);border-top:4px solid var(--accent);border-radius:8px;padding:22px;font:14px/1.4 'Segoe UI',sans-serif}
.nexus-tile.withheld,.nexus-tile.invalid_context{--accent:#a43a3a}
.nexus-tile.unassessed,.nexus-tile.no_data{--accent:#8a6228}
.nexus-tile *{box-sizing:border-box}.nexus-tile .eyebrow{font-size:10px;letter-spacing:1.7px;color:var(--muted)}
.nexus-tile h2{font-size:22px;font-weight:600;margin:12px 0}.nexus-tile .amount{font-size:clamp(20px,2.4vw,34px);font-weight:600;letter-spacing:-.7px;font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.nexus-tile .status{color:var(--accent);font-weight:600;margin:12px 0}.nexus-tile .context,.nexus-tile .authority{color:var(--muted);font-size:12px}
.nexus-tile details{font-size:11px;border-top:1px solid var(--muted);padding-top:12px;margin-top:16px;overflow-wrap:anywhere}.nexus-tile summary{cursor:pointer;font-weight:600}
.nexus-tile .evidence{background:var(--paper);color:var(--ink);border:1px solid var(--muted);padding:7px 10px;margin-top:14px;border-radius:4px;cursor:pointer;font:inherit;font-size:12px}
.nexus-tile :focus-visible{outline:3px solid var(--accent);outline-offset:3px}
`;
