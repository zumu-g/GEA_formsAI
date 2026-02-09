'use client';

import { Coins, Plus } from 'lucide-react';
import { useCreditStore } from '@/stores/creditStore';
import Link from 'next/link';

interface CreditBalanceProps {
  compact?: boolean;
}

export function CreditBalance({ compact = false }: CreditBalanceProps) {
  const balance = useCreditStore((s) => s.balance);

  if (compact) {
    return (
      <Link
        href="/credits"
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[#5856D6]/10 hover:bg-[#5856D6]/15 transition-colors"
      >
        <Coins size={14} className="text-[#5856D6]" />
        <span className="text-sm font-semibold text-[#5856D6]">{balance}</span>
      </Link>
    );
  }

  return (
    <div className="flex items-center justify-between p-5 rounded-2xl bg-gradient-to-br from-[#5856D6] to-[#4A48C4]">
      <div>
        <p className="text-sm text-white/70 font-medium">Credit Balance</p>
        <p className="text-3xl font-bold text-white mt-1">{balance}</p>
        <p className="text-xs text-white/50 mt-1">credits remaining</p>
      </div>
      <Link
        href="/credits"
        className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-white/20 hover:bg-white/30 transition-colors text-white text-sm font-medium"
      >
        <Plus size={14} />
        Buy Credits
      </Link>
    </div>
  );
}
