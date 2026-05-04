// In-memory PDF store for uploaded files (until Supabase Storage is wired up).
//
// Stored on globalThis so the Map survives Next.js Turbopack hot-module
// reloads in dev — without this, the route module is recompiled on first
// access, re-evaluating `new Map()` and wiping any previously stored PDFs.

interface PdfEntry {
  bytes: Uint8Array;
  filename: string;
  uploadedAt: number;
}

declare global {
  // eslint-disable-next-line no-var
  var __pdfStore: Map<string, PdfEntry> | undefined;
}

const store: Map<string, PdfEntry> =
  global.__pdfStore ?? (global.__pdfStore = new Map());

export function storePdf(formId: string, bytes: Uint8Array, filename: string) {
  store.set(formId, { bytes, filename, uploadedAt: Date.now() });
}

export function getPdf(formId: string): PdfEntry | null {
  return store.get(formId) ?? null;
}

export function deletePdf(formId: string) {
  store.delete(formId);
}

// Clean up PDFs older than 1 hour
export function cleanupOldPdfs() {
  const oneHour = 60 * 60 * 1000;
  const now = Date.now();
  for (const [id, entry] of store) {
    if (now - entry.uploadedAt > oneHour) {
      store.delete(id);
    }
  }
}
