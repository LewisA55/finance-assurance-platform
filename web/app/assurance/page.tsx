import type { Metadata } from "next";
import { FinanceIntelligenceExperience } from "../components/finance/FinanceIntelligenceExperience";
import initialSnapshot from "../../public/finance-data/latest-command-centre.json";
import initialAssurance from "../../public/finance-data/latest-assurance.json";
import initialManifest from "../../public/finance-data/runtime-manifest.json";
import type {
  AssuranceWarmSnapshot,
  CommandCentreRow,
  FinanceRuntimeManifest,
} from "../lib/finance-runtime/contracts";

export const metadata: Metadata = {
  title: "Assurance & Control Readiness | Nexus Technologies",
  description:
    "Governed close status, reconciliations, serving controls, metric readiness and package evidence queried locally in the browser.",
};

export default function AssurancePage() {
  return (
    <FinanceIntelligenceExperience
      initialSnapshot={initialSnapshot as CommandCentreRow}
      initialAssurance={initialAssurance as AssuranceWarmSnapshot}
      initialManifest={initialManifest as FinanceRuntimeManifest}
      initialView="assurance"
    />
  );
}
