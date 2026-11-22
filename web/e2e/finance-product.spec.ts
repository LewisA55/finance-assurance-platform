import { expect, test } from "@playwright/test";

async function requireLocalRuntime(page: import("@playwright/test").Page): Promise<void> {
  await page.waitForFunction(
    () => document.body.textContent?.includes("Local query ready") || document.body.textContent?.includes("Local query unavailable"),
    undefined,
    { timeout: 35_000 },
  );
  if (await page.locator(".fi-runtime-button strong", { hasText: "Local query unavailable" }).isVisible()) {
    await page.locator(".fi-runtime-button").click();
    const note = await page.locator(".fi-runtime-error").textContent();
    throw new Error(note ?? "Local runtime failed without an error note");
  }
  await expect(page.getByText("Local query ready", { exact: true })).toBeVisible();
}

test("CFO view authenticates locally and exposes metric evidence", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "CFO Command Centre" })).toBeVisible();
  await expect(page.getByText("Financial state, operating drivers and assurance in one view.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Inspect Revenue evidence" })).toBeVisible();
  await expect(page.getByLabel("Integrated financial statement bridge")).toBeVisible();
  await requireLocalRuntime(page);

  await page.getByRole("button", { name: "Inspect Revenue evidence" }).click();
  await expect(page.getByRole("heading", { name: "Revenue authority" })).toBeVisible();
  await expect(page.getByText("Selected metric", { exact: true })).toBeVisible();
});

test("historical reporting context becomes interactive after runtime verification", async ({ page }) => {
  await page.goto("/financial-performance");
  const period = page.getByLabel("Period");
  await requireLocalRuntime(page);
  await expect(period).toBeEnabled();
  await period.selectOption("2025-06");
  await expect(period).toHaveValue("2025-06");
});

test("Pythia preserves approval boundaries while publishing one viable draft DCF", async ({ page }) => {
  await page.goto("/planning-valuation");
  await requireLocalRuntime(page);
  await page.locator(".fi-scenario-switch").getByRole("button", { name: /BULL/ }).click();
  await expect(page.getByRole("heading", { name: "Terminal value supportable" })).toBeVisible();
  await expect(page.getByText("Economically viable; approval pending")).toBeVisible();
  await expect(page.getByRole("heading", { name: "11/11 Pythia validators pass" })).toBeVisible();
  await expect(page.getByText("Ready / draft", { exact: true })).toBeVisible();
});

test("assurance reporting hands off to casework and returns with context", async ({ page }) => {
  await page.goto("/assurance");
  await page.getByRole("link", { name: /Open assurance journeys/ }).click();
  await expect(page).toHaveURL(/\/atlas\/reporting\/2026-06/);
  await expect(page.getByRole("heading", { name: "Assurance Casework" })).toBeVisible();
  await expect(page.getByText("Runtime verified", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: /Return to assurance/ }).click();
  await expect(page).toHaveURL(/\/assurance$/);
});

test("casework overview contains each flagship journey once", async ({ page }) => {
  await page.goto("/casework");
  await expect(page.getByText("O-J02", { exact: true })).toHaveCount(1);
  await expect(page.getByText("Runtime verified", { exact: true })).toBeVisible();
});

