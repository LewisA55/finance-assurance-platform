"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AssuranceReadinessView } from "./AssuranceReadinessView";
import { CashCapitalView } from "./CashCapitalView";
import { FinancialPerformanceView } from "./FinancialPerformanceView";
import { PlanningValuationView } from "./PlanningValuationView";
import { RevenueSaasView } from "./RevenueSaasView";
import type {
  AssuranceWarmSnapshot,
  AssuranceWorkspace,
  CashCapitalWarmSnapshot,
  CashCapitalWorkspace,
  CommandCentreRow,
  FinancialPerformanceRow,
  FinancialPerformanceWorkspace,
  FinanceRuntimeManifest,
  FinanceWorkspace,
  PlanningValuationWarmSnapshot,
  PlanningValuationWorkspace,
  RevenueSaasWarmSnapshot,
  RevenueSaasWorkspace,
} from "../../lib/finance-runtime/contracts";

type RuntimeStatus = "starting" | "ready" | "error";
type FinanceView = "command-centre" | "financial-performance" | "cash-capital" | "revenue-saas" | "assurance" | "planning-valuation";

const number = new Intl.NumberFormat("en-GB", { maximumFractionDigits: 0 });

function formatMoney(minor: number | null | undefined): string {
  if (minor == null) return "-";
  const pounds = minor / 100;
  const absolute = Math.abs(pounds);
  const [scaled, suffix] = absolute >= 1_000_000_000
    ? [pounds / 1_000_000_000, "bn"]
    : absolute >= 1_000_000
      ? [pounds / 1_000_000, "m"]
      : absolute >= 1_000
        ? [pounds / 1_000, "k"]
        : [pounds, ""];
  const formatted = Math.abs(scaled).toFixed(1).replace(/\.0$/, "");
  return `${scaled < 0 ? "-" : ""}£${formatted}${suffix}`;
}

function formatPercent(basisPoints: number | null | undefined): string {
  return basisPoints == null ? "-" : `${(basisPoints / 100).toFixed(1)}%`;
}

function formatPeriod(periodId: string): string {
  const [year, month] = periodId.split("-").map(Number);
  return new Intl.DateTimeFormat("en-GB", {
    month: "long",
    year: "numeric",
  }).format(new Date(Date.UTC(year, month - 1, 1)));
}

function percentageChange(current: number, prior: number | undefined): number | null {
  if (prior == null || prior === 0) return null;
  return (current - prior) / Math.abs(prior);
}

function formatChange(change: number | null): string {
  if (change == null) return "No prior comparison";
  const sign = change > 0 ? "+" : "";
  return `${sign}${(change * 100).toFixed(1)}% vs prior month`;
}

function toneForChange(change: number | null, inverse = false): string {
  if (change == null || Math.abs(change) < 0.0005) return "neutral";
  const favourable = inverse ? change < 0 : change > 0;
  return favourable ? "positive" : "negative";
}

function shortDigest(digest: string): string {
  return `${digest.slice(0, 18)}...${digest.slice(-8)}`;
}

function managementSignal(row: CommandCentreRow): {
  title: string;
  detail: string;
  tone: "watch" | "stable";
} {
  if (row.ebitda_minor < 0 && row.revenue_minor > 0) {
    return {
      title: "Revenue scale is not converting into operating profitability.",
      detail: `${formatMoney(row.revenue_minor)} monthly revenue and ${formatPercent(row.gross_margin_bps)} gross margin are offset by an EBITDA loss of ${formatMoney(Math.abs(row.ebitda_minor))}.`,
      tone: "watch",
    };
  }
  return {
    title: "Operating performance remains within the governed presentation boundary.",
    detail: `The selected period reports ${formatMoney(row.revenue_minor)} revenue and ${formatPercent(row.ebitda_margin_bps)} EBITDA margin.`,
    tone: "stable",
  };
}

function TrendChart({ rows }: { rows: CommandCentreRow[] }) {
  const width = 760;
  const height = 260;
  const padding = { left: 52, right: 20, top: 22, bottom: 34 };
  const allValues = rows.flatMap((row) => [row.revenue_minor, row.ebitda_minor]);
  const minimum = Math.min(...allValues, 0);
  const maximum = Math.max(...allValues, 1);
  const range = maximum - minimum || 1;
  const x = (index: number) =>
    padding.left +
    (index / Math.max(rows.length - 1, 1)) * (width - padding.left - padding.right);
  const y = (value: number) =>
    padding.top +
    ((maximum - value) / range) * (height - padding.top - padding.bottom);
  const path = (key: "revenue_minor" | "ebitda_minor") =>
    rows
      .map((row, index) => `${index === 0 ? "M" : "L"}${x(index)},${y(row[key])}`)
      .join(" ");
  const zeroY = y(0);

  return (
    <div className="fi-chart-wrap" aria-label="Monthly revenue and EBITDA trend">
      <svg className="fi-chart" viewBox={`0 0 ${width} ${height}`} role="img">
        <title>Revenue and EBITDA, January 2021 to June 2026</title>
        {[0, 0.25, 0.5, 0.75, 1].map((step) => {
          const lineY = padding.top + step * (height - padding.top - padding.bottom);
          return (
            <line
              key={step}
              x1={padding.left}
              x2={width - padding.right}
              y1={lineY}
              y2={lineY}
              className="fi-chart-grid"
            />
          );
        })}
        <line
          x1={padding.left}
          x2={width - padding.right}
          y1={zeroY}
          y2={zeroY}
          className="fi-chart-zero"
        />
        <path d={path("revenue_minor")} className="fi-chart-line fi-revenue-line" />
        <path d={path("ebitda_minor")} className="fi-chart-line fi-ebitda-line" />
        <text x={padding.left} y={height - 10} className="fi-chart-label">
          Jan 2021
        </text>
        <text x={width - padding.right} y={height - 10} textAnchor="end" className="fi-chart-label">
          Jun 2026
        </text>
        <text x={padding.left - 8} y={padding.top + 4} textAnchor="end" className="fi-chart-label">
          {formatMoney(maximum)}
        </text>
        <text x={padding.left - 8} y={height - padding.bottom} textAnchor="end" className="fi-chart-label">
          {formatMoney(minimum)}
        </text>
      </svg>
      <div className="fi-chart-legend" aria-hidden="true">
        <span><i className="fi-legend-line revenue" /> Revenue</span>
        <span><i className="fi-legend-line ebitda" /> EBITDA</span>
      </div>
    </div>
  );
}

