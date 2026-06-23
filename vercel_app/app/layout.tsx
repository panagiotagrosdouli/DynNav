import "./globals.css";

export const metadata = {
  title: "DynNav",
  description: "Dynamic Navigation & Re-routing in Unknown Environments"
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
