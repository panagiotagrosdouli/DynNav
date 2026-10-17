import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

export const metadata: Metadata = {
  title: "DynNav | History-Conditioned Safe-Return Planning",
  description:
    "History-conditioned safe-return planning for autonomous robots under action-triggered topology hazards.",
};

export default function RootLayout({ children }: Readonly<{ children: ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
