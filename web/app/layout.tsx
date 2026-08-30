import type { Metadata } from "next";
import type { ReactNode } from "react";
import "./globals.css";
import "./finance-intelligence.css";

export const metadata: Metadata = {
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL ?? "http://localhost:3000",
  ),
  title: "Nexus Technologies | Financial Performance & Assurance",
  description:
    "A browser-local CFO finance intelligence product over governed statutory, operational and assurance data.",
  openGraph: {
    type: "website",
    title: "Nexus Technologies | Financial Performance & Assurance",
    description:
      "Governed financial performance, operating drivers and assurance in one browser-local product.",
    images: [
      {
        url: "/og.png",
        width: 1755,
        height: 896,
        alt: "Nexus Technologies finance intelligence",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "Nexus Technologies | Financial Performance & Assurance",
    description: "Governed finance intelligence, queried locally in the browser.",
    images: ["/og.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
