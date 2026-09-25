import { mkdir } from "node:fs/promises";
import { resolve } from "node:path";

import { chromium } from "@playwright/test";

const baseUrl = process.env.SCREENSHOT_BASE_URL ?? "http://localhost:3000";
const outputDir = resolve(process.cwd(), "..", "docs", "public-release", "linkedin");

const captures = [
  ["01-cfo-command-centre.png", "/", "CFO Command Centre"],
  ["02-financial-performance.png", "/financial-performance", "Financial Performance"],
  ["03-cash-and-capital.png", "/cash-capital", "Cash & Capital"],
  ["04-revenue-and-saas.png", "/revenue-saas", "Revenue & SaaS Economics"],
  ["05-assurance-and-control-readiness.png", "/assurance", "Assurance & Control Readiness"],
  ["06-planning-and-valuation.png", "/planning-valuation", "Planning & Valuation"],
  ["07-assurance-casework.png", "/atlas/reporting/2026-06", "Assurance Casework"],
];

await mkdir(outputDir, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 1440, height: 810 },
  deviceScaleFactor: 1,
});

for (const [filename, route, heading] of captures) {
  await page.goto(`${baseUrl}${route}`, { waitUntil: "domcontentloaded" });
  await page.getByRole("heading", { level: 1, name: heading, exact: true }).waitFor({ timeout: 45_000 });

  if (route === "/atlas/reporting/2026-06") {
    await page.getByText("Runtime verified", { exact: true }).waitFor({ timeout: 45_000 });
  } else {
    await page.waitForFunction(
      () => document.body.textContent?.includes("Local query ready"),
      undefined,
      { timeout: 45_000 },
    );
  }

  await page.screenshot({
    path: resolve(outputDir, filename),
    fullPage: false,
  });
}

await browser.close();
console.log(`Captured ${captures.length} LinkedIn assets in ${outputDir}`);
