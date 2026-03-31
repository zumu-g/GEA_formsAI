import { NextRequest, NextResponse } from 'next/server';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import { Template } from '@/types/template';
import { DEV_MODE, MOCK_USER } from '@/lib/dev';
import { randomUUID } from 'crypto';

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

export async function GET(request: NextRequest) {
  try {
    const { user, supabase } = await getUser();

    if (!user) {
      return NextResponse.json(
        {
          success: false,
          error: { code: 'UNAUTHORIZED', message: 'You must be logged in.' },
        },
        { status: 401 }
      );
    }

    const searchParams = request.nextUrl.searchParams;
    const query = searchParams.get('q')?.trim();

    // Try Supabase
    if (supabase) {
      try {
        let dbQuery = supabase
          .from('templates')
          .select('*')
          .eq('user_id', user.id)
          .order('updated_at', { ascending: false });

        if (query) {
          dbQuery = dbQuery.or(
            `name.ilike.%${query}%,description.ilike.%${query}%`
          );
        }

        const { data, error } = await dbQuery;

        if (!error) {
          return NextResponse.json({
            success: true,
            data: (data || []).map(rowToTemplate),
          });
        }
        console.warn(
          'Templates Supabase fetch failed, using in-memory fallback.',
          error.message
        );
      } catch (err) {
        console.warn(
          'Templates Supabase fetch failed, using in-memory fallback.',
          (err as Error)?.message
        );
      }
    }

    // Fallback: in-memory
    let templates = memoryTemplates.get(user.id) ?? [];
    if (query) {
      const q = query.toLowerCase();
      templates = templates.filter(
        (t) =>
          t.name.toLowerCase().includes(q) ||
          (t.description?.toLowerCase().includes(q) ?? false)
      );
    }

    return NextResponse.json({
      success: true,
      data: templates,
    });
  } catch (error) {
    console.error('Templates GET error:', error);
    return NextResponse.json(
      {
        success: false,
        error: { code: 'INTERNAL_ERROR', message: 'Internal server error.' },
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
          error: { code: 'UNAUTHORIZED', message: 'You must be logged in.' },
        },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { name, formId, description, fieldMappings, isPublic } = body;

    if (!name || !formId || !fieldMappings) {
      return NextResponse.json(
        {
          success: false,
          error: {
            code: 'INVALID_INPUT',
            message: 'name, formId, and fieldMappings are required.',
          },
        },
        { status: 400 }
      );
    }

    // Try Supabase
    if (supabase) {
      try {
        const { data, error } = await supabase
          .from('templates')
          .insert({
            user_id: user.id,
            form_id: formId,
            name,
            description: description || null,
            field_mappings: fieldMappings,
            is_public: isPublic ?? false,
          })
          .select()
          .single();

        if (!error && data) {
          return NextResponse.json(
            { success: true, data: rowToTemplate(data) },
            { status: 201 }
          );
        }
        console.warn(
          'Templates Supabase create failed, using in-memory fallback.',
          error?.message
        );
      } catch (err) {
        console.warn(
          'Templates Supabase create failed, using in-memory fallback.',
          (err as Error)?.message
        );
      }
    }

    // Fallback: in-memory
    const now = new Date().toISOString();
    const templates = memoryTemplates.get(user.id) ?? [];

    const newTemplate: Template = {
      id: randomUUID(),
      userId: user.id,
      formId,
      name,
      description: description || undefined,
      fieldMappings,
      isPublic: isPublic ?? false,
      useCount: 0,
      createdAt: now,
      updatedAt: now,
    };

    templates.unshift(newTemplate);
    memoryTemplates.set(user.id, templates);

    return NextResponse.json(
      { success: true, data: newTemplate },
      { status: 201 }
    );
  } catch (error) {
    console.error('Templates POST error:', error);
    return NextResponse.json(
      {
        success: false,
        error: { code: 'INTERNAL_ERROR', message: 'Internal server error.' },
      },
      { status: 500 }
    );
  }
}
