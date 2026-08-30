import { FinanceIntelligenceExperience } from "./components/finance/FinanceIntelligenceExperience";
import initialSnapshot from "../public/finance-data/latest-command-centre.json";
import initialManifest from "../public/finance-data/runtime-manifest.json";
import type {
  CommandCentreRow,
  FinanceRuntimeManifest,
} from "./lib/finance-runtime/contracts";

export default function Home() {
  return (
    <FinanceIntelligenceExperience
      initialSnapshot={initialSnapshot as CommandCentreRow}
      initialManifest={initialManifest as FinanceRuntimeManifest}
    />
  );
}
