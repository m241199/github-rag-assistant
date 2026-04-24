import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "GitHub RAG Assistant",
  description: "Ask questions about indexed GitHub repositories.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
