import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render(path = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  const request = new Request(`http://localhost${path}`, {
    headers: { accept: "text/html" },
  });
  const environment = {
    ASSETS: {
      fetch: async () => new Response("Not found", { status: 404 }),
    },
  };
  const context = {
    waitUntil() {},
    passThroughOnException() {},
  };

  return typeof worker === "function"
    ? worker(request, environment, context)
    : worker.fetch(request, environment, context);
}

test("server-renders the bounded finance product shell", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.match(html, /<title>Nexus Technologies \| Financial Performance &amp; Assurance<\/title>/i);
  assert.match(html, /Synthetic data environment/);
  assert.match(html, /CFO Command Centre/);
  assert.match(html, /Financial state, operating drivers and assurance in one view/);
  assert.match(html, /RV-NEXUS-GROUP-2026-06@v1/);
  assert.match(html, /DuckDB-Wasm \/ governed Parquet/);
  assert.doesNotMatch(html, /codex-preview|react-loading-skeleton|Starter Project/i);
});

test("keeps the public client finite and free of authoritative data fixtures", async () => {
  const [api, experience, layout, packageJson] = await Promise.all([
    readFile(new URL("../app/lib/public-api.ts", import.meta.url), "utf8"),
    readFile(
      new URL("../app/components/ProductExperience.tsx", import.meta.url),
      "utf8",
    ),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../package.json", import.meta.url), "utf8"),
  ]);

  assert.match(api, /\/api\/v1\/demo/);
  assert.match(api, /\/api\/v1\/overview/);
  assert.match(api, /\/api\/v1\/atlas\/reporting-versions/);
  assert.match(api, /\/api\/v1\/traces\/reporting-values/);
  assert.match(api, /view_contract_version/);
  assert.match(api, /EXACT_ORIGINAL/);
  assert.doesNotMatch(api, /sqlite|fixture|journal_line|fetch\(["']https?:/i);
  assert.match(experience, /Content bytes verified/);
  assert.match(experience, /The interface adds no inferred edge/);
  assert.match(layout, /Nexus Technologies \| Financial Performance & Assurance/);
  assert.match(packageJson, /@duckdb\/duckdb-wasm/);
  assert.doesNotMatch(packageJson, /react-loading-skeleton|drizzle/);

  await assert.rejects(access(new URL("../app/_sites-preview", import.meta.url)));
});
