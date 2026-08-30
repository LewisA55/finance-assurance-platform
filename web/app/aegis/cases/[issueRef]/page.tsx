import { ProductExperience } from "../../../components/ProductExperience";

type GovernanceCasePageProps = {
  params: Promise<{ issueRef: string }>;
};

export default async function GovernanceCasePage({ params }: GovernanceCasePageProps) {
  const { issueRef } = await params;
  return (
    <ProductExperience
      screen={{ kind: "governance", issueRef: decodeURIComponent(issueRef) }}
    />
  );
}
