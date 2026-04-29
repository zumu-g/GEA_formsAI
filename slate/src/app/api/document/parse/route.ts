import { NextRequest, NextResponse } from 'next/server';
import { parseDocument, extractTextForLLM } from '@/lib/services/unstructuredClient';

const MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024;

export async function POST(request: NextRequest) {
  try {
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
        { success: false, error: { code: 'FILE_TOO_LARGE', message: 'File exceeds the 50MB limit.' } },
        { status: 413 }
      );
    }

    const filename = file instanceof File ? file.name : 'document';
    const arrayBuffer = await file.arrayBuffer();
    const fileBytes = new Uint8Array(arrayBuffer);

    const elements = await parseDocument(fileBytes, filename);
    const textForLLM = extractTextForLLM(elements);

    return NextResponse.json({
      success: true,
      data: { elements, textForLLM },
    });
  } catch (error) {
    console.error('Document parse error:', error);

    if (error instanceof Error && error.message === 'UNSTRUCTURED_API_KEY not configured') {
      return NextResponse.json(
        { success: false, error: { code: 'SERVICE_NOT_CONFIGURED', message: 'Document parsing service is not configured.' } },
        { status: 503 }
      );
    }

    return NextResponse.json(
      { success: false, error: { code: 'PARSE_FAILED', message: 'Failed to parse document.' } },
      { status: 500 }
    );
  }
}