interface KpiProps {
  label: string;
  value: string;
  change?: number | null;
  inverse?: boolean;
  context: string;
}

function KpiCard({ label, value, change, inverse, context }: KpiProps) {
  return (
    <article className="fi-kpi-card">
      <p>{label}</p>
      <strong>{value}</strong>
      <div className="fi-kpi-meta">
        {change === undefined ? (
          <span className="neutral">{context}</span>
        ) : (
          <span className={toneForChange(change, inverse)}>{formatChange(change)}</span>
        )}
        <small>{context}</small>
      </div>
    </article>
  );
}

function NavItem({
  label,
  code,
  href,
  active,
}: {
  label: string;
  code: string;
  href?: string;
  active?: boolean;
}) {
  const content = (
    <>
      <span>{code}</span>
      <strong>{label}</strong>
      {!href && <small>Next slice</small>}
    </>
  );
  if (href) {
    return <Link className={`fi-nav-item${active ? " active" : ""}`} href={href} aria-current={active ? "page" : undefined}>{content}</Link>;
  }
  return (
    <button className="fi-nav-item" type="button" disabled>
      {content}
    </button>
  );
}

interface FinanceIntelligenceExperienceProps {
  initialSnapshot: CommandCentreRow;
  initialManifest: FinanceRuntimeManifest;
  initialFinancialPerformance?: FinancialPerformanceRow[];
  initialCashCapital?: CashCapitalWarmSnapshot;
  initialRevenueSaas?: RevenueSaasWarmSnapshot;
  initialAssurance?: AssuranceWarmSnapshot;
  initialPlanningValuation?: PlanningValuationWarmSnapshot;
  initialView?: FinanceView;
}

