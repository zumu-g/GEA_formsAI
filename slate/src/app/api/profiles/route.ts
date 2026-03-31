import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { DataProfile } from '@/types/profile';
import { DEV_MODE, MOCK_USER } from '@/lib/dev';
import { randomUUID } from 'crypto';

// In-memory fallback store for profiles (persists across requests in same server process)
const memoryProfiles = new Map<string, DataProfile[]>();

function toDataProfile(row: Record<string, unknown>): DataProfile {
  return {
    id: row.id as string,
    userId: row.user_id as string,
    name: row.name as string,
    data: (row.data ?? {}) as Record<string, string>,
    isDefault: row.is_default as boolean,
    createdAt: row.created_at as string,
    updatedAt: row.updated_at as string,
  };
}

async function getUser() {
  if (DEV_MODE) return { user: MOCK_USER, supabase: null };
  try {
    const supabase = await createServerSupabaseClient();
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser();
    if (!error && user) return { user, supabase };
  } catch {
    /* Supabase unavailable */
  }
  return { user: null, supabase: null };
}

export async function GET() {
  try {
    const { user, supabase } = await getUser();

    if (!user) {
      return NextResponse.json(
        {
          success: false,
          error: { code: 'UNAUTHORIZED', message: 'Not authenticated.' },
        },
        { status: 401 }
      );
    }

    // Try Supabase first
    if (supabase) {
      try {
        const { data, error } = await supabase
          .from('data_profiles')
          .select('*')
          .eq('user_id', user.id)
          .order('created_at', { ascending: false });

        if (!error) {
          return NextResponse.json({
            success: true,
            data: (data ?? []).map(toDataProfile),
          });
        }
        console.warn(
          'Profiles Supabase fetch failed, using in-memory fallback.',
          error.message
        );
      } catch (err) {
        console.warn(
          'Profiles Supabase fetch failed, using in-memory fallback.',
          (err as Error)?.message
        );
      }
    }

    // Fallback: in-memory
    const profiles = memoryProfiles.get(user.id) ?? [];
    return NextResponse.json({ success: true, data: profiles });
  } catch (error) {
    console.error('Profiles GET error:', error);
    return NextResponse.json(
      {
        success: false,
        error: { code: 'SERVER_ERROR', message: 'Internal server error.' },
      },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    const { user, supabase } = await getUser();

    if (!user) {
      return NextResponse.json(
        {
          success: false,
          error: { code: 'UNAUTHORIZED', message: 'Not authenticated.' },
        },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { name, data, isDefault } = body as {
      name?: string;
      data?: Record<string, string>;
      isDefault?: boolean;
    };

    if (!name || typeof name !== 'string' || name.trim().length === 0) {
      return NextResponse.json(
        {
          success: false,
          error: { code: 'INVALID_NAME', message: 'Profile name is required.' },
        },
        { status: 400 }
      );
    }

    // Try Supabase first
    if (supabase) {
      try {
        if (isDefault) {
          await supabase
            .from('data_profiles')
            .update({ is_default: false })
            .eq('user_id', user.id)
            .eq('is_default', true);
        }

        const { data: created, error } = await supabase
          .from('data_profiles')
          .insert({
            user_id: user.id,
            name: name.trim(),
            data: data ?? {},
            is_default: isDefault ?? false,
          })
          .select()
          .single();

        if (!error && created) {
          return NextResponse.json(
            { success: true, data: toDataProfile(created) },
            { status: 201 }
          );
        }
        console.warn(
          'Profiles Supabase create failed, using in-memory fallback.',
          error?.message
        );
      } catch (err) {
        console.warn(
          'Profiles Supabase create failed, using in-memory fallback.',
          (err as Error)?.message
        );
      }
    }

    // Fallback: in-memory
    const now = new Date().toISOString();
    const profiles = memoryProfiles.get(user.id) ?? [];

    if (isDefault) {
      profiles.forEach((p) => {
        p.isDefault = false;
      });
    }

    const newProfile: DataProfile = {
      id: randomUUID(),
      userId: user.id,
      name: name.trim(),
      data: data ?? {},
      isDefault: isDefault ?? false,
      createdAt: now,
      updatedAt: now,
    };

    profiles.unshift(newProfile);
    memoryProfiles.set(user.id, profiles);

    return NextResponse.json(
      { success: true, data: newProfile },
      { status: 201 }
    );
  } catch (error) {
    console.error('Profiles POST error:', error);
    return NextResponse.json(
      {
        success: false,
        error: { code: 'SERVER_ERROR', message: 'Internal server error.' },
      },
      { status: 500 }
    );
  }
}
