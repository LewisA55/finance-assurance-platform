import { ProductExperience } from "../../../components/ProductExperience";

type ExceptionPageProps = {
  params: Promise<{ exceptionRef: string }>;
};

export default async function ExceptionPage({ params }: ExceptionPageProps) {
  const { exceptionRef } = await params;
  return (
    <ProductExperience
      screen={{ kind: "exception", exceptionRef: decodeURIComponent(exceptionRef) }}
    />
  );
}