export function FinanceIntelligenceExperience({
  initialSnapshot,
  initialManifest,
  initialFinancialPerformance = [],
  initialCashCapital,
  initialRevenueSaas,
  initialAssurance,
  initialPlanningValuation,
  initialView = "command-centre",
}: FinanceIntelligenceExperienceProps) {
  const [workspace, setWorkspace] = useState<FinanceWorkspace | null>(null);
  const [financialWorkspace, setFinancialWorkspace] =
    useState<FinancialPerformanceWorkspace | null>(null);
  const [cashCapitalWorkspace, setCashCapitalWorkspace] =
    useState<CashCapitalWorkspace | null>(null);
  const [revenueSaasWorkspace, setRevenueSaasWorkspace] =
    useState<RevenueSaasWorkspace | null>(null);
  const [assuranceWorkspace, setAssuranceWorkspace] =
    useState<AssuranceWorkspace | null>(null);
  const [planningValuationWorkspace, setPlanningValuationWorkspace] =
    useState<PlanningValuationWorkspace | null>(null);
  const [warmSnapshot, setWarmSnapshot] = useState<CommandCentreRow | null>(initialSnapshot);
  const [warmFinancialPerformance, setWarmFinancialPerformance] =
    useState<FinancialPerformanceRow[]>(initialFinancialPerformance);
  const [warmCashCapital, setWarmCashCapital] =
    useState<CashCapitalWarmSnapshot | null>(initialCashCapital ?? null);
  const [warmRevenueSaas, setWarmRevenueSaas] =
    useState<RevenueSaasWarmSnapshot | null>(initialRevenueSaas ?? null);
  const [warmAssurance, setWarmAssurance] =
    useState<AssuranceWarmSnapshot | null>(initialAssurance ?? null);
  const [warmPlanningValuation, setWarmPlanningValuation] =
    useState<PlanningValuationWarmSnapshot | null>(initialPlanningValuation ?? null);
  const [manifest, setManifest] = useState<FinanceRuntimeManifest | null>(initialManifest);
  const [selectedPeriod, setSelectedPeriod] = useState<string | null>(initialSnapshot.period_id);
  const [selectedScope, setSelectedScope] = useState("NEXUS-GROUP");
  const [runtimeStatus, setRuntimeStatus] = useState<RuntimeStatus>("starting");
  const [runtimeError, setRuntimeError] = useState<string | null>(null);
  const [drawerOpen, setDrawerOpen] = useState(false);

  useEffect(() => {
    let current = true;
    const manifestRequest = fetch("/finance-data/runtime-manifest.json").then(
      async (response) => {
        if (!response.ok) throw new Error("C2 runtime manifest unavailable");
        return (await response.json()) as FinanceRuntimeManifest;
      },
    );

    if (initialView === "financial-performance") {
      Promise.all([
        fetch("/finance-data/latest-financial-performance.json").then(async (response) => {
          if (!response.ok) throw new Error("C2 financial-performance snapshot unavailable");
          return (await response.json()) as FinancialPerformanceRow[];
        }),
        manifestRequest,
      ])
        .then(([rows, runtimeManifest]) => {
          if (!current) return;
          setWarmFinancialPerformance(rows);
          setManifest(runtimeManifest);
          const latest = rows.find((row) => row.scope_id === "NEXUS-GROUP") ?? rows.at(-1);
          if (latest) setSelectedPeriod(latest.period_id);
        })
        .catch((error: unknown) => {
          if (current) setRuntimeError(error instanceof Error ? error.message : "Data unavailable");
        });

      import("../../lib/finance-runtime/queries")
        .then(({ loadFinancialPerformanceWorkspace }) =>
          loadFinancialPerformanceWorkspace(),
        )
        .then((value) => {
          if (!current) return;
          setFinancialWorkspace(value);
          setManifest(value.manifest);
          setSelectedPeriod((period) =>
            period ??
            value.financialPerformance
              .filter((row) => row.scope_id === "NEXUS-GROUP")
              .at(-1)?.period_id ??
            null,
          );
          setRuntimeStatus("ready");
        })
        .catch((error: unknown) => {
          if (!current) return;
          setRuntimeStatus("error");
          setRuntimeError(
            error instanceof Error ? error.message : "The local analytical runtime failed",
          );
        });
    } else if (initialView === "cash-capital") {
      Promise.all([
        fetch("/finance-data/latest-cash-capital.json").then(async (response) => {
          if (!response.ok) throw new Error("C2 cash-capital snapshot unavailable");
          return (await response.json()) as CashCapitalWarmSnapshot;
        }),
        manifestRequest,
      ])
        .then(([snapshot, runtimeManifest]) => {
          if (!current) return;
          setWarmCashCapital(snapshot);
          setManifest(runtimeManifest);
          const latest = snapshot.cashFlows.find((row) => row.scope_id === "NEXUS-GROUP") ?? snapshot.cashFlows.at(-1);
          if (latest) setSelectedPeriod(latest.period_id);
        })
        .catch((error: unknown) => {
          if (current) setRuntimeError(error instanceof Error ? error.message : "Data unavailable");
        });

      import("../../lib/finance-runtime/queries")
        .then(({ loadCashCapitalWorkspace }) => loadCashCapitalWorkspace())
        .then((value) => {
          if (!current) return;
          setCashCapitalWorkspace(value);
          setManifest(value.manifest);
          setSelectedPeriod((period) =>
            period ?? value.cashFlows.filter((row) => row.scope_id === "NEXUS-GROUP").at(-1)?.period_id ?? null,
          );
          setRuntimeStatus("ready");
        })
        .catch((error: unknown) => {
          if (!current) return;
          setRuntimeStatus("error");
          setRuntimeError(error instanceof Error ? error.message : "The local analytical runtime failed");
        });
    } else if (initialView === "revenue-saas") {
      Promise.all([
        fetch("/finance-data/latest-revenue-saas.json").then(async (response) => {
          if (!response.ok) throw new Error("C2 revenue and SaaS snapshot unavailable");
          return (await response.json()) as RevenueSaasWarmSnapshot;
        }),
        manifestRequest,
      ])
        .then(([snapshot, runtimeManifest]) => {
          if (!current) return;
          setWarmRevenueSaas(snapshot);
          setManifest(runtimeManifest);
          const latest = snapshot.revenueWaterfalls.at(-1);
          if (latest) setSelectedPeriod(latest.period_id);
        })
        .catch((error: unknown) => {
          if (current) setRuntimeError(error instanceof Error ? error.message : "Data unavailable");
        });

      import("../../lib/finance-runtime/queries")
        .then(({ loadRevenueSaasWorkspace }) => loadRevenueSaasWorkspace())
        .then((value) => {
          if (!current) return;
          setRevenueSaasWorkspace(value);
          setManifest(value.manifest);
          setSelectedPeriod((period) => period ?? value.revenueWaterfalls.at(-1)?.period_id ?? null);
          setRuntimeStatus("ready");
        })
        .catch((error: unknown) => {
          if (!current) return;
          setRuntimeStatus("error");
          setRuntimeError(error instanceof Error ? error.message : "The local analytical runtime failed");
        });
    } else if (initialView === "planning-valuation") {
      Promise.all([
        fetch("/finance-data/latest-planning-valuation.json").then(async (response) => {
          if (!response.ok) throw new Error("Pythia planning and valuation snapshot unavailable");
          return (await response.json()) as PlanningValuationWarmSnapshot;
        }),
        manifestRequest,
      ])
        .then(([snapshot, runtimeManifest]) => {
          if (!current) return;
          setWarmPlanningValuation(snapshot);
          setManifest(runtimeManifest);
        })
        .catch((error: unknown) => {
          if (current) setRuntimeError(error instanceof Error ? error.message : "Data unavailable");
        });

      import("../../lib/finance-runtime/queries")
        .then(({ loadPlanningValuationWorkspace }) => loadPlanningValuationWorkspace())
        .then((value) => {
          if (!current) return;
          setPlanningValuationWorkspace(value);
          setManifest(value.manifest);
          setRuntimeStatus("ready");
        })
        .catch((error: unknown) => {
          if (!current) return;
          setRuntimeStatus("error");
          setRuntimeError(error instanceof Error ? error.message : "The local analytical runtime failed");
        });
    } else if (initialView === "assurance") {
      Promise.all([
        fetch("/finance-data/latest-assurance.json").then(async (response) => {
          if (!response.ok) throw new Error("C2 assurance snapshot unavailable");
          return (await response.json()) as AssuranceWarmSnapshot;
        }),
        manifestRequest,
      ])
        .then(([snapshot, runtimeManifest]) => {
          if (!current) return;
          setWarmAssurance(snapshot);
          setManifest(runtimeManifest);
          const latest = snapshot.reportingVersions.find((row) => row.scope_id === "NEXUS-GROUP") ?? snapshot.reportingVersions.at(-1);
          if (latest) setSelectedPeriod(latest.period_id);
        })
        .catch((error: unknown) => {
          if (current) setRuntimeError(error instanceof Error ? error.message : "Data unavailable");
        });

      import("../../lib/finance-runtime/queries")
        .then(({ loadAssuranceWorkspace }) => loadAssuranceWorkspace())
        .then((value) => {
          if (!current) return;
          setAssuranceWorkspace(value);
          setManifest(value.manifest);
          setSelectedPeriod((period) => period ?? value.reportingVersions.filter((row) => row.scope_id === "NEXUS-GROUP").at(-1)?.period_id ?? null);
          setRuntimeStatus("ready");
        })
        .catch((error: unknown) => {
          if (!current) return;
          setRuntimeStatus("error");
          setRuntimeError(error instanceof Error ? error.message : "The local analytical runtime failed");
        });
    } else {
      Promise.all([
        fetch("/finance-data/latest-command-centre.json").then(async (response) => {
          if (!response.ok) throw new Error("C2 command-centre snapshot unavailable");
          return (await response.json()) as CommandCentreRow;
        }),
        manifestRequest,
      ])
        .then(([snapshot, runtimeManifest]) => {
          if (!current) return;
          setWarmSnapshot(snapshot);
          setManifest(runtimeManifest);
          setSelectedPeriod(snapshot.period_id);
        })
        .catch((error: unknown) => {
          if (current) setRuntimeError(error instanceof Error ? error.message : "Data unavailable");
        });

      import("../../lib/finance-runtime/queries")
        .then(({ loadFinanceWorkspace }) => loadFinanceWorkspace())
        .then((value) => {
          if (!current) return;
          setWorkspace(value);
          setManifest(value.manifest);
          setSelectedPeriod((period) => period ?? value.commandCentre.at(-1)?.period_id ?? null);
          setRuntimeStatus("ready");
        })
        .catch((error: unknown) => {
          if (!current) return;
          setRuntimeStatus("error");
          setRuntimeError(
            error instanceof Error ? error.message : "The local analytical runtime failed",
          );
        });
    }
    return () => {
      current = false;
    };
  }, [initialView]);

  const series = useMemo(
    () => workspace?.commandCentre ?? (warmSnapshot ? [warmSnapshot] : []),
    [workspace, warmSnapshot],
  );
  const selectedIndex = useMemo(() => {
    if (series.length === 0) return -1;
    if (!selectedPeriod) return series.length - 1;
    const index = series.findIndex((row) => row.period_id === selectedPeriod);
    return index < 0 ? series.length - 1 : index;
  }, [selectedPeriod, series]);
  const selected = selectedIndex >= 0 ? series[selectedIndex] : initialSnapshot;
  const prior = selectedIndex > 0 ? series[selectedIndex - 1] : undefined;

  const performanceSeries = useMemo(
    () => financialWorkspace?.financialPerformance ?? warmFinancialPerformance,
    [financialWorkspace, warmFinancialPerformance],
  );
  const scopedPerformanceSeries = useMemo(
    () => performanceSeries.filter((row) => row.scope_id === selectedScope),
    [performanceSeries, selectedScope],
  );
  const selectedFinancial = useMemo(() => {
    const exact = scopedPerformanceSeries.find((row) => row.period_id === selectedPeriod);
    return exact ?? scopedPerformanceSeries.at(-1) ?? performanceSeries.at(-1) ?? null;
  }, [performanceSeries, scopedPerformanceSeries, selectedPeriod]);
  const cashFlows = useMemo(
    () => cashCapitalWorkspace?.cashFlows ?? warmCashCapital?.cashFlows ?? [],
    [cashCapitalWorkspace, warmCashCapital],
  );
  const scopedCashFlows = useMemo(
    () => cashFlows.filter((row) => row.scope_id === selectedScope),
    [cashFlows, selectedScope],
  );
  const selectedCashFlow = useMemo(() => {
    const exact = scopedCashFlows.find((row) => row.period_id === selectedPeriod);
    return exact ?? scopedCashFlows.at(-1) ?? cashFlows.at(-1) ?? null;
  }, [cashFlows, scopedCashFlows, selectedPeriod]);
  const revenueWaterfalls = useMemo(
    () => revenueSaasWorkspace?.revenueWaterfalls ?? warmRevenueSaas?.revenueWaterfalls ?? [],
    [revenueSaasWorkspace, warmRevenueSaas],
  );
  const selectedRevenue = useMemo(() => {
    const exact = revenueWaterfalls.find((row) => row.period_id === selectedPeriod);
    return exact ?? revenueWaterfalls.at(-1) ?? null;
  }, [revenueWaterfalls, selectedPeriod]);
  const assuranceVersions = useMemo(
    () => assuranceWorkspace?.reportingVersions ?? warmAssurance?.reportingVersions ?? [],
    [assuranceWorkspace, warmAssurance],
  );
  const scopedAssuranceVersions = useMemo(
    () => assuranceVersions.filter((row) => row.scope_id === selectedScope),
    [assuranceVersions, selectedScope],
  );
  const selectedAssuranceVersion = useMemo(() => {
    const exact = scopedAssuranceVersions.find((row) => row.period_id === selectedPeriod);
    return exact ?? scopedAssuranceVersions.at(-1) ?? assuranceVersions.at(-1) ?? null;
  }, [assuranceVersions, scopedAssuranceVersions, selectedPeriod]);
  const planningForecasts = planningValuationWorkspace?.annualForecasts ?? warmPlanningValuation?.annualForecasts ?? [];
  const selectedPlanningForecast = planningForecasts.find(
    (row) => row.scenario_code === "BASE" && row.year === "2026",
  ) ?? planningForecasts[0] ?? null;
  const contextRow = initialView === "financial-performance"
    ? selectedFinancial
    : initialView === "cash-capital"
      ? selectedCashFlow
      : initialView === "revenue-saas" && selectedRevenue
        ? { ...selectedRevenue, scope_id: "NEXUS-GROUP" }
      : initialView === "assurance" && selectedAssuranceVersion
        ? {
            ...selectedAssuranceVersion,
            currency: "GBP",
            value_authority: "REPORTING_VERSION_CONTROL_STATE",
          }
      : initialView === "planning-valuation" && selectedPlanningForecast
        ? {
            ...selectedPlanningForecast,
            period_id: "2026-06",
            scope_id: "NEXUS-GROUP",
            reporting_version_ref: selectedPlanningForecast.actuals_reporting_version_ref,
            source_package_digest: selectedPlanningForecast.source_data_digest,
            _source_data_ref: manifest?.pythiaRef ?? "PYTHIA-D6@v1",
          }
      : selected;

  if (!contextRow) {
    return (
      <main className="fi-unavailable">
        <p className="fi-eyebrow">Nexus Technologies / Finance intelligence</p>
        <h1>The governed finance view is unavailable.</h1>
        <p>{runtimeError ?? "Preparing the local analytical package."}</p>
        {runtimeStatus === "error" && (
          <button type="button" onClick={() => window.location.reload()}>
            Retry local query
          </button>
        )}
      </main>
    );
  }

  const signal = managementSignal(selected);
  const metricsReady = workspace?.metricReadiness.filter(
    (row) => row.readiness_status === "READY",
  ).length;
  const controlsPassed = workspace?.readinessControls.filter(
    (row) => row.result_status === "PASS",
  ).length;
  const activeWorkspace = initialView === "financial-performance" ? financialWorkspace : initialView === "cash-capital" ? cashCapitalWorkspace : workspace;
  const populationsMatch = activeWorkspace?.populations.every((population) => {
    const contract = activeWorkspace.manifest.runtimeTables.find(
      (table) => table.tableName === population.table_name,
    );
    return contract?.expectedRows === population.actual_rows;
  });

  return (
    <div className="fi-app">
      <a className="fi-skip-link" href="#finance-main">Skip to finance content</a>
      <aside className="fi-sidebar">
        <Link className="fi-brand" href="/" aria-label="Nexus Technologies finance home">
          <span className="fi-brand-mark">N</span>
          <span>
            <strong>Nexus</strong>
            <small>Technologies</small>
          </span>
        </Link>

        <nav className="fi-nav" aria-label="Finance product navigation">
          <p>Management reporting</p>
          <NavItem code="01" label="CFO command centre" href="/" active={initialView === "command-centre"} />
          <NavItem code="02" label="Financial performance" href="/financial-performance" active={initialView === "financial-performance"} />
          <NavItem code="03" label="Cash & capital" href="/cash-capital" active={initialView === "cash-capital"} />
          <NavItem code="04" label="Revenue & SaaS" href="/revenue-saas" active={initialView === "revenue-saas"} />
          <NavItem code="05" label="Assurance" href="/assurance" active={initialView === "assurance"} />
          <NavItem code="06" label="Planning & valuation" href="/planning-valuation" active={initialView === "planning-valuation"} />
        </nav>

        <div className="fi-sidebar-lower">
          <Link href="/product-guide" className="fi-evidence-link fi-guide-link">
            <span>Product guide</span>
            <strong>Purpose, architecture & trust</strong>
          </Link>
          <Link href="/atlas/reporting/2026-06" className="fi-evidence-link">
            <span>Assurance Casework</span>
            <strong>Open assurance journeys</strong>
          </Link>
          <button className="fi-runtime-button" type="button" onClick={() => setDrawerOpen(true)}>
            <i className={runtimeStatus} />
            <span role="status" aria-live="polite">
              <strong>{runtimeStatus === "ready" ? "Local query ready" : runtimeStatus === "error" ? "Local query unavailable" : "Local query starting"}</strong>
              <small>DuckDB-Wasm / governed Parquet</small>
            </span>
          </button>
        </div>
      </aside>

      <div className="fi-stage">
        <div className="fi-synthetic-strip">
          <strong>Synthetic data environment</strong>
          <span>Demonstrative finance and assurance product. No real company data.</span>
        </div>
        <header className="fi-topbar">
          <div>
            <p className="fi-eyebrow">FY2026 / Management reporting</p>
            <h1>{initialView === "financial-performance" ? "Financial Performance" : initialView === "cash-capital" ? "Cash & Capital" : initialView === "revenue-saas" ? "Revenue & SaaS Economics" : initialView === "assurance" ? "Assurance & Control Readiness" : initialView === "planning-valuation" ? "Planning & Valuation" : "CFO Command Centre"}</h1>
          </div>
          <div className="fi-global-context" aria-label="Global reporting context">
            {initialView === "planning-valuation" ? (
              <>
                <div><span>Actuals cutover</span><strong>Jun 2026</strong></div>
                <div><span>Horizon</span><strong>120 months</strong></div>
              </>
            ) : (
            <label>
              <span>Period</span>
              <select
                value={contextRow.period_id}
                onChange={(event) => setSelectedPeriod(event.target.value)}
                disabled={initialView === "financial-performance" ? !financialWorkspace : initialView === "cash-capital" ? !cashCapitalWorkspace : initialView === "revenue-saas" ? !revenueSaasWorkspace : initialView === "assurance" ? !assuranceWorkspace : !workspace}
              >
                {(initialView === "financial-performance" ? scopedPerformanceSeries : initialView === "cash-capital" ? scopedCashFlows : initialView === "revenue-saas" ? revenueWaterfalls : initialView === "assurance" ? scopedAssuranceVersions : series).map((row) => (
                  <option key={row.period_id} value={row.period_id}>
                    {formatPeriod(row.period_id)}
                  </option>
                ))}
              </select>
            </label>
            )}
            {initialView === "financial-performance" || initialView === "cash-capital" || initialView === "assurance" ? (
              <label>
                <span>Scope</span>
                <select
                  value={selectedScope}
                  onChange={(event) => setSelectedScope(event.target.value)}
                  disabled={initialView === "financial-performance" ? !financialWorkspace : initialView === "cash-capital" ? !cashCapitalWorkspace : !assuranceWorkspace}
                >
                  {(initialView === "financial-performance"
                    ? financialWorkspace?.reportingScopes ?? []
                    : [...new Set((initialView === "cash-capital" ? cashFlows : assuranceVersions).map((row) => row.scope_id))]
                      .map((scopeId) => ({ scope_id: scopeId, scope_name: scopeId }))).map((scope) => (
                    <option key={scope.scope_id} value={scope.scope_id}>{scope.scope_name}</option>
                  ))}
                </select>
              </label>
            ) : (
              <div><span>Scope</span><strong>{contextRow.scope_id}</strong></div>
            )}
            <div><span>Currency</span><strong>{contextRow.currency}</strong></div>
            <button type="button" onClick={() => setDrawerOpen(true)}>
              <span>Reporting version</span>
              <strong>{contextRow.reporting_version_ref.replace(/^RV-NEXUS-(GROUP|UK|US)-/, "")}</strong>
            </button>
          </div>
        </header>

        <main id="finance-main" className="fi-main" tabIndex={-1}>
          {initialView === "financial-performance" && selectedFinancial ? (
            <FinancialPerformanceView
              rows={performanceSeries}
              presentedRows={financialWorkspace?.presentedFinancials ?? []}
              planningRows={financialWorkspace?.planningPerformance ?? []}
              reportingVersion={financialWorkspace?.reportingVersions.find(
                (row) => row.reporting_version_ref === selectedFinancial.reporting_version_ref,
              ) ?? null}
              selectedPeriod={selectedFinancial.period_id}
              selectedScope={selectedFinancial.scope_id}
              runtimeReady={runtimeStatus === "ready"}
              populationsMatch={populationsMatch}
              packageControlCount={manifest?.packageControlCount ?? 36}
              onInspectData={() => setDrawerOpen(true)}
            />
          ) : initialView === "cash-capital" && selectedCashFlow ? (
            <CashCapitalView
              workspace={cashCapitalWorkspace}
              warmSnapshot={warmCashCapital}
              selectedPeriod={selectedCashFlow.period_id}
              selectedScope={selectedCashFlow.scope_id}
              runtimeReady={runtimeStatus === "ready"}
              populationsMatch={populationsMatch}
              packageControlCount={manifest?.packageControlCount ?? 36}
              onInspectData={() => setDrawerOpen(true)}
            />
          ) : initialView === "revenue-saas" && selectedRevenue ? (
            <RevenueSaasView
              workspace={revenueSaasWorkspace}
              warmSnapshot={warmRevenueSaas}
              selectedPeriod={selectedRevenue.period_id}
              runtimeReady={runtimeStatus === "ready"}
            />
          ) : initialView === "planning-valuation" && selectedPlanningForecast ? (
            <PlanningValuationView
              workspace={planningValuationWorkspace}
              warmSnapshot={warmPlanningValuation}
              runtimeReady={runtimeStatus === "ready"}
            />
          ) : initialView === "assurance" && selectedAssuranceVersion ? (
            <AssuranceReadinessView
              workspace={assuranceWorkspace}
              warmSnapshot={warmAssurance}
              selectedPeriod={selectedAssuranceVersion.period_id}
              selectedScope={selectedAssuranceVersion.scope_id}
              runtimeReady={runtimeStatus === "ready"}
            />
          ) : (
          <>
          <section className="fi-heading-row">
            <div>
              <p className="fi-eyebrow">Executive performance / {formatPeriod(selected.period_id)}</p>
              <h2>Financial state, operating drivers and assurance in one view.</h2>
            </div>
            <div className="fi-status-stack">
              <span className="fi-ready-badge">{selected.presentation_status}</span>
              <small>{runtimeStatus === "ready" ? "Queried from C2 Parquet" : "C2 governed warm snapshot"}</small>
            </div>
          </section>

          <section className={`fi-signal ${signal.tone}`}>
            <div className="fi-signal-index">01</div>
            <div>
              <p>Management signal / deterministic presentation rule</p>
              <h3>{signal.title}</h3>
              <span>{signal.detail}</span>
            </div>
            <Link href="/financial-performance">Open driver analysis <small>D2</small></Link>
          </section>

          <section className="fi-kpi-grid" aria-label="Headline performance indicators">
            <KpiCard
              label="Revenue"
              value={formatMoney(selected.revenue_minor)}
              change={percentageChange(selected.revenue_minor, prior?.revenue_minor)}
              context="Statutory statement"
            />
            <KpiCard
              label="Gross margin"
              value={formatPercent(selected.gross_margin_bps)}
              change={
                prior
                  ? (selected.gross_margin_bps - prior.gross_margin_bps) / 10_000
                  : null
              }
              context="Revenue less cost of sales"
            />
            <KpiCard
              label="EBITDA"
              value={formatMoney(selected.ebitda_minor)}
              change={percentageChange(selected.ebitda_minor, prior?.ebitda_minor)}
              context="Statutory presentation"
            />
            <KpiCard
              label="Closing cash"
              value={formatMoney(selected.closing_cash_minor)}
              change={percentageChange(selected.closing_cash_minor, prior?.closing_cash_minor)}
              context="Reconciled cash flow"
            />
            <KpiCard
              label="Ending ARR"
              value={formatMoney(selected.ending_arr_minor)}
              change={percentageChange(selected.ending_arr_minor, prior?.ending_arr_minor)}
              context="Subscription state"
            />
            <KpiCard
              label="Net revenue retention"
              value={formatPercent(selected.net_revenue_retention_bps)}
              change={
                prior?.net_revenue_retention_bps != null && selected.net_revenue_retention_bps != null
                  ? (selected.net_revenue_retention_bps - prior.net_revenue_retention_bps) / 10_000
                  : null
              }
              context="Governed cohort movement"
            />
          </section>

          <section className="fi-analysis-grid">
            <article className="fi-panel fi-trend-panel">
              <div className="fi-panel-head">
                <div>
                  <p className="fi-eyebrow">66-month financial history</p>
                  <h3>Revenue scale and operating result</h3>
                </div>
                <span>GBP / monthly</span>
              </div>
              {workspace ? (
                <TrendChart rows={workspace.commandCentre} />
              ) : (
                <div className="fi-chart-loading">
                  <strong>Preparing 66-month local query</strong>
                  <span>The governed latest-period view remains available while DuckDB starts.</span>
                </div>
              )}
            </article>

            <article className="fi-panel fi-assurance-panel">
              <div className="fi-panel-head">
                <div>
                  <p className="fi-eyebrow">Purpose-specific reliability</p>
                  <h3>Executive presentation ready</h3>
                </div>
                <span className="fi-ready-dot" />
              </div>
              <div className="fi-assurance-score">
                <strong>{metricsReady ?? 11}<small>/11</small></strong>
                <span>executive metrics ready</span>
              </div>
              <dl className="fi-compact-list">
                <div><dt>Model controls</dt><dd>{controlsPassed ?? 15}/15 pass</dd></div>
                <div><dt>History</dt><dd>66 closed months</dd></div>
                <div><dt>Runtime replay</dt><dd>{populationsMatch === false ? "Mismatch" : "Reconciled"}</dd></div>
                <div><dt>Not-ready metrics</dt><dd>{selected.not_ready_metric_count}</dd></div>
              </dl>
              <button type="button" onClick={() => setDrawerOpen(true)}>Inspect data state</button>
            </article>
          </section>

          <section className="fi-domain-grid" aria-label="Finance domain positions">
            <article className="fi-domain-card">
              <div><p>Cash & capital</p><span>D3</span></div>
              <strong>{formatMoney(selected.available_liquidity_minor)}</strong>
              <small>Available liquidity</small>
              <dl>
                <div><dt>Net debt</dt><dd>{formatMoney(selected.net_debt_minor)}</dd></div>
                <div><dt>Operating cash flow</dt><dd>{formatMoney(selected.operating_cash_flow_minor)}</dd></div>
                <div><dt>Total equity</dt><dd>{formatMoney(selected.total_equity_minor)}</dd></div>
              </dl>
            </article>
            <article className="fi-domain-card">
              <div><p>Working capital</p><span>D3</span></div>
              <strong>{formatMoney(selected.operating_working_capital_minor)}</strong>
              <small>Operating working capital</small>
              <dl>
                <div><dt>Accounts receivable</dt><dd>{formatMoney(selected.closing_ar_minor)}</dd></div>
                <div><dt>Overdue receivables</dt><dd>{formatMoney(selected.overdue_ar_minor)}</dd></div>
                <div><dt>DSO / DPO</dt><dd>{selected.dso_days.toFixed(1)} / {selected.dpo_days.toFixed(1)}</dd></div>
              </dl>
            </article>
            <article className="fi-domain-card">
              <div><p>Revenue & SaaS</p><span>D4</span></div>
              <strong>{number.format(selected.active_customer_count)}</strong>
              <small>Active customers</small>
              <dl>
                <div><dt>Billings</dt><dd>{formatMoney(selected.billings_minor)}</dd></div>
                <div><dt>Collections</dt><dd>{formatMoney(selected.collections_minor)}</dd></div>
                <div><dt>Deferred revenue</dt><dd>{formatMoney(selected.closing_deferred_revenue_minor)}</dd></div>
              </dl>
            </article>
          </section>
          </>
          )}

          <footer className="fi-footer">
            <span>Nexus Technologies / Synthetic data environment</span>
            <span>Browser-local SQL / No application database / {initialView === "planning-valuation" ? "Governed Pythia authority" : "Governed C2 authority"}</span>
          </footer>
        </main>
      </div>

      {drawerOpen && (
        <div className="fi-drawer-backdrop">
          <button
            className="fi-drawer-dismiss"
            type="button"
            aria-label="Close data state"
            onClick={() => setDrawerOpen(false)}
          />
          <aside
            className="fi-data-drawer"
            role="dialog"
            aria-modal="true"
            aria-labelledby="data-state-title"
          >
            <div className="fi-drawer-head">
              <div>
                <p className="fi-eyebrow">Governed data state</p>
                <h2 id="data-state-title">Why this view can be trusted</h2>
              </div>
              <button type="button" aria-label="Close data state" onClick={() => setDrawerOpen(false)}>Close</button>
            </div>
            <div className="fi-state-callout">
              <span className="fi-ready-dot" />
              <div><strong>{contextRow.reliability_status.replaceAll("_", " ")}</strong><small>{contextRow.reliability_purpose.replaceAll("_", " ")}</small></div>
            </div>
            <dl className="fi-state-list">
              <div><dt>Selected reporting version</dt><dd>{contextRow.reporting_version_ref}</dd></div>
              <div><dt>Value authority</dt><dd>{contextRow.value_authority.replaceAll("_", " ")}</dd></div>
              <div><dt>Source state</dt><dd>{contextRow._source_data_ref}</dd></div>
              <div><dt>Source digest</dt><dd><code>{shortDigest(contextRow.source_package_digest)}</code></dd></div>
              <div><dt>Delivery</dt><dd>{manifest?.deliveryRef ?? "Q-FINANCE-C2@v1"}</dd></div>
              <div><dt>Finance model</dt><dd>{manifest?.financeModelRef ?? "Q-FINANCE-C1@v1"}</dd></div>
              {manifest?.pythiaRef && <div><dt>Pythia result</dt><dd>{manifest.pythiaRef} / {manifest.pythiaControlCount ?? 10} controls</dd></div>}
              <div><dt>Delivered surface</dt><dd>{manifest?.martCount ?? 21} marts + {manifest?.conformedDimensionCount ?? 8} dimensions</dd></div>
              <div><dt>Package controls</dt><dd>{manifest?.packageControlCount ?? 36}/{manifest?.packageControlCount ?? 36} pass</dd></div>
            </dl>
            <section className="fi-runtime-replay">
              <div><p className="fi-eyebrow">Browser replay</p><strong>{runtimeStatus === "ready" ? "DuckDB-Wasm active" : "Starting locally"}</strong></div>
              {activeWorkspace?.populations.map((population) => {
                const contract = activeWorkspace.manifest.runtimeTables.find(
                  (table) => table.tableName === population.table_name,
                );
                return (
                  <div key={population.table_name}>
                    <span>{population.table_name.replace("mart_", "")}</span>
                    <strong>{population.actual_rows} / {contract?.expectedRows}</strong>
                  </div>
                );
              })}
            </section>
            <div className="fi-lineage-path">
              <p>Source event</p><i />
              <p>Accounting state</p><i />
              <p>Governed mart</p><i />
              <p>Local query</p>
            </div>
            {runtimeError && <p className="fi-runtime-error">Local query note: {runtimeError}</p>}
          </aside>
        </div>
      )}
    </div>
  );
}
