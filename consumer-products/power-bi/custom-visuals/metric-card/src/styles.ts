export const styles=`
.nexus-tile-card{--ink:#162c43;--paper:#fff;--accent:#16776e;--muted:#566879;--rule:#dde3e9;box-sizing:border-box;height:100%;overflow:auto;background:var(--paper);color:var(--ink);border:1px solid var(--rule);border-left:3px solid var(--accent);border-radius:6px;padding:8px 13px;font:14px/1.25 'Segoe UI',sans-serif;display:flex;flex-direction:column;gap:2px}
.nexus-tile-card.blocked{--accent:#8a6228}
.nexus-tile-card *{box-sizing:border-box}
.nexus-tile-card .label{font-size:11px;font-weight:600;color:var(--ink)}
.nexus-tile-card .value{font-size:clamp(18px,3.2vw,27px);font-weight:600;letter-spacing:-.6px;font-variant-numeric:tabular-nums;color:var(--ink);margin-top:1px;overflow-wrap:anywhere}
.nexus-tile-card.blocked .value{font-size:14px;color:var(--accent)}
.nexus-tile-card .context{font-size:9.5px;color:var(--muted);margin-top:auto;overflow-wrap:anywhere}
.nexus-tile-card .authority{font-size:8.5px;color:var(--muted);letter-spacing:.4px}
.nexus-tile-card .reason{font-size:10px;color:var(--accent)}
`;
