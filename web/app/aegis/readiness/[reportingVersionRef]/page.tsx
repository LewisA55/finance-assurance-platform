import { ProductExperience } from "../../../components/ProductExperience";

type ReadinessPageProps = {
  params: Promise<{ reportingVersionRef: string }>;
};

export default async function ReadinessPage({ params }: ReadinessPageProps) {
  const { reportingVersionRef } = await params;
  return (
    <ProductExperience
      screen={{
        kind: "readiness",
        reportingVersionRef: decodeURIComponent(reportingVersionRef),
      }}
    />
  );
}
