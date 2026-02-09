'use client';

import { Check } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { CREDIT_PACKS, CreditPack } from '@/types/credit';

interface CreditPurchaseProps {
  onPurchase: (pack: CreditPack) => void;
  loading?: string | null;
}

export function CreditPurchase({ onPurchase, loading }: CreditPurchaseProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {CREDIT_PACKS.map((pack) => (
        <Card
          key={pack.id}
          hover
          className={`relative flex flex-col ${
            pack.popular ? 'border-[#5856D6] ring-1 ring-[#5856D6]/20' : ''
          }`}
        >
          {pack.popular && (
            <div className="absolute -top-2.5 left-1/2 -translate-x-1/2">
              <Badge variant="accent">Most Popular</Badge>
            </div>
          )}

          <div className="flex-1">
            <h3 className="text-base font-semibold text-[#1D1D1F]">{pack.name}</h3>
            <div className="mt-3">
              <span className="text-3xl font-bold text-[#1D1D1F]">
                ${pack.price.toFixed(2)}
              </span>
            </div>
            <p className="text-sm text-[#86868B] mt-1">
              {pack.credits} credits
            </p>

            <ul className="mt-4 space-y-2">
              <li className="flex items-center gap-2 text-sm text-[#86868B]">
                <Check size={14} className="text-[#34C759]" />
                ${pack.pricePerCredit.toFixed(2)} per credit
              </li>
              <li className="flex items-center gap-2 text-sm text-[#86868B]">
                <Check size={14} className="text-[#34C759]" />
                {pack.savings}% savings
              </li>
              <li className="flex items-center gap-2 text-sm text-[#86868B]">
                <Check size={14} className="text-[#34C759]" />
                Never expires
              </li>
            </ul>
          </div>

          <Button
            variant={pack.popular ? 'primary' : 'secondary'}
            className="w-full mt-6"
            onClick={() => onPurchase(pack)}
            loading={loading === pack.id}
          >
            Buy {pack.name}
          </Button>
        </Card>
      ))}
    </div>
  );
}
