import { NextRequest, NextResponse } from 'next/server';
import { DEV_MODE } from '@/lib/dev';
import { createServerSupabaseClient } from '@/lib/supabase/server';

const MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024;

export async function POST(request: NextRequest) {
  try {
    if (!DEV_MODE) {
      const supabase = await createServerSupabaseClient();
      const {
        data: { user },
        error,
      } = await supabase.auth.getUser();
      if (error || !user) {
        return NextResponse.json(
          { success: false, error: { code: 'UNAUTHORIZED', message: 'Not authenticated.' } },
          { status: 401 }
        );
      }
    }

    const formData = await request.formData();
    const file = formData.get('file');

    if (!file || !(file instanceof Blob)) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'A file is required.' } },
        { status: 400 }
      );
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      return NextResponse.json(
        { success: false, error: { code: 'FILE_TOO_LARGE', message: 'File exceeds the 20MB limit.' } },
        { status: 413 }
      );
    }

    const filename = file instanceof File ? file.name : 'document';
    const arrayBuffer = await file.arrayBuffer();
    const fileBytes = new Uint8Array(arrayBuffer);

    const backendUrl = process.env.FORM_FILLING_BACKEND_URL || 'http://localhost:8000';
    const backendFormData = new FormData();
    backendFormData.append('file', new Blob([Buffer.from(fileBytes)]), filename);

    const convertRes = await fetch(`${backendUrl}/convert`, {
      method: 'POST',
      body: backendFormData,
    });

    if (!convertRes.ok) {
      throw new Error(`Document convert failed: ${convertRes.status} ${convertRes.statusText}`);
    }

    const result: { markdown: string; title: string } = await convertRes.json();

    return NextResponse.json({
      success: true,
      data: {
        markdown: result.markdown,
        title: result.title,
        charCount: result.markdown.length,
        filename,
      },
    });
  } catch (error) {
    console.error('Context upload error:', error);
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'CONVERT_FAILED',
          message: error instanceof Error ? error.message : 'Failed to convert document.',
        },
      },
      { status: 500 }
    );
  }
}
