import type { Metadata } from "next";
import { Space_Grotesk, IBM_Plex_Sans, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";

// Display / headings / UI chrome — geometric, characterful, not Inter.
const spaceGrotesk = Space_Grotesk({
  subsets: ["latin"],
  variable: "--font-space-grotesk",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

// Body / dense UI — warm, engineered, reads well at small sizes.
const plexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-plex-sans",
  display: "swap",
  weight: ["400", "500", "600", "700"],
});

// Monospace — values, results, technical chrome.
const plexMono = IBM_Plex_Mono({
  subsets: ["latin"],
  variable: "--font-plex-mono",
  display: "swap",
  weight: ["400", "500"],
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
    <html lang="en" className={`${spaceGrotesk.variable} ${plexSans.variable} ${plexMono.variable}`}>
      <body className="antialiased bg-white text-[#1B1D24]">
        {children}
      </body>
    </html>
  );
}
