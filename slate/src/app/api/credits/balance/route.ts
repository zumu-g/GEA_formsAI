import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // TODO: Get authenticated user from Supabase session
    // TODO: Query user_profiles for credit_balance

    return NextResponse.json({
      success: true,
      data: {
        balance: 5,
        totalPurchased: 0,
        totalUsed: 0,
      },
    });
  } catch (error) {
    console.error('Balance error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'BALANCE_FAILED', message: 'Failed to get credit balance.' } },
      { status: 500 }
    );
  }
}
