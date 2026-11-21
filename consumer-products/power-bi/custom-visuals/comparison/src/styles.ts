export const styles = `
.nexus-comparison{--ink:#162c43;--muted:#566879;--rule:#dce5ec;--paper:#fff;--accent:#16776e;--bad:#a43a3a;box-sizing:border-box;height:100%;overflow:auto;background:var(--paper);color:var(--ink);border:1px solid var(--rule);border-top:4px solid var(--accent);border-radius:8px;padding:18px 24px;font:14px/1.45 'Segoe UI',sans-serif}
.nexus-comparison h2{font-size:22px;margin:2px 0 10px;font-weight:600}
.nexus-comparison .context{font-size:12px;color:var(--muted);margin:0 0 4px}
.nexus-comparison .head{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
.nexus-comparison select{margin-left:8px;border:1px solid var(--muted);border-radius:4px;padding:5px;color:var(--ink);background:var(--paper);font:inherit}
.nexus-comparison .result{color:var(--accent);font-weight:600;margin:0 0 10px}
.nexus-comparison svg{display:block;width:min(100%,920px);margin:0 auto 10px;overflow:visible}
.nexus-comparison svg text{font:12px 'Segoe UI',sans-serif;fill:var(--muted);text-anchor:middle}
.nexus-comparison svg .value{font-weight:600;fill:var(--ink)}
.nexus-comparison svg .anchor{fill:var(--ink)}
.nexus-comparison svg .favourable{fill:var(--accent)}
.nexus-comparison svg .adverse{fill:var(--bad)}
.nexus-comparison svg .on-plan{fill:var(--muted)}
.nexus-comparison .axis{stroke:var(--rule)}
.nexus-comparison .connector{stroke:var(--muted);stroke-dasharray:4 3}
.nexus-comparison .table-wrap{overflow:auto}
.nexus-comparison table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums}
.nexus-comparison th,.nexus-comparison td{padding:7px 10px;border-bottom:1px solid var(--rule);text-align:left;vertical-align:top}
.nexus-comparison th{color:var(--muted);font-size:11px;white-space:nowrap}
.nexus-comparison .num{text-align:right;font-weight:600;white-space:nowrap}
.nexus-comparison th:not(:first-child){text-align:right}
.nexus-comparison details{overflow-wrap:anywhere;margin:8px 0}
.nexus-comparison td details{margin:0}
.nexus-comparison summary{cursor:pointer;color:var(--accent)}
.nexus-comparison dl{font-size:11px;margin:6px 0}
.nexus-comparison dt{font-weight:600}
.nexus-comparison dd{margin:0 0 6px;color:var(--muted)}
.nexus-comparison .snapshot-proof{border:1px solid var(--rule);border-radius:6px;margin-top:18px;padding:12px 14px}
.nexus-comparison .snapshot-proof dl{display:grid;grid-template-columns:minmax(120px,max-content) minmax(0,1fr);gap:6px 18px}
.nexus-comparison .snapshot-proof dd{margin:0}
.nexus-comparison :focus-visible{outline:2px solid var(--accent);outline-offset:2px}
`;
