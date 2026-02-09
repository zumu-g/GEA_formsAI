import { NextRequest, NextResponse } from 'next/server';
import { getPDFPageCount } from '@/lib/pdf/filler';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File | null;

    if (!file) {
      return NextResponse.json(
        { success: false, error: { code: 'NO_FILE', message: 'No file provided.' } },
        { status: 400 }
      );
    }

    if (file.type !== 'application/pdf') {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_TYPE', message: 'Only PDF files are accepted.' } },
        { status: 400 }
      );
    }

    if (file.size > 25 * 1024 * 1024) {
      return NextResponse.json(
        { success: false, error: { code: 'FILE_TOO_LARGE', message: 'File must be under 25MB.' } },
        { status: 400 }
      );
    }

    const buffer = await file.arrayBuffer();
    const pdfBytes = new Uint8Array(buffer);
    const pageCount = await getPDFPageCount(pdfBytes);

    if (pageCount > 100) {
      return NextResponse.json(
        { success: false, error: { code: 'TOO_MANY_PAGES', message: 'PDF must have 100 pages or fewer.' } },
        { status: 400 }
      );
    }

    // TODO: Upload to S3 / Supabase Storage
    // TODO: Create form record in database
    // TODO: Return form ID

    const formId = crypto.randomUUID();

    return NextResponse.json({
      success: true,
      data: {
        id: formId,
        originalName: file.name,
        fileSize: file.size,
        pageCount,
        status: 'uploaded',
      },
    });
  } catch (error) {
    console.error('Upload error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'UPLOAD_FAILED', message: 'Failed to upload file.' } },
      { status: 500 }
    );
  }
}
