import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "DynNav Research",
  description: "Risk-aware dynamic navigation research prototype",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  );
}
