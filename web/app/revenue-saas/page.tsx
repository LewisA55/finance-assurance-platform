import type { Metadata } from "next";
import { FinanceIntelligenceExperience } from "../components/finance/FinanceIntelligenceExperience";
import initialSnapshot from "../../public/finance-data/latest-command-centre.json";
import initialRevenueSaas from "../../public/finance-data/latest-revenue-saas.json";
import initialManifest from "../../public/finance-data/runtime-manifest.json";
import type {
  CommandCentreRow,
  FinanceRuntimeManifest,
  RevenueSaasWarmSnapshot,
} from "../lib/finance-runtime/contracts";

export const metadata: Metadata = {
  title: "Revenue & SaaS Economics | Nexus Technologies",
  description:
    "Governed revenue recognition, subscription movements, retention and recurring-revenue portfolio analysis queried locally in the browser.",
};

export default function RevenueSaasPage() {
  return (
    <FinanceIntelligenceExperience
      initialSnapshot={initialSnapshot as CommandCentreRow}
      initialRevenueSaas={initialRevenueSaas as RevenueSaasWarmSnapshot}
      initialManifest={initialManifest as FinanceRuntimeManifest}
      initialView="revenue-saas"
    />
  );
}
