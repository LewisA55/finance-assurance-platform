import { ProductExperience } from "../../../components/ProductExperience";

type ReportingHistoryPageProps = {
  params: Promise<{ periodId: string }>;
};

export default async function ReportingHistoryPage({ params }: ReportingHistoryPageProps) {
  const { periodId } = await params;
  return (
    <ProductExperience
      screen={{ kind: "history", periodId: decodeURIComponent(periodId) }}
    />
  );
}
