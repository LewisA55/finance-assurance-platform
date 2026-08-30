import { ProductExperience } from "../../../../components/ProductExperience";

type ReportingPageProps = {
  params: Promise<{ periodId: string; versionRef: string }>;
};

export default async function ReportingPage({ params }: ReportingPageProps) {
  const { periodId, versionRef } = await params;
  return (
    <ProductExperience
      screen={{
        kind: "reporting",
        periodId: decodeURIComponent(periodId),
        versionRef: decodeURIComponent(versionRef),
      }}
    />
  );
}
