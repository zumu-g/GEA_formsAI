import { NextRequest, NextResponse } from 'next/server';
import { getPdf } from '@/lib/services/pdfStore';
import { DEV_MODE } from '@/lib/dev';
import { createServerSupabaseClient } from '@/lib/supabase/server';
import type { DoclingExtractResult, DoclingTextBlock } from '@/lib/services/formFillingBackend';

function ptsToMm(pts: number): number { return pts * 25.4 / 72; }

function convertBbox(bbox: { x0: number; y0: number; x1: number; y1: number }, pageHeightPts = 841.89) {
  return {
    x0: ptsToMm(bbox.x0),
    y0: ptsToMm(pageHeightPts - bbox.y1),
    x1: ptsToMm(bbox.x1),
    y1: ptsToMm(pageHeightPts - bbox.y0),
  };
}

interface CalibrationHint {
  possibleLabel: string;
  page: number;
  suggestedX: number;
  suggestedY: number;
  bboxMm: { x0: number; y0: number; x1: number; y1: number };
}

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

    const { formId, skillId } = await request.json();

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

    const backendUrl = process.env.FORM_FILLING_BACKEND_URL || 'http://localhost:8000';
    const formData = new FormData();
    formData.append('file', new Blob([Buffer.from(stored.bytes)], { type: 'application/pdf' }), stored.filename);

    const doclingRes = await fetch(`${backendUrl}/docling/extract`, { method: 'POST', body: formData });

    if (!doclingRes.ok) {
      throw new Error(`Docling extract failed: ${doclingRes.status} ${doclingRes.statusText}`);
    }

    const doclingData: DoclingExtractResult = await doclingRes.json();

    const allBlocks: DoclingTextBlock[] = [
      ...(doclingData.text_blocks ?? []),
      ...(doclingData.tables ?? []),
    ];

    const pageCount = doclingData.pages?.length ?? 0;

    const calibrationHints: CalibrationHint[] = allBlocks.map((block) => {
      const bboxMm = convertBbox(block.bbox);
      return {
        possibleLabel: block.text.slice(0, 60),
        page: block.page,
        suggestedX: bboxMm.x1 + 2,
        suggestedY: bboxMm.y0,
        bboxMm,
      };
    });

    return NextResponse.json({
      success: true,
      data: {
        formId,
        skillId: skillId ?? null,
        textBlocks: allBlocks,
        pageCount,
        calibrationHints,
      },
    });
  } catch (error) {
    console.error('Calibration error:', error);
    return NextResponse.json(
      {
        success: false,
        error: {
          code: 'CALIBRATION_FAILED',
          message: error instanceof Error ? error.message : 'Failed to calibrate form.',
        },
      },
      { status: 500 }
    );
  }
}
