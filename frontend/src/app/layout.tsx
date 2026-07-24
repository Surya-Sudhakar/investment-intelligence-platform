import type { Metadata } from "next";

import { Providers } from "@/components/common/providers";

import "./globals.css";

export const metadata: Metadata = {
  title: "AI Investment Intelligence Platform",
  description: "Phase 1 development status",
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
