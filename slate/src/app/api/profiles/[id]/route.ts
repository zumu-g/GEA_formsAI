import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { DataProfile } from '@/types/profile';
import { DEV_MODE, MOCK_USER } from '@/lib/dev';

// In-memory fallback store for profiles
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

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
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

    // Try Supabase
    if (supabase) {
      try {
        const { data, error } = await supabase
          .from('data_profiles')
          .select('*')
          .eq('id', id)
          .eq('user_id', user.id)
          .single();

        if (!error && data) {
          return NextResponse.json({
            success: true,
            data: toDataProfile(data),
          });
        }
        if (error?.code !== 'PGRST116') {
          console.warn(
            'Profile Supabase GET failed, trying in-memory.',
            error?.message
          );
        }
      } catch (err) {
        console.warn(
          'Profile Supabase GET failed, trying in-memory.',
          (err as Error)?.message
        );
      }
    }

    // Fallback: in-memory
    const profiles = memoryProfiles.get(user.id) ?? [];
    const profile = profiles.find((p) => p.id === id);

    if (!profile) {
      return NextResponse.json(
        {
          success: false,
          error: { code: 'NOT_FOUND', message: 'Profile not found.' },
        },
        { status: 404 }
      );
    }

    return NextResponse.json({ success: true, data: profile });
  } catch (error) {
    console.error('Profile GET error:', error);
    return NextResponse.json(
      {
        success: false,
        error: { code: 'SERVER_ERROR', message: 'Internal server error.' },
      },
      { status: 500 }
    );
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
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

    // Try Supabase
    if (supabase) {
      try {
        const updates: Record<string, unknown> = {
          updated_at: new Date().toISOString(),
        };
        if (name !== undefined) updates.name = name.trim();
        if (data !== undefined) updates.data = data;
        if (isDefault !== undefined) updates.is_default = isDefault;

        if (isDefault === true) {
          await supabase
            .from('data_profiles')
            .update({ is_default: false })
            .eq('user_id', user.id)
            .eq('is_default', true);
        }

        const { data: updated, error } = await supabase
          .from('data_profiles')
          .update(updates)
          .eq('id', id)
          .eq('user_id', user.id)
          .select()
          .single();

        if (!error && updated) {
          return NextResponse.json({
            success: true,
            data: toDataProfile(updated),
          });
        }
        console.warn(
          'Profile Supabase PUT failed, trying in-memory.',
          error?.message
        );
      } catch (err) {
        console.warn(
          'Profile Supabase PUT failed, trying in-memory.',
          (err as Error)?.message
        );
      }
    }

    // Fallback: in-memory
    const profiles = memoryProfiles.get(user.id) ?? [];
    const idx = profiles.findIndex((p) => p.id === id);

    if (idx === -1) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'UPDATE_FAILED',
            message: 'Failed to update profile.',
          },
        },
        { status: 404 }
      );
    }

    if (isDefault === true) {
      profiles.forEach((p) => {
        p.isDefault = false;
      });
    }

    const profile = profiles[idx];
    if (name !== undefined) profile.name = name.trim();
    if (data !== undefined) profile.data = data;
    if (isDefault !== undefined) profile.isDefault = isDefault;
    profile.updatedAt = new Date().toISOString();

    return NextResponse.json({ success: true, data: profile });
  } catch (error) {
    console.error('Profile PUT error:', error);
    return NextResponse.json(
      {
        success: false,
        error: { code: 'SERVER_ERROR', message: 'Internal server error.' },
      },
      { status: 500 }
    );
  }
}

export async function DELETE(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  try {
    const { id } = await params;
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

    // Try Supabase
    if (supabase) {
      try {
        const { error } = await supabase
          .from('data_profiles')
          .delete()
          .eq('id', id)
          .eq('user_id', user.id);

        if (!error) {
          return NextResponse.json({ success: true });
        }
        console.warn(
          'Profile Supabase DELETE failed, trying in-memory.',
          error.message
        );
      } catch (err) {
        console.warn(
          'Profile Supabase DELETE failed, trying in-memory.',
          (err as Error)?.message
        );
      }
    }

    // Fallback: in-memory
    const profiles = memoryProfiles.get(user.id) ?? [];
    const idx = profiles.findIndex((p) => p.id === id);
    if (idx !== -1) {
      profiles.splice(idx, 1);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Profile DELETE error:', error);
    return NextResponse.json(
      {
        success: false,
        error: { code: 'SERVER_ERROR', message: 'Internal server error.' },
      },
      { status: 500 }
    );
  }
}
