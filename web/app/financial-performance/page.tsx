import type { Metadata } from "next";
import { FinanceIntelligenceExperience } from "../components/finance/FinanceIntelligenceExperience";
import initialSnapshot from "../../public/finance-data/latest-command-centre.json";
import initialFinancialPerformance from "../../public/finance-data/latest-financial-performance.json";
import initialManifest from "../../public/finance-data/runtime-manifest.json";
import type {
  CommandCentreRow,
  FinancialPerformanceRow,
  FinanceRuntimeManifest,
} from "../lib/finance-runtime/contracts";

export const metadata: Metadata = {
  title: "Financial Performance | Nexus Technologies",
  description:
    "Governed statutory performance, entity consolidation and management-budget variance queried locally in the browser.",
};

export default function FinancialPerformancePage() {
  return (
    <FinanceIntelligenceExperience
      initialSnapshot={initialSnapshot as CommandCentreRow}
      initialFinancialPerformance={initialFinancialPerformance as FinancialPerformanceRow[]}
      initialManifest={initialManifest as FinanceRuntimeManifest}
      initialView="financial-performance"
    />
  );
}
