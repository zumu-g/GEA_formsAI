import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.text();
    const signature = request.headers.get('stripe-signature');

    if (!signature) {
      return NextResponse.json(
        { success: false, error: { code: 'NO_SIGNATURE', message: 'Missing Stripe signature.' } },
        { status: 400 }
      );
    }

    // TODO: Verify Stripe webhook signature
    // const event = stripe.webhooks.constructEvent(body, signature, process.env.STRIPE_WEBHOOK_SECRET!);

    // TODO: Handle events:
    // - checkout.session.completed → Add credits to user
    // - payment_intent.payment_failed → Log failure

    return NextResponse.json({ received: true });
  } catch (error) {
    console.error('Webhook error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'WEBHOOK_FAILED', message: 'Webhook processing failed.' } },
      { status: 500 }
    );
  }
}
