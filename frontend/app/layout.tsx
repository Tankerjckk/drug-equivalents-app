import "./globals.css";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Drug Finder",
  description: "Wyszukiwanie leków i zamienników dla personelu medycznego",
  manifest: "/manifest.json",
  icons: {
    icon: "/favicon.ico",
    shortcut: "/favicon.ico",
    apple: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pl">
      <body>{children}</body>
    </html>
  );
}