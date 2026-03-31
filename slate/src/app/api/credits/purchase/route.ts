import { NextRequest, NextResponse } from 'next/server';
import { CREDIT_PACKS } from '@/types/credit';
import { addCredits } from '@/lib/services/creditService';

// In-memory balance for dev mode (when DB is unavailable)
const devBalances = new Map<string, number>();

const DEV_USER_ID = '00000000-0000-0000-0000-000000000000';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { packId } = body;

    const pack = CREDIT_PACKS.find((p) => p.id === packId);
    if (!pack) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_PACK', message: 'Invalid credit pack.' } },
        { status: 400 }
      );
    }

    // Future path: real Stripe checkout
    if (process.env.STRIPE_SECRET_KEY) {
      // When Stripe is configured, create a real checkout session
      // const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);
      // const session = await stripe.checkout.sessions.create({
      //   mode: 'payment',
      //   line_items: [{ price: pack.stripePriceId, quantity: 1 }],
      //   success_url: `${process.env.NEXT_PUBLIC_APP_URL}/credits?success=true`,
      //   cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/credits?canceled=true`,
      //   metadata: { userId, packId, credits: pack.credits.toString() },
      // });
      // return NextResponse.json({ success: true, data: { checkoutUrl: session.url } });
    }

    // Dev mode: mock purchase — immediately grant credits
    const userId = DEV_USER_ID;

    try {
      // Try the real DB path first
      const result = await addCredits(
        userId,
        pack.credits,
        'purchase',
        `Purchased ${pack.name} pack`
      );
      return NextResponse.json({
        success: true,
        data: {
          credits: pack.credits,
          balanceAfter: result.balanceAfter,
          mockPurchase: true,
        },
      });
    } catch {
      // DB unavailable — use in-memory fallback
      const current = devBalances.get(userId) ?? 0;
      const newBalance = current + pack.credits;
      devBalances.set(userId, newBalance);

      return NextResponse.json({
        success: true,
        data: {
          credits: pack.credits,
          balanceAfter: newBalance,
          mockPurchase: true,
        },
      });
    }
  } catch (error) {
    console.error('Purchase error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'PURCHASE_FAILED', message: 'Failed to process purchase.' } },
      { status: 500 }
    );
  }
}
