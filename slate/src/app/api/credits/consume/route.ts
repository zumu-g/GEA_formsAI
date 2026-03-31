import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { deductCredits } from '@/lib/services/creditService';
import { DEV_MODE, MOCK_USER } from '@/lib/dev';

export async function POST(request: NextRequest) {
  try {
    let userId: string;

    if (DEV_MODE) {
      userId = MOCK_USER.id;
    } else {
      const supabase = await createServerSupabaseClient();
      const { data: { user }, error: authError } = await supabase.auth.getUser();

      if (authError || !user) {
        return NextResponse.json(
          { success: false, error: { code: 'UNAUTHORIZED', message: 'Not authenticated.' } },
          { status: 401 }
        );
      }
      userId = user.id;
    }

    const body = await request.json();
    const { amount, description, fillSessionId } = body;

    if (!amount || typeof amount !== 'number' || amount <= 0) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'A positive credit amount is required.' } },
        { status: 400 }
      );
    }

    if (!description || typeof description !== 'string') {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'A description is required.' } },
        { status: 400 }
      );
    }

    // In dev mode, skip actual credit deduction
    if (DEV_MODE) {
      return NextResponse.json({
        success: true,
        data: { balanceAfter: 99 },
      });
    }

    const result = await deductCredits(userId, amount, description, fillSessionId);

    if (!result.success) {
      return NextResponse.json(
        { success: false, error: { code: 'INSUFFICIENT_CREDITS', message: result.error } },
        { status: 402 }
      );
    }

    return NextResponse.json({
      success: true,
      data: { balanceAfter: result.balanceAfter },
    });
  } catch (error) {
    console.error('Credit consume error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'CONSUME_FAILED', message: 'Failed to consume credits.' } },
      { status: 500 }
    );
  }
}
