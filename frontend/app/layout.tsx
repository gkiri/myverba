import type { Metadata } from "next";
import "./globals.css";
import AuthProviderWrapper from './AuthProviderWrapper'

export const metadata: Metadata = {
  title: "Verba",
  description: "The GoldenRAGtriever",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <link rel="icon" href="/icon.ico" />
      <body>
        <AuthProviderWrapper>{children}</AuthProviderWrapper>
      </body>
    </html>
  );
}