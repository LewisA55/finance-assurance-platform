import type { Metadata } from "next";
import { FinanceIntelligenceExperience } from "../components/finance/FinanceIntelligenceExperience";
import initialSnapshot from "../../public/finance-data/latest-command-centre.json";
import initialCashCapital from "../../public/finance-data/latest-cash-capital.json";
import initialManifest from "../../public/finance-data/runtime-manifest.json";
import type {
  CashCapitalWarmSnapshot,
  CommandCentreRow,
  FinanceRuntimeManifest,
} from "../lib/finance-runtime/contracts";

export const metadata: Metadata = {
  title: "Cash & Capital | Nexus Technologies",
  description:
    "Governed liquidity, cash flow, working capital and capital structure queried locally in the browser.",
};

export default function CashCapitalPage() {
  return (
    <FinanceIntelligenceExperience
      initialSnapshot={initialSnapshot as CommandCentreRow}
      initialCashCapital={initialCashCapital as CashCapitalWarmSnapshot}
      initialManifest={initialManifest as FinanceRuntimeManifest}
      initialView="cash-capital"
    />
  );
}
