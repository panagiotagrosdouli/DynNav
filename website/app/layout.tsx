import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

const siteUrl = "https://panagiotagrosdouli.github.io/DynNav/";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: "DynNav | Dynamic Navigation Research",
    template: "%s | DynNav",
  },
  description:
    "DynNav is an open ROS 2 and Python research project for dynamic navigation, risk-aware planning, recoverability, ROS occupancy maps, and reproducible experiments across 26 contribution tracks.",
  applicationName: "DynNav",
  keywords: [
    "dynamic navigation",
    "autonomous mobile robots",
    "ROS 2",
    "Nav2",
    "risk-aware planning",
    "recoverability",
    "occupancy maps",
    "robotics research",
    "reproducible experiments",
  ],
  alternates: { canonical: siteUrl },
  openGraph: {
    type: "website",
    url: siteUrl,
    title: "DynNav | Dynamic Navigation Research",
    description:
      "Open research software for risk-aware, recoverability-aware navigation and reproducible robotics experiments.",
    siteName: "DynNav",
  },
  twitter: {
    card: "summary",
    title: "DynNav | Dynamic Navigation Research",
    description:
      "ROS 2 and Python research on dynamic navigation, recoverability, maps, and reproducible experiments.",
  },
  robots: { index: true, follow: true },
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
