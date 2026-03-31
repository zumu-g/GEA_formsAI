import { NextRequest, NextResponse } from 'next/server';
import { getPdfUrl, getPdf } from '@/lib/services/pdfStore';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ formId: string }> }
) {
  try {
    const { formId } = await params;

    if (!formId) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'Form ID is required.' } },
        { status: 400 }
      );
    }

    // Try to get a signed URL (works when Supabase Storage is available)
    const signedUrl = await getPdfUrl(formId);

    if (signedUrl) {
      return NextResponse.redirect(signedUrl);
    }

    // Fallback: serve PDF bytes directly from getPdf (covers in-memory store)
    const pdf = await getPdf(formId);

    if (!pdf) {
      return NextResponse.json(
        { success: false, error: { code: 'NOT_FOUND', message: 'PDF not found.' } },
        { status: 404 }
      );
    }

    return new NextResponse(Buffer.from(pdf.bytes), {
      status: 200,
      headers: {
        'Content-Type': 'application/pdf',
        'Content-Disposition': `inline; filename="${pdf.filename}"`,
        'Content-Length': String(pdf.bytes.length),
      },
    });
  } catch (error) {
    console.error('PDF serve error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'SERVE_FAILED', message: 'Failed to serve PDF.' } },
      { status: 500 }
    );
  }
}
