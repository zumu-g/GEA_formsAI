/**
 * Hybrid OCR layer for scanned PDFs.
 *
 * Calls the form-filling backend `/ocr` endpoint (ocrmypdf) to add a searchable text
 * layer. If that endpoint is absent or fails (e.g. ocrmypdf not installed in the
 * deployed runtime), this degrades gracefully — the caller then falls back to Claude
 * reading the PDF natively. No hard dependency is introduced on the slate side.
 */

const BACKEND_URL = process.env.FORM_FILLING_BACKEND_URL || 'http://localhost:8001';

export interface OcrResult {
  /** True only if ocrmypdf actually produced a searchable PDF. */
  ocrUsed: boolean;
  /** The OCR'd PDF bytes when ocrUsed is true; otherwise the original bytes. */
  pdfBytes?: Uint8Array;
}

/**
 * Run ocrmypdf on a (presumed scanned) PDF via the backend. Returns `{ ocrUsed: false }`
 * if the backend `/ocr` endpoint is unavailable so callers can fall back to vision.
 */
export async function ocrIfScanned(
  pdfBytes: Uint8Array,
  filename: string = 'document.pdf',
): Promise<OcrResult> {
  try {
    const formData = new FormData();
    formData.append('file', new Blob([Buffer.from(pdfBytes)], { type: 'application/pdf' }), filename);

    const res = await fetch(`${BACKEND_URL}/ocr`, {
      method: 'POST',
      body: formData,
      signal: AbortSignal.timeout(120_000),
    });

    if (!res.ok) {
      // 404 → endpoint not deployed; any other error → OCR failed. Either way, fall back.
      console.warn(`[ocrService] /ocr returned ${res.status} ${res.statusText}; falling back.`);
      return { ocrUsed: false, pdfBytes };
    }

    const buf = new Uint8Array(await res.arrayBuffer());
    if (buf.length === 0) return { ocrUsed: false, pdfBytes };
    return { ocrUsed: true, pdfBytes: buf };
  } catch (err) {
    console.warn(
      '[ocrService] ocrmypdf unavailable, falling back to vision:',
      err instanceof Error ? err.message : err,
    );
    return { ocrUsed: false, pdfBytes };
  }
}
