import type { Metadata } from 'next';
import Link from 'next/link';
import { Navbar } from '@/components/layout/Navbar';
import { Footer } from '@/components/layout/Footer';

export const metadata: Metadata = {
  title: 'Terms of Service — Slate',
  description: 'Terms of Service for Slate, the AI form filling platform by GEA Technologies.',
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-white flex flex-col">
      <Navbar />
      <main className="flex-1 max-w-3xl mx-auto px-6 pt-32 pb-20">
        <h1 className="text-3xl font-bold text-[#1B1D24]">Terms of Service</h1>
        <p className="text-sm text-[#767A85] mt-2">Last updated: coming soon</p>
        <div className="mt-10 p-8 rounded-2xl border border-[#E2E4EA] bg-[#F2F4F7]/50 text-center">
          <p className="text-base text-[#767A85]">This page is coming soon.</p>
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
