import { NextRequest, NextResponse } from 'next/server';
import { CREDIT_PACKS } from '@/types/credit';

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

    // TODO: Get authenticated user
    // TODO: Create Stripe checkout session
    // const session = await stripe.checkout.sessions.create({
    //   mode: 'payment',
    //   line_items: [{ price: pack.stripePriceId, quantity: 1 }],
    //   success_url: `${process.env.NEXT_PUBLIC_APP_URL}/credits?success=true`,
    //   cancel_url: `${process.env.NEXT_PUBLIC_APP_URL}/credits?canceled=true`,
    //   metadata: { userId, packId, credits: pack.credits.toString() },
    // });

    return NextResponse.json({
      success: true,
      data: {
        checkoutUrl: '/credits?success=true', // placeholder
      },
    });
  } catch (error) {
    console.error('Purchase error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'PURCHASE_FAILED', message: 'Failed to create checkout session.' } },
      { status: 500 }
    );
  }
}
