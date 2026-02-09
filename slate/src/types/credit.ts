export interface CreditTransaction {
  id: string;
  userId: string;
  amount: number;
  balanceAfter: number;
  transactionType: 'purchase' | 'fill' | 'template_create' | 'referral' | 'bonus' | 'refund';
  description?: string;
  stripePaymentId?: string;
  fillSessionId?: string;
  createdAt: string;
}

export interface CreditPack {
  id: string;
  name: string;
  credits: number;
  price: number;
  pricePerCredit: number;
  savings: number;
  stripePriceId: string;
  popular?: boolean;
}

export const CREDIT_PACKS: CreditPack[] = [
  {
    id: 'starter',
    name: 'Starter',
    credits: 10,
    price: 2.00,
    pricePerCredit: 0.20,
    savings: 20,
    stripePriceId: '',
  },
  {
    id: 'business',
    name: 'Business',
    credits: 50,
    price: 8.50,
    pricePerCredit: 0.17,
    savings: 32,
    stripePriceId: '',
    popular: true,
  },
  {
    id: 'professional',
    name: 'Professional',
    credits: 200,
    price: 28.00,
    pricePerCredit: 0.14,
    savings: 44,
    stripePriceId: '',
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    credits: 1000,
    price: 100.00,
    pricePerCredit: 0.10,
    savings: 60,
    stripePriceId: '',
  },
];

export const CREDIT_COSTS = {
  manual_fill: 1,
  ai_auto_fill: 2,
  template_create: 2,
  template_fill: 1,
  batch_fill: 1,
  recurring_fill: 1,
  api_fill: 1,
} as const;
