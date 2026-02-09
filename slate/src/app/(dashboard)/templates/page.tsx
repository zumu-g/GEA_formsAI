'use client';

import { BookTemplate, Plus, Search } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import Link from 'next/link';

export default function TemplatesPage() {
  return (
    <div className="max-w-5xl">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-[#1D1D1F]">Templates</h1>
          <p className="text-sm text-[#86868B] mt-1">
            Save time with reusable form templates.
          </p>
        </div>
        <Link href="/fill">
          <Button>
            <Plus size={16} />
            Create Template
          </Button>
        </Link>
      </div>

      {/* Search */}
      <div className="relative mb-6">
        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#AEAEB2]" />
        <Input
          placeholder="Search templates..."
          className="pl-9"
        />
      </div>

      {/* Empty State */}
      <Card className="py-16 text-center">
        <div className="w-14 h-14 rounded-2xl bg-[#F5F5F7] flex items-center justify-center mx-auto">
          <BookTemplate size={28} className="text-[#AEAEB2]" />
        </div>
        <h3 className="text-base font-semibold text-[#1D1D1F] mt-5">No templates yet</h3>
        <p className="text-sm text-[#86868B] mt-2 max-w-sm mx-auto">
          Fill a form and save it as a template to reuse it with one click next time.
        </p>
        <Link href="/fill" className="inline-block mt-5">
          <Button variant="secondary" size="sm">
            Fill Your First Form
          </Button>
        </Link>
      </Card>
    </div>
  );
}
