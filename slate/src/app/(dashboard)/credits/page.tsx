'use client';

import { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle } from 'lucide-react';
import { CreditBalance } from '@/components/credits/CreditBalance';
import { CreditPurchase } from '@/components/credits/CreditPurchase';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { useCreditStore } from '@/stores/creditStore';
import type { CreditPack } from '@/types/credit';

interface SuccessBannerProps {
  credits: number;
  isMock: boolean;
  onDismiss: () => void;
}

function SuccessBanner({ credits, isMock, onDismiss }: SuccessBannerProps) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 3000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <motion.div
      initial={{ opacity: 0, y: -40 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -40 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className="mb-6 rounded-xl px-5 py-4 bg-[#34C759] text-white shadow-lg"
    >
      <div className="flex items-center gap-3">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.15, type: 'spring', stiffness: 400, damping: 15 }}
        >
          <CheckCircle size={22} />
        </motion.div>
        <div>
          <p className="font-semibold text-sm">
            {credits} credits added to your account
          </p>
          {isMock && (
            <p className="text-xs text-white/70 mt-0.5">
              Mock purchase — connect Stripe for real payments
            </p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export default function CreditsPage() {
  const [loading, setLoading] = useState<string | null>(null);
  const [successInfo, setSuccessInfo] = useState<{
    credits: number;
    isMock: boolean;
  } | null>(null);

  const addCreditsToStore = useCreditStore((s) => s.addCredits);
  const fetchBalance = useCreditStore((s) => s.fetchBalance);

  const dismissBanner = useCallback(() => setSuccessInfo(null), []);

  const handlePurchase = async (pack: CreditPack) => {
    setLoading(pack.id);
    try {
      const response = await fetch('/api/credits/purchase', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ packId: pack.id }),
      });

      const json = await response.json();

      if (!response.ok || !json.success) {
        console.error('Purchase failed:', json.error?.message);
        return;
      }

      const { credits, mockPurchase } = json.data;

      // Update local store immediately for instant feedback
      addCreditsToStore(credits);

      // Also re-fetch from server to stay in sync
      fetchBalance();

      setSuccessInfo({ credits, isMock: !!mockPurchase });
    } catch (error) {
      console.error('Purchase request failed:', error);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="max-w-5xl">
      <AnimatePresence>
        {successInfo && (
          <SuccessBanner
            credits={successInfo.credits}
            isMock={successInfo.isMock}
            onDismiss={dismissBanner}
          />
        )}
      </AnimatePresence>

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
