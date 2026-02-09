'use client';

import { Sidebar } from '@/components/layout/Sidebar';
import { CreditBalance } from '@/components/credits/CreditBalance';

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-[#F5F5F7]/30">
      <Sidebar />
      <div className="ml-60">
        {/* Top bar */}
        <header className="h-14 border-b border-[#E5E5EA]/60 bg-white/80 backdrop-blur-xl flex items-center justify-end px-6 sticky top-0 z-30">
          <CreditBalance compact />
        </header>
        <main className="p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
