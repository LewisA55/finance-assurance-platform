import { ProductExperience } from "../../../components/ProductExperience";

export default async function DecisionPage({ params }: { params: Promise<{ decisionRef: string }> }) {
  const { decisionRef } = await params;
  return (
    <ProductExperience
      screen={{ kind: "decision", decisionRef: decodeURIComponent(decisionRef) }}
    />
  );
}