test("transaction explorer finds exact records and preserves each case boundary", async ({ page }) => {
  await page.goto("/casework");
  await page.getByRole("link", { name: "Transaction explorer" }).click();
  const search = page.getByRole("searchbox", { name: "Search cases and evidence" });
  const revenueCase = page.getByRole("region", { name: "Missing subscription revenue" });
  const cashCase = page.getByRole("region", { name: "Cash applied to the wrong customer" });
  await expect(revenueCase.getByText("DECISION-C001@v1", { exact: true })).toBeVisible();
  await expect(cashCase.getByText("VERIFY-CT1@v1", { exact: true })).toBeVisible();

  await search.fill("pr-o2c-recog@v1");
  await expect(revenueCase).toBeVisible();
  await expect(cashCase).toHaveCount(0);
  await page.getByRole("link", { name: "Records in the restatement trace" }).click();
  await expect(page).toHaveURL(/#C-001-stage-\d+$/);
  await revenueCase.getByText(/Directed trace relationships/).click();
  await expect(revenueCase.locator(".explorer-edges > li").first()).toBeVisible();
  await expect(revenueCase.getByRole("link", { name: "Open governed decision" })).toHaveAttribute("href", /DECISION-C001%40v1$/);

  await search.fill("j-010");
  await expect(revenueCase).toHaveCount(0);
  await expect(cashCase.getByRole("heading", { name: "Reversal and replacement proof" })).toBeVisible();
  await expect(cashCase.getByRole("link", { name: "Open governed decision" })).toHaveCount(0);

  await search.fill("no-such-record");
  await expect(page.getByText("No matching cases.")).toBeVisible();
  await page.getByRole("button", { name: "Clear search" }).click();
  await expect(revenueCase).toBeVisible();
  await expect(cashCase).toBeVisible();
});

test("transaction explorer withholds an inconsistent case and keeps the other case available", async ({ page }) => {
  await page.route("**/api/v1/pythia/decisions/*", async (route) => {
    const response = await route.fetch();
    const json = await response.json();
    json.data.readiness_ref = "UNBOUND-READINESS@v1";
    await route.fulfill({ response, json });
  });

  await page.goto("/explorer");
  await expect(page.getByText(/Evidence unavailable for C-001/)).toBeVisible();
  await expect(page.getByRole("link", { name: "Open governed decision" })).toHaveCount(0);
  await expect(page.getByRole("link", { name: "Open correction integrity proof" })).toBeVisible();
});

test("period-close cockpit blocks unresolved and unsigned closes, then shows the simulated June posting", async ({ page }) => {
  await page.goto("/period-close");
  const close = page.getByRole("button", { name: "Attempt hard close" });
  const post = page.getByRole("button", { name: "Approve, post and rerun control" });
  const signOff = page.getByRole("button", { name: "Record reviewer sign-off" });
  const checklist = page.getByRole("region", { name: "Close checklist" });

  await expect(signOff).toBeDisabled();
  await close.click();
  await expect(page.getByRole("heading", { name: "Close blocked by an unresolved proposal" })).toBeVisible();
  await expect(page.getByText("Soft-closed", { exact: true })).toBeVisible();

  await post.click();
  await expect(checklist.getByText(/12\/12 posted.*GBP 0\.00 gap.*Pass/)).toBeVisible();
  await close.click();
  await expect(page.getByRole("heading", { name: "Close blocked pending reviewer sign-off" })).toBeVisible();
  await signOff.click();
  await close.click();
  await expect(page.getByRole("heading", { name: "June hard-closed after simulated posting" })).toBeVisible();
  await expect(page.getByText("GBP 110,000.00", { exact: true })).toBeVisible();
  await expect(close).toBeDisabled();
  await expect(post).toBeDisabled();

  await page.getByRole("link", { name: "Follow consequences in explorer" }).click();
  await expect(page).toHaveURL(/\/explorer\?close=resolved$/);
  await expect(page.getByRole("region", { name: "Period-close simulation" })).toContainText("In the recorded case, the gap was carried into June v1");
  const revenue = page.getByRole("region", { name: "Missing subscription revenue" });
  await expect(revenue.getByText("GBP 0.00", { exact: true })).toBeVisible();
});

test("period-close cockpit preserves the deferred gap and links to the recorded restatement", async ({ page }) => {
  await page.goto("/explorer");
  await page.getByRole("link", { name: "Simulate the June close" }).click();
  await page.getByRole("button", { name: "Authorise deferral" }).click();
  await page.getByRole("button", { name: "Record reviewer sign-off" }).click();
  await page.getByRole("button", { name: "Attempt hard close" }).click();
  await expect(page.getByRole("heading", { name: "June hard-closed with authorised deferral" })).toBeVisible();
  await expect(page.getByRole("region", { name: "Close checklist" })).toContainText(/11\/12 posted.*GBP 10,000\.00 gap.*Gap open/);
  await expect(page.getByText("GBP 120,000.00", { exact: true })).toBeVisible();

  await page.getByRole("link", { name: "Follow consequences in explorer" }).click();
  await expect(page.getByRole("region", { name: "Period-close simulation" })).toContainText("This matches the recorded C-001 path");
  await expect(page.getByRole("region", { name: "Missing subscription revenue" }).getByText("RV-2026-06@v2", { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("region", { name: "Cash applied to the wrong customer" }).getByRole("link", { name: "Open correction integrity proof" })).toBeVisible();
  await page.getByRole("link", { name: "Start a new close simulation" }).click();
  await expect(page.getByRole("region", { name: "Close checklist" })).toContainText("Submitted and unresolved");
});
