import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { Template } from '@/types/template';
import { DEV_MODE, MOCK_USER } from '@/lib/dev';

// In-memory fallback store for templates
const memoryTemplates = new Map<string, Template[]>();

function rowToTemplate(row: Record<string, unknown>): Template {
  return {
    id: row.id as string,
    userId: row.user_id as string,
    formId: row.form_id as string,
    name: row.name as string,
    description: (row.description as string) || undefined,
    fieldMappings: (row.field_mappings as Template['fieldMappings']) || [],
    isPublic: row.is_public as boolean,
    useCount: row.use_count as number,
    createdAt: row.created_at as string,
    updatedAt: row.updated_at as string,
  };
}

async function getUser() {
  if (DEV_MODE) return { user: MOCK_USER, supabase: null };
  try {
    const supabase = await createServerSupabaseClient();
    const { data: { user }, error } = await supabase.auth.getUser();
    if (!error && user) return { user, supabase };
  } catch {}
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
        { success: false, error: { code: 'UNAUTHORIZED', message: 'You must be logged in.' } },
        { status: 401 }
      );
    }

    // Try Supabase
    if (supabase) {
      try {
        const { data, error } = await supabase
          .from('templates')
          .select('*')
          .eq('id', id)
          .eq('user_id', user.id)
          .single();

        if (!error && data) {
          return NextResponse.json({ success: true, data: rowToTemplate(data) });
        }
        if (error?.code === 'PGRST116') {
          // Not found — fall through to memory
        } else if (error) {
          console.warn('Template Supabase GET failed, trying in-memory.', error.message);
        }
      } catch (err) {
        console.warn('Template Supabase GET failed, trying in-memory.', (err as Error)?.message);
      }
    }

    // Fallback: in-memory
    const templates = memoryTemplates.get(user.id) ?? [];
    const template = templates.find((t) => t.id === id);

    if (!template) {
      return NextResponse.json(
        { success: false, error: { code: 'NOT_FOUND', message: 'Template not found.' } },
        { status: 404 }
      );
    }

    return NextResponse.json({ success: true, data: template });
  } catch (error) {
    console.error('Template GET error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'INTERNAL_ERROR', message: 'Internal server error.' } },
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
        { success: false, error: { code: 'UNAUTHORIZED', message: 'You must be logged in.' } },
        { status: 401 }
      );
    }

    const body = await request.json();

    // Try Supabase
    if (supabase) {
      try {
        const updates: Record<string, unknown> = {};

        if (body.name !== undefined) updates.name = body.name;
        if (body.description !== undefined) updates.description = body.description;
        if (body.fieldMappings !== undefined) updates.field_mappings = body.fieldMappings;
        if (body.isPublic !== undefined) updates.is_public = body.isPublic;

        if (Object.keys(updates).length === 0) {
          return NextResponse.json(
            { success: false, error: { code: 'INVALID_INPUT', message: 'No fields to update.' } },
            { status: 400 }
          );
        }

        updates.updated_at = new Date().toISOString();

        const { data, error } = await supabase
          .from('templates')
          .update(updates)
          .eq('id', id)
          .eq('user_id', user.id)
          .select()
          .single();

        if (!error && data) {
          return NextResponse.json({ success: true, data: rowToTemplate(data) });
        }
        console.warn('Template Supabase PUT failed, trying in-memory.', error?.message);
      } catch (err) {
        console.warn('Template Supabase PUT failed, trying in-memory.', (err as Error)?.message);
      }
    }

    // Fallback: in-memory
    const templates = memoryTemplates.get(user.id) ?? [];
    const idx = templates.findIndex((t) => t.id === id);

    if (idx === -1) {
      return NextResponse.json(
        { success: false, error: { code: 'UPDATE_FAILED', message: 'Template not found or update failed.' } },
        { status: 404 }
      );
    }

    const template = templates[idx];
    if (body.name !== undefined) template.name = body.name;
    if (body.description !== undefined) template.description = body.description;
    if (body.fieldMappings !== undefined) template.fieldMappings = body.fieldMappings;
    if (body.isPublic !== undefined) template.isPublic = body.isPublic;
    template.updatedAt = new Date().toISOString();

    return NextResponse.json({ success: true, data: template });
  } catch (error) {
    console.error('Template PUT error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'INTERNAL_ERROR', message: 'Internal server error.' } },
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
        { success: false, error: { code: 'UNAUTHORIZED', message: 'You must be logged in.' } },
        { status: 401 }
      );
    }

    // Try Supabase
    if (supabase) {
      try {
        const { error } = await supabase
          .from('templates')
          .delete()
          .eq('id', id)
          .eq('user_id', user.id);

        if (!error) {
          return NextResponse.json({ success: true });
        }
        console.warn('Template Supabase DELETE failed, trying in-memory.', error.message);
      } catch (err) {
        console.warn('Template Supabase DELETE failed, trying in-memory.', (err as Error)?.message);
      }
    }

    // Fallback: in-memory
    const templates = memoryTemplates.get(user.id) ?? [];
    const idx = templates.findIndex((t) => t.id === id);
    if (idx !== -1) {
      templates.splice(idx, 1);
    }

    return NextResponse.json({ success: true });
  } catch (error) {
    console.error('Template DELETE error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'INTERNAL_ERROR', message: 'Internal server error.' } },
      { status: 500 }
    );
  }
}
