import type { Metadata } from 'next';
import Link from 'next/link';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';

export const metadata: Metadata = {
  title: 'Privacy Policy — Slate',
  description: 'Privacy Policy for Slate, the AI form filling platform by GEA Technologies.',
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Navbar />
      <main className="flex-1 max-w-3xl mx-auto px-6 pt-32 pb-20">
        <h1 className="text-3xl font-bold text-[#1D1D1F]">Privacy Policy</h1>
        <p className="text-sm text-[#86868B] mt-2">Last updated: coming soon</p>
        <div className="mt-10 p-8 rounded-2xl border border-[#E5E5EA] bg-[#F5F5F7]/50 text-center">
          <p className="text-base text-[#86868B]">This page is coming soon.</p>
          <Link
            href="/"
            className="inline-block mt-6 text-sm font-medium text-[#5856D6] hover:underline"
          >
            Back to home
          </Link>
        </div>
      </main>
      <Footer />
    </div>
  );
}
