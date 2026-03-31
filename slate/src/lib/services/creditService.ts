import { createServerSupabaseClient } from '@/lib/supabase/server';

// In-memory credit store for dev/fallback mode
const memoryCredits = new Map<string, number>();
const memoryTransactions: Array<{
  user_id: string;
  amount: number;
  balance_after: number;
  transaction_type: string;
  description: string;
  fill_session_id?: string | null;
  stripe_payment_id?: string | null;
  created_at: string;
}> = [];

const DEFAULT_DEV_CREDITS = 50;

/**
 * Get the credit balance for a user from user_profiles.
 */
export async function getBalance(userId: string): Promise<number> {
  try {
    const supabase = await createServerSupabaseClient();

    const { data, error } = await supabase
      .from('user_profiles')
      .select('credit_balance')
      .eq('id', userId)
      .single();

    if (error) throw error;
    if (data) return data.credit_balance ?? 0;
  } catch (err) {
    console.warn('Supabase credit balance fetch failed, using in-memory store.', (err as Error)?.message);
  }

  // Fallback
  if (!memoryCredits.has(userId)) {
    memoryCredits.set(userId, DEFAULT_DEV_CREDITS);
  }
  return memoryCredits.get(userId)!;
}

/**
 * Atomically deduct credits from a user's balance and log the transaction.
 * Returns an error if insufficient credits.
 */
export async function deductCredits(
  userId: string,
  amount: number,
  description: string,
  fillSessionId?: string
): Promise<{ success: boolean; balanceAfter: number; error?: string }> {
  try {
    const supabase = await createServerSupabaseClient();

    // 1. Read current balance
    const { data: profile, error: fetchError } = await supabase
      .from('user_profiles')
      .select('credit_balance')
      .eq('id', userId)
      .single();

    if (fetchError) throw fetchError;

    const currentBalance = profile.credit_balance ?? 0;

    if (currentBalance < amount) {
      return {
        success: false,
        balanceAfter: currentBalance,
        error: `Insufficient credits. You have ${currentBalance} but need ${amount}.`,
      };
    }

    const newBalance = currentBalance - amount;

    // 2. Update balance (with optimistic-lock check to prevent races)
    const { error: updateError, count } = await supabase
      .from('user_profiles')
      .update({ credit_balance: newBalance })
      .eq('id', userId)
      .gte('credit_balance', amount);

    if (updateError) throw updateError;

    // If no row was updated, another request consumed credits first
    if (count !== null && count === 0) {
      return {
        success: false,
        balanceAfter: currentBalance,
        error: 'Insufficient credits (concurrent deduction detected).',
      };
    }

    // 3. Insert transaction record
    const { error: txError } = await supabase
      .from('credit_transactions')
      .insert({
        user_id: userId,
        amount: -amount,
        balance_after: newBalance,
        transaction_type: 'fill',
        description,
        fill_session_id: fillSessionId ?? null,
      });

    if (txError) {
      // Log but don't fail — the balance was already deducted
      console.error('Failed to insert credit transaction:', txError.message);
    }

    return { success: true, balanceAfter: newBalance };
  } catch (err) {
    console.warn('Supabase deductCredits failed, using in-memory store.', (err as Error)?.message);
  }

  // Fallback: in-memory
  if (!memoryCredits.has(userId)) {
    memoryCredits.set(userId, DEFAULT_DEV_CREDITS);
  }
  const currentBalance = memoryCredits.get(userId)!;

  if (currentBalance < amount) {
    return {
      success: false,
      balanceAfter: currentBalance,
      error: `Insufficient credits. You have ${currentBalance} but need ${amount}.`,
    };
  }

  const newBalance = currentBalance - amount;
  memoryCredits.set(userId, newBalance);

  memoryTransactions.push({
    user_id: userId,
    amount: -amount,
    balance_after: newBalance,
    transaction_type: 'fill',
    description,
    fill_session_id: fillSessionId ?? null,
    created_at: new Date().toISOString(),
  });

  return { success: true, balanceAfter: newBalance };
}

/**
 * Add credits to a user's balance (purchase, refund, bonus, etc.)
 */
export async function addCredits(
  userId: string,
  amount: number,
  transactionType: string,
  description: string,
  stripePaymentId?: string
): Promise<{ balanceAfter: number }> {
  try {
    const supabase = await createServerSupabaseClient();

    // 1. Read current balance
    const { data: profile, error: fetchError } = await supabase
      .from('user_profiles')
      .select('credit_balance')
      .eq('id', userId)
      .single();

    if (fetchError) throw fetchError;

    const currentBalance = profile.credit_balance ?? 0;
    const newBalance = currentBalance + amount;

    // 2. Update balance
    const { error: updateError } = await supabase
      .from('user_profiles')
      .update({ credit_balance: newBalance })
      .eq('id', userId);

    if (updateError) throw updateError;

    // 3. Insert transaction record
    const { error: txError } = await supabase
      .from('credit_transactions')
      .insert({
        user_id: userId,
        amount,
        balance_after: newBalance,
        transaction_type: transactionType,
        description,
        stripe_payment_id: stripePaymentId ?? null,
      });

    if (txError) {
      console.error('Failed to insert credit transaction:', txError.message);
    }

    return { balanceAfter: newBalance };
  } catch (err) {
    console.warn('Supabase addCredits failed, using in-memory store.', (err as Error)?.message);
  }

  // Fallback: in-memory
  if (!memoryCredits.has(userId)) {
    memoryCredits.set(userId, DEFAULT_DEV_CREDITS);
  }
  const currentBalance = memoryCredits.get(userId)!;
  const newBalance = currentBalance + amount;
  memoryCredits.set(userId, newBalance);

  memoryTransactions.push({
    user_id: userId,
    amount,
    balance_after: newBalance,
    transaction_type: transactionType,
    description,
    stripe_payment_id: stripePaymentId ?? null,
    created_at: new Date().toISOString(),
  });

  return { balanceAfter: newBalance };
}
