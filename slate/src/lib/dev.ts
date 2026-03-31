/**
 * Dev mode utilities — allows running the app without a real Supabase backend.
 * DEV_MODE is true when running in development AND no SUPABASE_SERVICE_ROLE_KEY is set.
 */

export const DEV_MODE =
  process.env.NODE_ENV === 'development' &&
  !process.env.SUPABASE_SERVICE_ROLE_KEY;

export const MOCK_USER = {
  id: '00000000-0000-0000-0000-000000000000',
  email: 'dev@useslate.com',
  user_metadata: { display_name: 'Dev User' },
};
