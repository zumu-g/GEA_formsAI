// In-memory PDF store for uploaded files (until Supabase Storage is wired up)
// Keys are form IDs, values are PDF bytes

const store = new Map<string, { bytes: Uint8Array; filename: string; uploadedAt: number }>();

export function storePdf(formId: string, bytes: Uint8Array, filename: string) {
  store.set(formId, { bytes, filename, uploadedAt: Date.now() });
}

export function getPdf(formId: string) {
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
