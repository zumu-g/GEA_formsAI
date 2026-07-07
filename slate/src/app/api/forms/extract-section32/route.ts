export const runtime = 'nodejs';
export const maxDuration = 120;

import { NextRequest, NextResponse } from 'next/server';
import { getPdf } from '@/lib/services/pdfStore';
import { doclingExtract } from '@/lib/services/formFillingBackend';
import { extractSection32 } from '@/lib/ai/extractSection32';
import { ocrIfScanned } from '@/lib/services/ocrService';
import type { Section32Extraction } from '@/types/section32Extraction';

/**
 * Minimum amount of extracted, non-whitespace text below which we treat a PDF as
 * scanned/image-based and route it through OCR (or the Claude-vision fallback).
 */
const TEXT_LAYER_MIN_CHARS = 200;

/**
 * POST /api/forms/extract-section32
 * Body: { formId: string }
 *
 * Pipeline: docling text extract → detect scanned → (ocrmypdf if available, else
 * Claude-vision) → Claude structured extraction + summary.
 */
export async function POST(request: NextRequest): Promise<NextResponse> {
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

  // ── STEP 1: extract the text layer (docling) ────────────────────────────────
  let documentText = '';
  let pageCount: number | undefined;
  try {
    const docling = await doclingExtract(stored.bytes, stored.filename);
    documentText = (docling.markdown || '').trim();
    pageCount = Array.isArray(docling.pages) ? docling.pages.length : undefined;
  } catch (err) {
    console.warn(
      '[extract-section32] docling extract unavailable, will rely on OCR/vision:',
      err instanceof Error ? err.message : err,
    );
  }

  const nonWhitespace = documentText.replace(/\s/g, '').length;
  const scanned = nonWhitespace < TEXT_LAYER_MIN_CHARS;

  try {
    // ── STEP 2: digital PDF with a usable text layer → extract straight from text ──
    if (!scanned) {
      const result = await extractSection32({
        documentText,
        method: 'text',
        scanned: false,
        ocrUsed: false,
        pageCount,
      });
      return NextResponse.json(result satisfies Section32Extraction);
    }

    // ── STEP 3: scanned PDF → try ocrmypdf (hybrid), then re-extract its text ────
    const ocr = await ocrIfScanned(stored.bytes, stored.filename);
    if (ocr.ocrUsed && ocr.pdfBytes) {
      try {
        const docling = await doclingExtract(ocr.pdfBytes, stored.filename);
        const ocrText = (docling.markdown || '').trim();
        if (ocrText.replace(/\s/g, '').length >= TEXT_LAYER_MIN_CHARS) {
          const result = await extractSection32({
            documentText: ocrText,
            method: 'ocrmypdf',
            scanned: true,
            ocrUsed: true,
            pageCount,
          });
          return NextResponse.json(result satisfies Section32Extraction);
        }
      } catch (err) {
        console.warn(
          '[extract-section32] post-OCR docling failed, falling back to vision:',
          err instanceof Error ? err.message : err,
        );
      }
    }

    // ── STEP 4: fallback → Claude reads the (scanned) PDF natively ───────────────
    const result = await extractSection32({
      pdfBytes: ocr.pdfBytes ?? stored.bytes,
      method: 'vision',
      scanned: true,
      ocrUsed: ocr.ocrUsed,
      pageCount,
    });
    return NextResponse.json(result satisfies Section32Extraction);
  } catch (err) {
    console.error(
      '[extract-section32] extraction failed:',
      err instanceof Error ? err.message : err,
    );
    return NextResponse.json(
      { error: 'Extraction failed.', detail: err instanceof Error ? err.message : String(err) },
      { status: 500 },
    );
  }
}
