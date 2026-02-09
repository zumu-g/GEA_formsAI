import { NextRequest, NextResponse } from 'next/server';
import { fillPDF } from '@/lib/pdf/filler';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { formId, fieldValues } = body;

    if (!formId || !fieldValues) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'Form ID and field values are required.' } },
        { status: 400 }
      );
    }

    // TODO: Verify user owns this form
    // TODO: Check credits (1 credit for manual, 2 for AI)
    // TODO: Load original PDF from storage
    // TODO: Fill the PDF
    // TODO: Upload filled PDF to storage
    // TODO: Deduct credits
    // TODO: Create fill session record

    return NextResponse.json({
      success: true,
      data: {
        fillSessionId: crypto.randomUUID(),
        downloadUrl: '/api/forms/download/placeholder',
        creditsUsed: 1,
      },
    });
  } catch (error) {
    console.error('Fill error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'FILL_FAILED', message: 'Failed to fill form.' } },
      { status: 500 }
    );
  }
}
