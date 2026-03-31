import { createServerSupabaseClient } from './server';
import { DEV_MODE, MOCK_USER } from '../dev';

/**
 * Returns the authenticated user (real or mock in dev mode).
 * In dev mode, supabase is null — callers must handle that.
 */
export async function getAuthUser() {
  if (DEV_MODE) {
    return { user: MOCK_USER, supabase: null };
  }
  const supabase = await createServerSupabaseClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  return { user, supabase };
}
