import { ProductExperience } from "../../../components/ProductExperience";

type ReconciliationPageProps = {
  params: Promise<{ productRef: string }>;
};

export default async function ReconciliationPage({ params }: ReconciliationPageProps) {
  const { productRef } = await params;
  return (
    <ProductExperience
      screen={{ kind: "reconciliation", productRef: decodeURIComponent(productRef) }}
    />
  );
}
