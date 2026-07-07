export const runtime = 'nodejs';
export const maxDuration = 120;

import { NextRequest, NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import type { ContentBlockParam } from '@anthropic-ai/sdk/resources/messages/messages';
import { getPdf } from '@/lib/services/pdfStore';
import { analyzeForm, detectFieldsDocling, detectFieldsPdfplumber, detectFieldsCommonForms } from '@/lib/services/formFillingBackend';
import { ocrWithZerox } from '@/lib/ocr/zeroxService';
import { discoverFields } from '@/lib/ocr/fieldDiscovery';
import type { DiscoveredField } from '@/lib/ocr/fieldDiscovery';
import type { DetectedField, PageDimension, SmartDetectResult, DetectionMethod } from '@/types/smartFill';
import type { BackendFieldInfo } from '@/types/formFillingBackend';
import { detectWithGoogleDocumentAI, isGoogleDocAIConfigured } from '@/lib/services/googleDocumentAI';

const FORM_FILLING_BACKEND_URL =
  process.env.FORM_FILLING_BACKEND_URL ?? 'http://localhost:8001';

const VISION_PROMPT = `You are a form field detector. Analyse this PDF form page image and identify every fillable field.

Look for: blank lines, underscored areas, boxes/rectangles, checkboxes, radio buttons, signature lines, date fields, and any space where someone would write or type information.

Return ONLY a valid JSON array — no explanation, no markdown, no preamble. Start your response with [ and end with ].

Each element must be:
{
  "id": "snake_case_unique_id",
  "label": "Human Readable Label from nearby text",
  "type": "text|checkbox|date|currency|signature|textarea",
  "bbox": { "x": 0.1, "y": 0.2, "w": 0.3, "h": 0.05 },
  "required": false,
  "profileKey": null,
  "confidence": 0.8
}

Rules:
- bbox: normalised 0–1 (x=left/pageWidth, y=top/pageHeight, w=fieldWidth/pageWidth, h=fieldHeight/pageHeight)
- Include ALL fields, even if partially filled or hard to read
- type: "currency" for dollar amounts, "date" for dates, "signature" for signature lines, "checkbox" for tick boxes
- If no fillable fields exist on this page, return: []`;

// ---------------------------------------------------------------------------
// Parse Claude's text response into DetectedField[]
// ---------------------------------------------------------------------------
function parseClaudeResponse(
  text: string,
  pageNumber: number,
): DetectedField[] {
  try {
    // Strip UTF-8 BOM and markdown fences
    let cleaned = text
      .replace(/^﻿/, '')
      .replace(/^```(?:json)?\s*/im, '')
      .replace(/```\s*$/m, '')
      .trim();

    // Extract first JSON array or object from anywhere in the string
    // This handles cases where Claude adds explanatory text before the JSON
    const arrayMatch = cleaned.match(/\[[\s\S]*\]/);
    const objectMatch = cleaned.match(/\{[\s\S]*\}/);
    if (arrayMatch) {
      cleaned = arrayMatch[0];
    } else if (objectMatch) {
      cleaned = objectMatch[0];
    } else {
      return [];
    }

    let raw: unknown = JSON.parse(cleaned);

    // Handle wrapped format: {"fields": [...]} or {"data": [...]}
    if (!Array.isArray(raw) && raw !== null && typeof raw === 'object') {
      const obj = raw as Record<string, unknown>;
      if (Array.isArray(obj.fields)) raw = obj.fields;
      else if (Array.isArray(obj.data)) raw = obj.data;
    }

    if (!Array.isArray(raw)) return [];

    return (raw as unknown[]).map((item) => {
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
  } catch {
    console.error(`[detect-smart] Failed to parse Claude response for page ${pageNumber}`);
    return [];
  }
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
    max_tokens: 8192,
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

  return parseClaudeResponse(textBlock.text, pageNumber);
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
    max_tokens: 8192,
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

  const raw = parseClaudeResponse(textBlock.text, 1);
  // Approximate stacked vertical positions for fallback (no real page images)
  const fields = raw.map((f, i) => ({
    ...f,
    bbox: { x: 0.05, y: i * 0.05, w: 0.9, h: 0.05 },
  }));

  return { fields, pageCount: 1 };
}

// ---------------------------------------------------------------------------
// Helper: convert BackendFieldInfo to DetectedField
// ---------------------------------------------------------------------------
function backendFieldToDetected(f: BackendFieldInfo): DetectedField {
  // BackendFieldInfo bbox: [x0, y0, x1, y1] in PDF points
  // PDF A4 dimensions in points: 595.28 x 841.89 (use as defaults if page dimensions unknown)
  const pageW = 595.28;
  const pageH = 841.89;
  const bbox = f.bbox ?? [0, 0, 100, 20];
  return {
    id: f.field_id,
    label: f.friendly_label || f.native_field_name || f.field_id,
    type: (f.field_type as DetectedField['type']) ?? 'text',
    page: (f.page ?? 0) + 1, // 0-indexed → 1-indexed
    bbox: {
      x: bbox[0] / pageW,
      y: bbox[1] / pageH,
      w: (bbox[2] - bbox[0]) / pageW,
      h: (bbox[3] - bbox[1]) / pageH,
    },
    required: false,
    value: f.current_value ?? '',
    profileKey: undefined,
    confidence: 0.9, // AcroForm fields are high confidence
  } satisfies DetectedField;
}

// ---------------------------------------------------------------------------
// Adapter: convert DiscoveredField[] (zerox output) to DetectedField[]
// ---------------------------------------------------------------------------
function discoveredToDetected(fields: DiscoveredField[], pageDimCount: number): DetectedField[] {
  void pageDimCount; // retained for API symmetry; unused in mapping logic

  const yFromPosition: Record<string, number> = {
    top: 0.05,
    middle: 0.45,
    bottom: 0.80,
  };

  return fields.map((df, index) => {
    const y = yFromPosition[df.approximatePosition] ?? 0.45;
    const rawId = `${df.fieldName}_p${df.page}_${index}`
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '')
      .slice(0, 60);
    return {
      id: rawId || `field_${index}`,
      label: df.fieldName,
      type: df.fieldType satisfies DetectedField['type'],
      page: df.page,
      bbox: { x: 0.05, y, w: 0.90, h: 0.04 },
      required: false,
      value: df.currentValue ?? '',
      profileKey: undefined,
      confidence: 0.5,
    } satisfies DetectedField;
  });
}

// ---------------------------------------------------------------------------
// POST /api/forms/detect-smart
// ---------------------------------------------------------------------------
export async function POST(request: NextRequest): Promise<NextResponse> {
  // 1. Parse body
  let body: { formId?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body.' }, { status: 400 });
  }

  const { formId } = body;
  if (!formId) return NextResponse.json({ error: 'formId is required.' }, { status: 400 });

  const stored = getPdf(formId);
  if (!stored) return NextResponse.json({ error: 'PDF not found.' }, { status: 404 });

  const client = new Anthropic(
    process.env.ANTHROPIC_API_KEY ? { apiKey: process.env.ANTHROPIC_API_KEY } : {}
  );

  // ── Fetch page images in parallel with detection (non-blocking) ──────────
  let pageImages: string[] = [];
  let pageDimensions: PageDimension[] = [];
  let pageCount = 0;

  const pdfBlob = new Blob(
    [stored.bytes.buffer.slice(
      stored.bytes.byteOffset,
      stored.bytes.byteOffset + stored.bytes.byteLength,
    ) as ArrayBuffer],
    { type: 'application/pdf' },
  );

  const pageImagesPromise = (async () => {
    try {
      const fd = new FormData();
      fd.append('file', pdfBlob, stored.filename);
      const res = await fetch(`${FORM_FILLING_BACKEND_URL}/pdf/pages`, {
        method: 'POST',
        body: fd,
        signal: AbortSignal.timeout(60_000),
      });
      if (res.ok) {
        const data = await res.json() as {
          pages: Array<{ page: number; image: string; width?: number; height?: number }>;
          count: number;
        };
        pageImages = data.pages.map(p => p.image);
        pageCount = data.count;
        pageDimensions = data.pages.map(p => ({
          width: p.width ?? 595.28,
          height: p.height ?? 841.89,
        }));
      }
    } catch (err) {
      console.warn(
        '[detect-smart] Backend unavailable for page images — PDF viewer will use iframe fallback:',
        err instanceof Error ? err.message : err,
      );
    }
  })();

  // ── STEP 1: AcroForm detection (no AI, instant) ──────────────────────────
  try {
    const result = await analyzeForm(stored.bytes, stored.filename);
    const backendFields = result.fields ?? [];
    if (backendFields.length > 0) {
      console.log(`[detect-smart] AcroForm detected ${backendFields.length} native fields`);
      await pageImagesPromise;
      return NextResponse.json({
        fields: backendFields.map(f => backendFieldToDetected(f)),
        pageImages,
        pageCount: pageCount || 1,
        pageDimensions: pageDimensions.length
          ? pageDimensions
          : [{ width: 595.28, height: 841.89 }],
        detectionMethod: 'acroform' as DetectionMethod,
      } satisfies SmartDetectResult);
    }
  } catch (err) {
    console.warn(
      '[detect-smart] AcroForm detection skipped:',
      err instanceof Error ? err.message : err,
    );
  }

  // ── STEP 1.5: pdfplumber visual field detection (digital PDFs with drawn boxes) ──
  try {
    const pdfplumberResult = await detectFieldsPdfplumber(stored.bytes, stored.filename);
    const pdfplumberFields = pdfplumberResult.fields ?? [];
    if (pdfplumberFields.length > 0) {
      console.log(`[detect-smart] pdfplumber detected ${pdfplumberFields.length} fields`);
      await pageImagesPromise;
      return NextResponse.json({
        fields: pdfplumberFields.map(f => backendFieldToDetected(f)),
        pageImages,
        pageCount: pageCount || 1,
        pageDimensions: pageDimensions.length ? pageDimensions : [{ width: 595.28, height: 841.89 }],
        detectionMethod: 'pdfplumber' as DetectionMethod,
      } satisfies SmartDetectResult);
    }
  } catch (err) {
    console.warn('[detect-smart] pdfplumber skipped:', err instanceof Error ? err.message : err);
  }

  // ── STEP 1.75: CommonForms ML blank-field detection (all PDFs incl. scanned) ──
  try {
    const cfResult = await detectFieldsCommonForms(stored.bytes, stored.filename);
    const cfFields = cfResult.fields ?? [];
    if (cfFields.length > 0) {
      console.log(`[detect-smart] CommonForms detected ${cfFields.length} fields`);
      await pageImagesPromise;
      return NextResponse.json({
        fields: cfFields.map(f => backendFieldToDetected(f)),
        pageImages,
        pageCount: pageCount || 1,
        pageDimensions: pageDimensions.length ? pageDimensions : [{ width: 595.28, height: 841.89 }],
        detectionMethod: 'commonforms' as DetectionMethod,
      } satisfies SmartDetectResult);
    }
  } catch (err) {
    console.warn('[detect-smart] CommonForms skipped:', err instanceof Error ? err.message : err);
  }

  // ── STEP 2: Google Document AI Form Parser ──────────────────────────────────
  if (isGoogleDocAIConfigured()) {
    try {
      console.log('[detect-smart] Trying Google Document AI Form Parser');
      const gdaiFields = await detectWithGoogleDocumentAI(stored.bytes);
      if (gdaiFields.length > 0) {
        console.log(`[detect-smart] Google Doc AI detected ${gdaiFields.length} fields`);
        await pageImagesPromise;
        return NextResponse.json({
          fields: gdaiFields,
          pageImages,
          pageCount: pageCount || 1,
          pageDimensions: pageDimensions.length
            ? pageDimensions
            : [{ width: 595.28, height: 841.89 }],
          detectionMethod: 'docai' as DetectionMethod,
        } satisfies SmartDetectResult);
      }
    } catch (err) {
      console.warn(
        '[detect-smart] Google Document AI skipped:',
        err instanceof Error ? err.message : err,
      );
    }
  }

  // ── STEP 2.5: Docling structured document analysis ────────────────────────
  try {
    console.log('[detect-smart] Trying Docling structured field detection');
    const doclingResult = await detectFieldsDocling(stored.bytes, stored.filename);
    const doclingFields = doclingResult.fields ?? [];
    if (doclingFields.length > 0) {
      console.log(`[detect-smart] Docling detected ${doclingFields.length} fields`);
      await pageImagesPromise;
      return NextResponse.json({
        fields: doclingFields.map(f => backendFieldToDetected(f)),
        pageImages,
        pageCount: pageCount || 1,
        pageDimensions: pageDimensions.length
          ? pageDimensions
          : [{ width: 595.28, height: 841.89 }],
        detectionMethod: 'docling' as DetectionMethod,
      } satisfies SmartDetectResult);
    }
  } catch (err) {
    console.warn(
      '[detect-smart] Docling detection skipped:',
      err instanceof Error ? err.message : err,
    );
  }

  // ── STEP 3: Zerox OCR fallback ────────────────────────────────────────────
  try {
    console.log('[detect-smart] Trying Zerox OCR');
    const ocrResult = await ocrWithZerox(stored.bytes, stored.filename);
    const discovered = await discoverFields(ocrResult);
    if (discovered.length > 0) {
      await pageImagesPromise;
      const zeroxPageCount = ocrResult.pages?.length ?? 1;
      return NextResponse.json({
        fields: discoveredToDetected(discovered, zeroxPageCount),
        pageImages,
        pageCount: pageCount || zeroxPageCount,
        pageDimensions: pageDimensions.length
          ? pageDimensions
          : Array.from({ length: zeroxPageCount }, () => ({ width: 595.28, height: 841.89 })),
        detectionMethod: 'zerox' as DetectionMethod,
      } satisfies SmartDetectResult);
    }
  } catch (err) {
    console.warn(
      '[detect-smart] Zerox fallback skipped:',
      err instanceof Error ? err.message : err,
    );
  }

  // ── STEP 4: Claude Vision (per-page images or raw PDF) ───────────────────
  await pageImagesPromise; // ensure images are ready
  const visionFields: DetectedField[] = [];

  if (pageImages.length > 0) {
    for (let i = 0; i < pageImages.length; i++) {
      try {
        const fields = await analysePageImage(client, pageImages[i], i + 1);
        visionFields.push(...fields);
      } catch (err) {
        console.error(
          `[detect-smart] Vision failed for page ${i + 1}:`,
          err instanceof Error ? err.message : err,
        );
      }
    }
  } else {
    // Raw PDF fallback
    try {
      const { fields } = await analyseRawPdf(client, stored.bytes);
      visionFields.push(...fields);
    } catch (err) {
      console.error(
        '[detect-smart] Raw PDF vision failed:',
        err instanceof Error ? err.message : err,
      );
    }
  }

  if (visionFields.length > 0) {
    return NextResponse.json({
      fields: visionFields,
      pageImages,
      pageCount: pageCount || 1,
      pageDimensions: pageDimensions.length ? pageDimensions : [{ width: 595.28, height: 841.89 }],
      detectionMethod: 'vision' as DetectionMethod,
    } satisfies SmartDetectResult);
  }

  // ── STEP 5: Empty ─────────────────────────────────────────────────────────
  return NextResponse.json({
    fields: [],
    pageImages,
    pageCount: pageCount || 0,
    pageDimensions,
    detectionMethod: 'empty' as DetectionMethod,
  } satisfies SmartDetectResult);
}
