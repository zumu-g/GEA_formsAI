'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Zap } from 'lucide-react';

export function Navbar() {
  return (
    <nav className="fixed top-0 left-0 right-0 z-40 bg-white/80 backdrop-blur-xl border-b border-[#E2E4EA]/60">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link href="/" className="flex items-center gap-2">
          <div className="w-7 h-7 bg-[#1B1D24] rounded-lg flex items-center justify-center">
            <Zap size={14} className="text-white" />
          </div>
          <span className="text-lg font-semibold tracking-tight text-[#1B1D24]">
            Slate
          </span>
        </Link>

        <div className="hidden md:flex items-center gap-8">
          <Link href="#features" className="text-sm text-[#767A85] hover:text-[#1B1D24] transition-colors">
            Features
          </Link>
          <Link href="#pricing" className="text-sm text-[#767A85] hover:text-[#1B1D24] transition-colors">
            Pricing
          </Link>
          <Link href="#how-it-works" className="text-sm text-[#767A85] hover:text-[#1B1D24] transition-colors">
            How It Works
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <Link href="/login">
            <Button variant="ghost" size="sm">Log In</Button>
          </Link>
          <Link href="/signup">
            <Button size="sm">Get Started Free</Button>
          </Link>
        </div>
      </div>
    </nav>
  );
}
