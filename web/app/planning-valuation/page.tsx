import type { Metadata } from "next";
import { FinanceIntelligenceExperience } from "../components/finance/FinanceIntelligenceExperience";
import initialSnapshot from "../../public/finance-data/latest-command-centre.json";
import initialPlanningValuation from "../../public/finance-data/latest-planning-valuation.json";
import initialManifest from "../../public/finance-data/runtime-manifest.json";
import type {
  CommandCentreRow,
  FinanceRuntimeManifest,
  PlanningValuationWarmSnapshot,
} from "../lib/finance-runtime/contracts";

export const metadata: Metadata = {
  title: "Planning & Valuation | Nexus Technologies",
  description:
    "Governed Pythia scenarios, integrated forecast statements, liquidity capacity and DCF decision gates queried locally in the browser.",
};

export default function PlanningValuationPage() {
  return (
    <FinanceIntelligenceExperience
      initialSnapshot={initialSnapshot as CommandCentreRow}
      initialPlanningValuation={initialPlanningValuation as PlanningValuationWarmSnapshot}
      initialManifest={initialManifest as FinanceRuntimeManifest}
      initialView="planning-valuation"
    />
  );
}
