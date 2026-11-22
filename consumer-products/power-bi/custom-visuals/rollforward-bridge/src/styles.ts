export const styles=`
.nexus-bridge{--ink:#162c43;--paper:#fff;--accent:#16776e;--muted:#566879;--rule:#dde3e9;--up:#16776e;--down:#a43a3a;box-sizing:border-box;height:100%;overflow:auto;background:var(--paper);color:var(--ink);border:1px solid var(--muted);border-top:4px solid var(--accent);border-radius:8px;padding:22px;font:14px/1.4 'Segoe UI',sans-serif}
.nexus-bridge.broken{--accent:#a43a3a}
.nexus-bridge.blocked{--accent:#8a6228}
.nexus-bridge *{box-sizing:border-box}
.nexus-bridge .eyebrow{font-size:10px;letter-spacing:1.7px;color:var(--muted)}
.nexus-bridge h2{font-size:20px;font-weight:600;margin:8px 0}
.nexus-bridge .status{color:var(--accent);font-weight:600;margin:8px 0}
.nexus-bridge .context{color:var(--muted);font-size:12px;margin:0 0 10px}
.nexus-bridge svg{display:block;max-width:100%;font-variant-numeric:tabular-nums}
.nexus-bridge svg .bar-up{fill:var(--up)}.nexus-bridge svg .bar-down{fill:var(--down)}.nexus-bridge svg .bar-anchor{fill:#162c43}
.nexus-bridge svg .connector{stroke:var(--muted);stroke-width:1;stroke-dasharray:3 2}
.nexus-bridge svg .zero{stroke:var(--rule);stroke-width:1}
.nexus-bridge svg .value{font-size:10px;fill:var(--ink)}
.nexus-bridge svg .label{font-size:10px;fill:var(--muted)}
.nexus-bridge .assertions{list-style:none;padding:0;margin:12px 0 0;border-top:1px solid var(--rule)}
.nexus-bridge .assertions li{display:flex;gap:10px;justify-content:space-between;padding:6px 0;border-bottom:1px solid var(--rule);font-size:12px}
.nexus-bridge .assertions .name{color:var(--muted)}
.nexus-bridge .assertions .result{font-weight:600;text-align:right;overflow-wrap:anywhere}
.nexus-bridge .assertions .pass{color:var(--up)}.nexus-bridge .assertions .fail{color:var(--down)}.nexus-bridge .assertions .none{color:#8a6228}
.nexus-bridge .note{color:var(--muted);font-size:11px;margin:14px 0 0}
.nexus-bridge details{font-size:11px;border-top:1px solid var(--muted);padding-top:12px;margin-top:16px;overflow-wrap:anywhere}
.nexus-bridge summary{cursor:pointer;font-weight:600}
.nexus-bridge .evidence{background:var(--paper);color:var(--ink);border:1px solid var(--muted);padding:7px 10px;margin-top:14px;border-radius:4px;cursor:pointer;font:inherit;font-size:12px}
.nexus-bridge :focus-visible{outline:3px solid var(--accent);outline-offset:3px}
`;
