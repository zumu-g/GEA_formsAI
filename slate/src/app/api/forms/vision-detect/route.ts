export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import type { ContentBlockParam } from '@anthropic-ai/sdk/resources/messages/messages';
import { getPdf } from '@/lib/services/pdfStore';
import type { DetectedField, PageDimension, VisionDetectResult } from '@/types/smartFill';

const FORM_FILLING_BACKEND_URL =
  process.env.FORM_FILLING_BACKEND_URL ?? 'http://localhost:8000';

const VISION_PROMPT = `You are a form field detector. Analyse this PDF form page image and identify every fillable field.

Return ONLY a JSON array (no markdown, no explanation) with this structure for each field:
[
  {
    "id": "snake_case_unique_id",
    "label": "Human Readable Label",
    "type": "text|checkbox|date|currency|signature|textarea",
    "bbox": { "x": 0.1, "y": 0.2, "w": 0.3, "h": 0.05 },
    "required": true,
    "profileKey": "full_name|email|phone|address_line_1|company_name|date_of_birth|abn|licence_number or null",
    "confidence": 0.9
  }
]

Rules:
- bbox values are normalised 0-1 (x=left edge / page width, y=top edge / page height, w=width/page width, h=height/page height)
- type "currency" for dollar amounts, "date" for date fields, "signature" for signature boxes
- profileKey must be one of: full_name, first_name, last_name, email, phone, address_line_1, city, state, zip_code, company_name, abn, date_of_birth, licence_number — or null
- If no fillable fields on this page, return []`;

// ---------------------------------------------------------------------------
// Parse Claude's text response into DetectedField[]
// ---------------------------------------------------------------------------
function parseClaudeResponse(
  text: string,
  pageNumber: number,
): DetectedField[] {
  // Strip any accidental markdown fences
  const cleaned = text
    .replace(/^```(?:json)?\s*/i, '')
    .replace(/```\s*$/, '')
    .trim();

  const raw: unknown[] = JSON.parse(cleaned);
  if (!Array.isArray(raw)) return [];

  return raw.map((item) => {
    const f = item as Record<string, unknown>;
    const bbox = (f.bbox as Record<string, number> | undefined) ?? {
      x: 0,
      y: 0,
      w: 0,
      h: 0,
    };
    return {
      id: String(f.id ?? ''),
      label: String(f.label ?? ''),
      type: (f.type as DetectedField['type']) ?? 'text',
      page: pageNumber,
      bbox: {
        x: Number(bbox.x ?? 0),
        y: Number(bbox.y ?? 0),
        w: Number(bbox.w ?? 0),
        h: Number(bbox.h ?? 0),
      },
      required: Boolean(f.required ?? false),
      value: '',
      profileKey:
        f.profileKey !== null && f.profileKey !== undefined
          ? String(f.profileKey)
          : undefined,
      confidence: Number(f.confidence ?? 0.5),
    } satisfies DetectedField;
  });
}

// ---------------------------------------------------------------------------
// Call Claude Vision for a single page image (base64 PNG)
// ---------------------------------------------------------------------------
async function analysePageImage(
  client: Anthropic,
  base64Png: string,
  pageNumber: number,
): Promise<DetectedField[]> {
  const response = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 4096,
    messages: [
      {
        role: 'user',
        content: [
          {
            type: 'image',
            source: {
              type: 'base64',
              media_type: 'image/png',
              data: base64Png,
            },
          },
          {
            type: 'text',
            text: VISION_PROMPT,
          },
        ],
      },
    ],
  });

  const textBlock = response.content.find((b) => b.type === 'text');
  if (!textBlock || textBlock.type !== 'text') return [];

  try {
    return parseClaudeResponse(textBlock.text, pageNumber);
  } catch {
    console.error(`[vision-detect] Failed to parse Claude response for page ${pageNumber}`);
    return [];
  }
}

// ---------------------------------------------------------------------------
// Fallback: send raw PDF bytes as a document block (Claude reads PDFs natively)
// ---------------------------------------------------------------------------
async function analyseRawPdf(
  client: Anthropic,
  pdfBytes: Uint8Array,
): Promise<{ fields: DetectedField[]; pageCount: number }> {
  const base64Pdf = Buffer.from(pdfBytes).toString('base64');

  const documentBlock: ContentBlockParam = {
    type: 'document',
    source: {
      type: 'base64',
      media_type: 'application/pdf',
      data: base64Pdf,
    },
  };

  const response = await client.messages.create({
    model: 'claude-sonnet-4-6',
    max_tokens: 4096,
    messages: [
      {
        role: 'user',
        content: [
          documentBlock,
          {
            type: 'text',
            text: VISION_PROMPT,
          },
        ],
      },
    ],
  });

  const textBlock = response.content.find((b) => b.type === 'text');
  if (!textBlock || textBlock.type !== 'text') {
    return { fields: [], pageCount: 0 };
  }

  let fields: DetectedField[] = [];
  try {
    const raw = parseClaudeResponse(textBlock.text, 1);
    // Approximate stacked vertical positions for fallback (no real page images)
    fields = raw.map((f, i) => ({
      ...f,
      bbox: { x: 0.05, y: i * 0.05, w: 0.9, h: 0.05 },
    }));
  } catch {
    console.error('[vision-detect] Failed to parse Claude response in PDF fallback');
  }

  return { fields, pageCount: 1 };
}

