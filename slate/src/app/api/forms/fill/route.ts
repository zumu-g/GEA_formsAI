import { NextRequest, NextResponse } from 'next/server';
import { fillPDF } from '@/lib/pdf/filler';
import { fillAgent } from '@/lib/services/formFillingBackend';
import { getPdf } from '@/lib/services/pdfStore';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { formId, fieldValues, instructions, useAgent } = body;

    if (!formId) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'Form ID is required.' } },
        { status: 400 }
      );
    }

    const stored = getPdf(formId);
    if (!stored) {
      return NextResponse.json(
        { success: false, error: { code: 'FORM_NOT_FOUND', message: 'Uploaded PDF not found. Please re-upload.' } },
        { status: 404 }
      );
    }

    // Path 1: AI Agent fill (natural language instructions)
    if (useAgent && instructions) {
      const result = await fillAgent(stored.bytes, instructions, {
        filename: stored.filename,
        anthropicApiKey: process.env.ANTHROPIC_API_KEY,
      });

      const base64 = Buffer.from(result.pdfBytes).toString('base64');

      return NextResponse.json({
        success: true,
        data: {
          fillSessionId: result.sessionId,
          pdfBase64: base64,
          creditsUsed: 2,
          fillMethod: 'ai_auto',
        },
      });
    }

    // Path 2: Direct field-value fill (manual or template)
    if (!fieldValues) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'Field values or instructions are required.' } },
        { status: 400 }
      );
    }

    const fields = Object.entries(fieldValues).map(([fieldName, value]) => ({
      field: {
        id: fieldName,
        formId,
        fieldName,
        fieldType: 'text' as const,
        pageNumber: 1,
        x: 0,
        y: 0,
        width: 100,
        height: 20,
        isRequired: false,
        aiDetected: false,
      },
      value: String(value),
    }));

    const filledBytes = await fillPDF(stored.bytes, fields);
    const base64 = Buffer.from(filledBytes).toString('base64');

    return NextResponse.json({
      success: true,
      data: {
        fillSessionId: crypto.randomUUID(),
        pdfBase64: base64,
        creditsUsed: 1,
        fillMethod: 'manual',
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
