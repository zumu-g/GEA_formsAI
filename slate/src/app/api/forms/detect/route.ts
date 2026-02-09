import { NextRequest, NextResponse } from 'next/server';
import { detectFormFields } from '@/lib/ai/fieldDetection';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { formId, pageImages } = body;

    if (!formId || !pageImages?.length) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'Form ID and page images are required.' } },
        { status: 400 }
      );
    }

    // TODO: Verify user owns this form
    // TODO: Check user has credits for AI detection (2 credits)

    const detectedFields = await detectFormFields(pageImages);

    // TODO: Save detected fields to database
    // TODO: Deduct credits

    return NextResponse.json({
      success: true,
      data: {
        formId,
        fields: detectedFields,
        fieldCount: detectedFields.length,
      },
    });
  } catch (error) {
    console.error('Detection error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'DETECTION_FAILED', message: 'Failed to detect form fields.' } },
      { status: 500 }
    );
  }
}
