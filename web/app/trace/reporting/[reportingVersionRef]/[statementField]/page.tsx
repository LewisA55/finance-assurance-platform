import { ProductExperience } from "../../../../components/ProductExperience";

type TracePageProps = {
  params: Promise<{ reportingVersionRef: string; statementField: string }>;
};

export default async function TracePage({ params }: TracePageProps) {
  const { reportingVersionRef, statementField } = await params;
  return (
    <ProductExperience
      screen={{
        kind: "trace",
        reportingVersionRef: decodeURIComponent(reportingVersionRef),
        statementField: decodeURIComponent(statementField),
      }}
    />
  );
}
