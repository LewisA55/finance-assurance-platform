import { ProductExperience } from "../../components/ProductExperience";

export default async function CorrectionPage({ params }: { params: Promise<{ correctionRef: string }> }) {
  const { correctionRef } = await params;
  return (
    <ProductExperience
      screen={{ kind: "correction", correctionRef: decodeURIComponent(correctionRef) }}
    />
  );
}
