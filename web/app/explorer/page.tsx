import { ProductExperience } from "../components/ProductExperience";
import { readCloseOutcome } from "../lib/period-close";

export default async function ExplorerPage({ searchParams }: {
  searchParams: Promise<{ close?: string | string[] }>;
}) {
  const { close } = await searchParams;
  return <ProductExperience screen={{ kind: "explorer", closeOutcome: readCloseOutcome(close) }} />;
}
