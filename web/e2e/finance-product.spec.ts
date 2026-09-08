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
