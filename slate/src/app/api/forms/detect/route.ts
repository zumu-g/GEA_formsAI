import { NextRequest, NextResponse } from 'next/server';
import { detectFormFields } from '@/lib/ai/fieldDetection';
import { analyzeForm } from '@/lib/services/formFillingBackend';
import { getPdf } from '@/lib/services/pdfStore';
import type { FormField } from '@/types/form';
import type { BackendFieldInfo } from '@/types/formFillingBackend';

function backendFieldToFormField(field: BackendFieldInfo, formId: string): FormField {
  return {
    id: field.field_id,
    formId,
    fieldName: field.friendly_label || field.native_field_name,
    fieldType: field.field_type === 'dropdown' ? 'dropdown' : field.field_type,
    pageNumber: field.page + 1, // backend is 0-indexed
    x: 0,
    y: 0,
    width: 0,
    height: 0,
    isRequired: false,
    aiDetected: true,
    value: field.current_value ?? undefined,
  };
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { formId, pageImages, useBackend } = body;

    if (!formId) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'Form ID is required.' } },
        { status: 400 }
      );
    }

    // Path 1: Use the form_filling_app backend (PyMuPDF — better for native AcroForm fields)
    if (useBackend !== false) {
      const stored = getPdf(formId);
      if (stored) {
        try {
          const result = await analyzeForm(stored.bytes, stored.filename);
          if (result.success && result.fields.length > 0) {
            const fields = result.fields.map((f) => backendFieldToFormField(f, formId));
            return NextResponse.json({
              success: true,
              data: { formId, fields, fieldCount: fields.length, method: 'acroform' },
            });
          }
        } catch (err) {
          console.warn('Backend analyze failed, falling back to vision detection:', err);
        }
      }
    }

    // Path 2: Vision-based detection (for scanned PDFs without AcroForm fields)
    if (!pageImages?.length) {
      return NextResponse.json(
        { success: false, error: { code: 'NO_FIELDS', message: 'No form fields detected and no page images provided for vision detection.' } },
        { status: 400 }
      );
    }

    const detectedFields = await detectFormFields(pageImages);

    return NextResponse.json({
      success: true,
      data: {
        formId,
        fields: detectedFields,
        fieldCount: detectedFields.length,
        method: 'vision',
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
