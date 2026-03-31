import { NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { getBalance } from '@/lib/services/creditService';
import { DEV_MODE, MOCK_USER } from '@/lib/dev';

export async function GET() {
  try {
    let userId: string;

    if (DEV_MODE) {
      userId = MOCK_USER.id;
      // In dev mode, return a mock balance instead of hitting the DB
      return NextResponse.json({
        success: true,
        data: { balance: 100 },
      });
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

    const balance = await getBalance(userId);

    return NextResponse.json({
      success: true,
      data: { balance },
    });
  } catch (error) {
    console.error('Balance error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'BALANCE_FAILED', message: 'Failed to get credit balance.' } },
      { status: 500 }
    );
  }
}
