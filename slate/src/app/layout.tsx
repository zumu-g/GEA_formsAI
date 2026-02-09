import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Slate — AI-Powered Form Filling",
  description: "Upload a PDF, map your data, and fill forms instantly. Pay per use, no subscription required.",
  keywords: ["form filling", "PDF", "AI", "automation", "business forms"],
  openGraph: {
    title: "Slate — Fill Forms, Not Your Calendar",
    description: "AI-powered form filling. Upload, map, done. Pay only when you fill.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="antialiased bg-white text-[#1D1D1F]">
        {children}
      </body>
    </html>
  );
}
