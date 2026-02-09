'use client';

import Link from 'next/link';
import { FileText, BookTemplate, Clock, ArrowRight, Plus, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { CreditBalance } from '@/components/credits/CreditBalance';

export default function DashboardPage() {
  return (
    <div className="max-w-5xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#1D1D1F]">Dashboard</h1>
          <p className="text-sm text-[#86868B] mt-1">Welcome back. What would you like to fill today?</p>
        </div>
        <Link href="/fill">
          <Button>
            <Plus size={16} />
            Fill a Form
          </Button>
        </Link>
      </div>

      {/* Credit Balance */}
      <CreditBalance />

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <Link href="/fill">
          <Card hover className="flex items-center gap-4 cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-[#5856D6]/10 flex items-center justify-center flex-shrink-0">
              <FileText size={20} className="text-[#5856D6]" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold text-[#1D1D1F]">Upload PDF</h3>
              <p className="text-xs text-[#86868B]">Upload a new form to fill</p>
            </div>
            <ArrowRight size={16} className="text-[#AEAEB2]" />
          </Card>
        </Link>

        <Link href="/templates">
          <Card hover className="flex items-center gap-4 cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-[#34C759]/10 flex items-center justify-center flex-shrink-0">
              <BookTemplate size={20} className="text-[#34C759]" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold text-[#1D1D1F]">Templates</h3>
              <p className="text-xs text-[#86868B]">Fill from a saved template</p>
            </div>
            <ArrowRight size={16} className="text-[#AEAEB2]" />
          </Card>
        </Link>

        <Link href="/fill">
          <Card hover className="flex items-center gap-4 cursor-pointer">
            <div className="w-10 h-10 rounded-xl bg-[#FF9F0A]/10 flex items-center justify-center flex-shrink-0">
              <Sparkles size={20} className="text-[#FF9F0A]" />
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-semibold text-[#1D1D1F]">AI Auto-Fill</h3>
              <p className="text-xs text-[#86868B]">Let AI fill your form</p>
            </div>
            <ArrowRight size={16} className="text-[#AEAEB2]" />
          </Card>
        </Link>
      </div>

      {/* Recent Activity */}
      <div className="mt-10">
        <h2 className="text-lg font-semibold text-[#1D1D1F] mb-4">Recent Activity</h2>
        <Card className="divide-y divide-[#E5E5EA]">
          {/* Empty state */}
          <div className="py-12 text-center">
            <div className="w-12 h-12 rounded-2xl bg-[#F5F5F7] flex items-center justify-center mx-auto">
              <Clock size={24} className="text-[#AEAEB2]" />
            </div>
            <p className="text-sm text-[#86868B] mt-4">No forms filled yet</p>
            <p className="text-xs text-[#AEAEB2] mt-1">Upload your first PDF to get started</p>
            <Link href="/fill" className="inline-block mt-4">
              <Button variant="secondary" size="sm">
                Fill Your First Form
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
