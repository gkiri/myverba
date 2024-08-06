import type { Metadata } from "next";
import "./globals.css";
import ClientLayout from './ClientLayout';

export const metadata: Metadata = {
  title: "Verba",
  description: "The GoldenRAGtriever",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/icon.ico" />
      </head>
      <body>
        <ClientLayout>{children}</ClientLayout>
      </body>
    </html>
  );
}