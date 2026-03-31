import { NextRequest, NextResponse } from 'next/server';
import { getPdf } from '@/lib/services/pdfStore';
import { ocrWithZerox } from '@/lib/ocr/zeroxService';
import { discoverFields } from '@/lib/ocr/fieldDiscovery';
import { DEV_MODE, MOCK_USER } from '@/lib/dev';
import { createServerSupabaseClient } from '@/lib/supabase/server';

export async function POST(request: NextRequest) {
  try {
    // Authenticate
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

    const { formId, skillFieldIds } = await request.json();

    if (!formId) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'Form ID is required.' } },
        { status: 400 }
      );
    }

    const stored = await getPdf(formId);
    if (!stored) {
      return NextResponse.json(
        { success: false, error: { code: 'FORM_NOT_FOUND', message: 'PDF not found.' } },
        { status: 404 }
      );
    }

    // Step 1: OCR the document with Zerox + Claude vision
    const ocrResult = await ocrWithZerox(stored.bytes, stored.filename);

    // Step 2: Discover fields from the OCR output
    const fields = await discoverFields(ocrResult, skillFieldIds);

    return NextResponse.json({
      success: true,
      data: {
        formId,
        fields,
        fieldCount: fields.length,
        ocrMarkdown: ocrResult.fullMarkdown,
        tokens: {
          input: ocrResult.inputTokens,
          output: ocrResult.outputTokens,
        },
        method: 'zerox',
      },
    });
  } catch (error) {
    console.error('Field detection error:', error);
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'DETECTION_FAILED',
          message: error instanceof Error ? error.message : 'Failed to detect fields.',
        },
      },
      { status: 500 }
    );
  }
}
