import assert from "node:assert/strict";
import { readFile, readdir } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const webRoot = fileURLToPath(new URL("..", import.meta.url));

async function render(route) {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("phase6", `${process.pid}-${Date.now()}-${route}`);
  const { default: worker } = await import(workerUrl.href);
  const request = new Request(`http://localhost${route}`, {
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

async function sourceFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const nested = await Promise.all(
    entries.map(async (entry) => {
      const target = path.join(directory, entry.name);
      if (entry.isDirectory()) return sourceFiles(target);
      return /\.(?:ts|tsx|css)$/.test(entry.name) ? [target] : [];
    }),
  );
  return nested.flat();
}

test("renders every finite browser route with the shared accessible shell", async () => {
  const routes = [
    "/",
    "/financial-performance",
    "/cash-capital",
    "/revenue-saas",
    "/assurance",
    "/planning-valuation",
    "/product-guide",
    "/atlas/reporting/2026-06",
    "/atlas/reporting/2026-06/RV-2026-06%40v2",
    "/trace/reporting/RV-2026-06%40v2/subscription_revenue_minor",
    "/hermes/reconciliation/RECON-C001%40v1",
    "/argus/exceptions/EXC-C001%40v1",
    "/aegis/cases/ISSUE-C001%40v1",
    "/aegis/readiness/RV-2026-06%40v2",
    "/pythia/decisions/DECISION-C001%40v1",
    "/corrections/VERIFY-CT1%40v1",
  ];

  for (const route of routes) {
    const response = await render(route);
    assert.equal(response.status, 200, route);
    const html = await response.text();
    assert.match(html, /<html[^>]+lang="en"/i, route);
    if (["/", "/financial-performance", "/cash-capital", "/revenue-saas", "/assurance", "/planning-valuation", "/product-guide"].includes(route)) {
      assert.match(html, /href="#finance-main"[^>]*>\s*Skip to (?:finance content|product guide)/i, route);
      assert.match(html, /<nav[^>]+aria-label="(?:Finance product navigation|Management report pages)"/i, route);
      assert.match(html, /<main[^>]+id="finance-main"[^>]+tabindex="-1"/i, route);
      assert.match(html, /Synthetic data environment/i, route);
    } else {
      assert.match(html, /href="#main-content"[^>]*>\s*Skip to main content/i, route);
      assert.match(html, /<nav[^>]+aria-label="Primary navigation"/i, route);
      assert.match(html, /<main[^>]+id="main-content"[^>]+tabindex="-1"[^>]+aria-busy="true"/i, route);
      assert.match(html, /role="status"[^>]+aria-live="polite"/i, route);
      assert.match(html, /All entities, transactions, evidence, and decisions are fictional/i, route);
    }
  }
});

test("uses native read-only navigation and decodes every dynamic subject", async () => {
  const componentFiles = [
    "ProductExperience.tsx",
    "BrokenQuarterViews.tsx",
    "DecisionCorrectionViews.tsx",
  ];
  const components = (
    await Promise.all(
      componentFiles.map((file) =>
        readFile(path.join(webRoot, "app", "components", file), "utf8"),
      ),
    )
  ).join("\n");
  const decisionPage = await readFile(
    path.join(webRoot, "app", "pythia", "decisions", "[decisionRef]", "page.tsx"),
    "utf8",
  );
  const correctionPage = await readFile(
    path.join(webRoot, "app", "corrections", "[correctionRef]", "page.tsx"),
    "utf8",
  );

  assert.doesNotMatch(components, /from ["']next\/link["']/);
  assert.match(components, /function Link\(\{ children, \.\.\.props \}/);
  assert.match(components, /<code>\{data\.decision_ref\}<\/code>/);
  assert.match(decisionPage, /decisionRef: decodeURIComponent\(decisionRef\)/);
  assert.match(correctionPage, /correctionRef: decodeURIComponent\(correctionRef\)/);
});

test("keeps responsive, contrast, motion, and keyboard hardening explicit", async () => {
  const css = await readFile(path.join(webRoot, "app", "globals.css"), "utf8");

  assert.match(css, /:focus-visible\s*\{[^}]*outline:\s*3px solid var\(--amber\)/s);
  assert.match(css, /@media \(prefers-reduced-motion: reduce\)/);
  assert.match(css, /@media \(prefers-contrast: more\)/);
  assert.match(css, /@media \(forced-colors: active\)/);
  assert.match(css, /grid-template-columns:\s*repeat\(6, minmax\(48px, 1fr\)\)/);
  assert.match(css, /\.module-link\s*\{[^}]*min-width:\s*48px;[^}]*min-height:\s*48px;/s);
  assert.match(css, /\.screen-stack\s*\{[^}]*min-width:\s*0;/s);
  assert.match(css, /\.screen-stack > \*\s*\{[^}]*min-width:\s*0;/s);
  assert.match(css, /--muted:\s*#5b6965/);
});

test("has no paid-service, secret, telemetry, or external runtime boundary", async () => {
  const files = await sourceFiles(path.join(webRoot, "app"));
  const corpus = (await Promise.all(files.map((file) => readFile(file, "utf8")))).join("\n");
  const packageJson = JSON.parse(
    await readFile(path.join(webRoot, "package.json"), "utf8"),
  );

  assert.doesNotMatch(corpus, /fetch\(\s*["']https?:\/\//i);
  assert.doesNotMatch(corpus, /OPENAI_API_KEY|ANTHROPIC_API_KEY|SENTRY_DSN|POSTHOG|GOOGLE_ANALYTICS/i);
  assert.deepEqual(Object.keys(packageJson.dependencies).sort(), [
    "@duckdb/duckdb-wasm",
    "react",
    "react-dom",
  ]);
  assert.match(corpus, /fetch\(\s*`\$\{path\}\?\$\{/);
});

test("publishes portfolio metadata without claiming hosted authority", async () => {
  const layout = await readFile(path.join(webRoot, "app", "layout.tsx"), "utf8");
  const experience = await readFile(
    path.join(webRoot, "app", "components", "ProductExperience.tsx"),
    "utf8",
  );

  assert.match(layout, /Nexus Technologies \| Financial Performance & Assurance/);
  assert.match(layout, /browser-local CFO finance intelligence product/i);
  assert.match(layout, /openGraph/);
  assert.match(layout, /summary_large_image/);
  assert.match(layout, /NEXT_PUBLIC_SITE_URL/);
  assert.match(layout, /url: "\/og\.png"/);
  assert.match(experience, /no paid API required/i);
  assert.match(experience, /Exact-original reads/);
  assert.doesNotMatch(layout, /x-forwarded-host|x-forwarded-proto/i);
});

test("derives the build identity from versioned deployable inputs", async () => {
  const config = await readFile(path.join(webRoot, "next.config.ts"), "utf8");

  assert.match(config, /function deterministicBuildId\(\)/);
  assert.match(config, /createHash\("sha256"\)/);
  assert.match(config, /deploymentId:\s*buildIdentity/);
  assert.match(config, /generateBuildId:\s*async \(\) => buildIdentity/);
  for (const input of ["app", "public", "package-lock.json", "next.config.ts"]) {
    assert.match(config, new RegExp(`"${input.replace(".", "\\.")}"`));
  }
  assert.doesNotMatch(config, /randomUUID|Date\.now|Math\.random/);
});
