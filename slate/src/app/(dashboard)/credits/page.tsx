'use client';

import { useState } from 'react';
import { CreditBalance } from '@/components/credits/CreditBalance';
import { CreditPurchase } from '@/components/credits/CreditPurchase';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import type { CreditPack } from '@/types/credit';

export default function CreditsPage() {
  const [loading, setLoading] = useState<string | null>(null);

  const handlePurchase = async (pack: CreditPack) => {
    setLoading(pack.id);
    try {
      // TODO: Create Stripe checkout session
      // const response = await fetch('/api/credits/purchase', {
      //   method: 'POST',
      //   body: JSON.stringify({ packId: pack.id }),
      // });
      // const { data } = await response.json();
      // window.location.href = data.checkoutUrl;

      await new Promise((resolve) => setTimeout(resolve, 1000));
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="max-w-5xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-[#1D1D1F]">Credits</h1>
        <p className="text-sm text-[#86868B] mt-1">
          Buy credits to fill forms. Credits never expire.
        </p>
      </div>

      <CreditBalance />

      <div className="mt-10">
        <h2 className="text-lg font-semibold text-[#1D1D1F] mb-4">Buy Credits</h2>
        <CreditPurchase onPurchase={handlePurchase} loading={loading} />
      </div>

      {/* Credit costs reference */}
      <div className="mt-10">
        <h2 className="text-lg font-semibold text-[#1D1D1F] mb-4">How Credits Work</h2>
        <Card>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { action: 'Manual form fill', cost: '1 credit' },
              { action: 'AI auto-fill', cost: '2 credits' },
              { action: 'Create template', cost: '2 credits' },
              { action: 'Fill from template', cost: '1 credit' },
              { action: 'Batch fill (per form)', cost: '1 credit' },
              { action: 'API call (per fill)', cost: '1 credit' },
            ].map((item) => (
              <div key={item.action} className="flex items-center justify-between">
                <span className="text-sm text-[#86868B]">{item.action}</span>
                <Badge variant="accent">{item.cost}</Badge>
              </div>
            ))}
          </div>
        </Card>
      </div>

      {/* Transaction History */}
      <div className="mt-10">
        <h2 className="text-lg font-semibold text-[#1D1D1F] mb-4">Transaction History</h2>
        <Card className="text-center py-10">
          <p className="text-sm text-[#86868B]">No transactions yet</p>
        </Card>
      </div>
    </div>
  );
}