// ---------------------------------------------------------------------------
// POST /api/forms/vision-detect
// ---------------------------------------------------------------------------
export async function POST(request: NextRequest): Promise<NextResponse> {
  let body: { formId?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json(
      { error: 'Invalid JSON body.' },
      { status: 400 },
    );
  }

  const { formId } = body;
  if (!formId) {
    return NextResponse.json(
      { error: 'formId is required.' },
      { status: 400 },
    );
  }

  const stored = getPdf(formId);
  if (!stored) {
    return NextResponse.json(
      { error: 'PDF not found. Please upload the form first.' },
      { status: 404 },
    );
  }

  const client = new Anthropic(
    process.env.ANTHROPIC_API_KEY ? { apiKey: process.env.ANTHROPIC_API_KEY } : {}
  );

  // -------------------------------------------------------------------------
  // Step 1: Ask the Python backend to render the PDF pages to PNG images
  // -------------------------------------------------------------------------
  let pageImages: string[] = [];
  let pageDimensions: PageDimension[] = [];
  let pageCount = 0;
  let backendAvailable = false;

  try {
    const formData = new FormData();
    // Convert Uint8Array to a plain ArrayBuffer so Blob accepts it without
    // TypeScript complaining about SharedArrayBuffer vs ArrayBuffer.
    const buffer = stored.bytes.buffer.slice(
      stored.bytes.byteOffset,
      stored.bytes.byteOffset + stored.bytes.byteLength,
    ) as ArrayBuffer;
    const blob = new Blob([buffer], { type: 'application/pdf' });
    formData.append('file', blob, stored.filename);

    const backendResponse = await fetch(
      `${FORM_FILLING_BACKEND_URL}/pdf/pages`,
      {
        method: 'POST',
        body: formData,
        signal: AbortSignal.timeout(60_000),
      },
    );

    if (backendResponse.ok) {
      const data = (await backendResponse.json()) as {
        pages: Array<{ page: number; image: string; width?: number; height?: number }>;
        count: number;
      };
      pageImages = data.pages.map((p) => p.image);
      pageDimensions = data.pages.map((p) => ({
        width: p.width ?? 595.28,
        height: p.height ?? 841.89,
      }));
      pageCount = data.count;
      backendAvailable = true;
    } else {
      console.warn(
        `[vision-detect] Backend returned ${backendResponse.status} — falling back to raw PDF analysis.`,
      );
    }
  } catch (err) {
    console.warn('[vision-detect] Backend unreachable — falling back to raw PDF analysis.', err);
  }

  // -------------------------------------------------------------------------
  // Step 2a: Analyse each page image with Claude Vision
  // -------------------------------------------------------------------------
  if (backendAvailable && pageImages.length > 0) {
    const allFields: DetectedField[] = [];

    for (let i = 0; i < pageImages.length; i++) {
      try {
        const fields = await analysePageImage(client, pageImages[i], i + 1);
        allFields.push(...fields);
      } catch (err) {
        console.error(`[vision-detect] Claude Vision failed for page ${i + 1}:`, err);
      }
    }

    const result: VisionDetectResult = {
      fields: allFields,
      pageImages,
      pageCount,
      pageDimensions,
    };

    return NextResponse.json(result);
  }

  // -------------------------------------------------------------------------
  // Step 2b: Fallback — send raw PDF to Claude Vision directly
  // -------------------------------------------------------------------------
  try {
    const { fields, pageCount: fallbackPageCount } = await analyseRawPdf(
      client,
      stored.bytes,
    );

    const result: VisionDetectResult = {
      fields,
      pageImages: [],
      pageCount: fallbackPageCount,
      pageDimensions: [{ width: 595.28, height: 841.89 }],
    };

    return NextResponse.json(result);
  } catch (err) {
    console.error('[vision-detect] Raw PDF fallback failed:', err);
    const result: VisionDetectResult = {
      fields: [],
      pageImages: [],
      pageCount: 0,
      pageDimensions: [{ width: 595.28, height: 841.89 }],
      error: 'Parse failed',
    };
    return NextResponse.json(result);
  }
}
