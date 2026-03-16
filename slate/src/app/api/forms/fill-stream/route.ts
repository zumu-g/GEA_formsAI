import { NextRequest, NextResponse } from 'next/server';
import { fillAgentStream } from '@/lib/services/formFillingBackend';
import { getPdf } from '@/lib/services/pdfStore';

export const runtime = 'nodejs';

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const formId = formData.get('formId') as string;
    const instructions = formData.get('instructions') as string;
    const resumeSessionId = formData.get('resumeSessionId') as string | null;

    if (!formId || !instructions) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'Form ID and instructions are required.' } },
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

    // Collect any context files from the form data
    const contextFiles: { bytes: Uint8Array; name: string }[] = [];
    for (const [key, value] of formData.entries()) {
      if (key === 'contextFile' && value instanceof File) {
        const buf = await value.arrayBuffer();
        contextFiles.push({ bytes: new Uint8Array(buf), name: value.name });
      }
    }

    const backendResponse = await fillAgentStream(stored.bytes, instructions, {
      filename: stored.filename,
      resumeSessionId: resumeSessionId ?? undefined,
      anthropicApiKey: process.env.ANTHROPIC_API_KEY,
      contextFiles: contextFiles.length > 0 ? contextFiles : undefined,
    });

    if (!backendResponse.body) {
      throw new Error('No stream body from backend');
    }

    // Pipe SSE stream from backend to client
    return new Response(backendResponse.body, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        Connection: 'keep-alive',
      },
    });
  } catch (error) {
    console.error('Fill stream error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'STREAM_FAILED', message: 'Failed to start fill stream.' } },
      { status: 500 }
    );
  }
}
