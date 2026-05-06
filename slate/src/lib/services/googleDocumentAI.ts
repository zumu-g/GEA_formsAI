import type { DetectedField } from '@/types/smartFill';

const PROJECT_ID = process.env.GOOGLE_CLOUD_PROJECT_ID;
const LOCATION = process.env.GOOGLE_CLOUD_LOCATION ?? 'us';
const PROCESSOR_ID = process.env.GOOGLE_DOCUMENT_AI_PROCESSOR_ID;

export function isGoogleDocAIConfigured(): boolean {
  return Boolean(PROJECT_ID && PROCESSOR_ID);
}

function inferFieldType(label: string, value: string): DetectedField['type'] {
  const l = label.toLowerCase();
  if (/date|dob|born|expir|settlement/.test(l)) return 'date';
  if (/sign|signature/.test(l)) return 'signature';
  if (/amount|price|fee|\$|cost|total|deposit|purchase/.test(l)) return 'currency';
  if (/\byes\b|\bno\b|\bcheck\b|tick|✓|✗/.test(l + value)) return 'checkbox';
  if (/notes?|comments?|description|details|address|remarks/.test(l)) return 'textarea';
  // Real estate-specific patterns (use word boundaries to avoid substring matches)
  if (/commission|\brate\b|percent|%|\bgst\b/.test(l)) return 'currency';
  if (/\bperiod\b|\bfrom\b|\bstart\b|\bend\b/.test(l)) return 'date';
  return 'text';
}

function inferProfileKey(label: string): string | undefined {
  const l = label.toLowerCase();
  if (/full.?name|purchaser.?name|vendor.?name|buyer.?name/.test(l)) return 'full_name';
  if (/\bfirst.?name\b/.test(l)) return 'first_name';
  if (/\blast.?name\b|surname/.test(l)) return 'last_name';
  if (/email/.test(l)) return 'email';
  if (/phone|mobile|contact.?no/.test(l)) return 'phone';
  if (/\baddress\b|street/.test(l)) return 'address_line_1';
  if (/company|business|firm|entity/.test(l)) return 'company_name';
  if (/\babn\b/.test(l)) return 'abn';
  if (/date.of.birth|dob/.test(l)) return 'date_of_birth';
  if (/licence|license/.test(l)) return 'licence_number';
  // Real estate-specific mappings
  if (/\bagent\b/.test(l)) return 'full_name';
  if (/\bvendor\b/.test(l)) return 'full_name';
  if (/city|suburb/.test(l)) return 'city';
  if (/\bstate\b/.test(l)) return 'state';
  if (/postcode|post.?code|zip/.test(l)) return 'zip_code';
  return undefined;
}

// Labels that look like field headers but aren't fill targets
const SKIP_LABELS = new Set([
  'note', 'notes', 'see', 'refer', 'if', 'the', 'this', 'for',
  'and', 'or', 'to', 'of', 'in', 'on', 'at', 'by', 'with',
  // Legal boilerplate words common in Victorian real estate forms
  'pursuant', 'subject', 'whereby', 'herein', 'thereof', 'notwithstanding',
]);

// Known real estate field label keywords — used to relax the colon requirement
const FIELD_KEYWORDS_RELAXED = [
  'commission', 'rate', 'period', 'from', 'gst', 'postcode', 'suburb',
  'state', 'price', 'deposit',
];

// Known standalone field keywords — if label ends with one and has a garbled prefix, use just the keyword
const FIELD_KEYWORDS_CLEAN = [
  'Email', 'Mobile', 'Phone', 'Fax', 'Address', 'Name', 'Date', 'Signature',
  'Agent', 'Vendor', 'ABN', 'Attention', 'Property',
];

// Extract additional fields from text lines (catches labels Form Parser misses)
function extractFieldsFromLines(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  pages: any[],
  fullText: string,
  existingFields: DetectedField[],
  seenIds: Set<string>,
): DetectedField[] {
  const extra: DetectedField[] = [];

  // Build a set of y-positions already covered by Form Parser fields (within 2% tolerance)
  const coveredY = existingFields.map(f => f.bbox.y);
  const isCovered = (y: number, page: number) =>
    existingFields.some(f => f.page === page && Math.abs(f.bbox.y - y) < 0.025);

  for (const page of pages) {
    const pageNum = Number(page.pageNumber ?? 1);
    const lines: unknown[] = page.lines ?? [];

    for (const line of lines) {
      const l = line as Record<string, unknown>;
      const layout = l.layout as Record<string, unknown> | undefined;
      const anchor = layout?.textAnchor as Record<string, unknown> | undefined;
      const segs = anchor?.textSegments as Array<Record<string, unknown>> | undefined;
      if (!segs?.length) continue;

      const start = Number(segs[0].startIndex ?? 0);
      const end = Number(segs[0].endIndex ?? 0);
      const text = fullText.slice(start, end).replace(/\n/g, '').trim();

      if (text.length < 2) continue;

      // For long lines (bleed-through after colon), extract just the prefix before the first ":"
      // e.g. "Agent: 626,morw of bris vthodA..." → candidate = "Agent"
      let candidate = text;
      if (text.length > 35 && text.includes(':')) {
        const prefix = text.split(':')[0].trim();
        if (prefix.length >= 2 && prefix.length <= 30) {
          candidate = prefix + ':'; // re-add colon so downstream logic works
        } else {
          continue; // prefix still too long or empty — skip line
        }
      } else if (text.length > 35) {
        continue; // long line with no colon — not a field label
      }

      const candidateLower = candidate.toLowerCase();
      // Match whole-word keywords only (avoid "rate" inside "incorporated")
      const isKnownKeyword = FIELD_KEYWORDS_RELAXED.some(kw =>
        new RegExp(`\\b${kw}\\b`).test(candidateLower)
      );
      if (!candidate.endsWith(':') && !isKnownKeyword) continue;

      // Skip if it contains mostly non-ASCII (garbled bleed-through text)
      const asciiRatio = (candidate.match(/[\x20-\x7E]/g) ?? []).length / candidate.length;
      if (asciiRatio < 0.85) continue;

      const label = candidate.replace(/:$/, '').trim();
      if (!label) continue;

      // Known standalone field keywords — if label ends with one and has a garbled prefix, use just the keyword
      let cleanLabel = label;
      const lastWord = label.split(/\s+/).pop() ?? '';
      if (FIELD_KEYWORDS_CLEAN.some(kw => kw.toLowerCase() === lastWord.toLowerCase()) && label.split(/\s+/).length > 1) {
        cleanLabel = lastWord;
      }

      // Skip if starts with a digit (legal clause numbering like "1.3 binding offer")
      if (/^\d/.test(cleanLabel)) continue;

      const cleanLabelLower = cleanLabel.toLowerCase();
      const words = cleanLabelLower.split(/\s+/);

      // Skip if first word is a common non-field word
      if (SKIP_LABELS.has(words[0])) continue;
      // Skip very long labels (likely headings, not field labels)
      if (words.length > 4) continue;

      // Detect garbled words: long words with very few vowels (bleed-through text)
      const hasGarbledWord = words.some(w => {
        if (w.length < 5) return false;
        const vowels = (w.match(/[aeiou]/g) ?? []).length;
        return vowels / w.length < 0.15; // < 15% vowels = likely garbled
      });
      if (hasGarbledWord) continue;

      // Skip all-uppercase words longer than 3 chars (bleed-through caps text)
      const hasAllCapsGarble = words.some(w => w.length > 3 && w === w.toUpperCase() && /[A-Z]{4,}/.test(w));
      if (hasAllCapsGarble) continue;

      // Get bounding box
      const poly = layout?.boundingPoly as Record<string, unknown> | undefined;
      const verts = (poly?.normalizedVertices ?? []) as Array<Record<string, number>>;
      if (verts.length < 2) continue;

      const xs = verts.map(v => v.x ?? 0);
      const ys = verts.map(v => v.y ?? 0);
      const y = Math.min(...ys);
      const x = Math.min(...xs);

      // Skip if already covered by Form Parser at this position
      if (isCovered(y, pageNum)) continue;

      // Deduplicate by normalised label — skip if already on this page at same y-position.
      // Allow duplicate labels (e.g. "Address") at different y-positions (> 5% apart).
      const normalizedLabel = cleanLabel.toLowerCase().replace(/[^a-z0-9]/g, '');
      const isDuplicate = [...existingFields, ...extra].some(f =>
        f.page === pageNum &&
        f.label.toLowerCase().replace(/[^a-z0-9]/g, '') === normalizedLabel &&
        Math.abs(f.bbox.y - y) < 0.05
      );
      if (isDuplicate) continue;

      // Build id
      let id = cleanLabel.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 55);
      if (!id) continue;
      const base = id;
      let s = 2;
      while (seenIds.has(id)) id = `${base}_${s++}`;
      seenIds.add(id);

      // Field value area is to the right of and below the label
      extra.push({
        id,
        label: cleanLabel,
        type: inferFieldType(cleanLabel, ''),
        page: pageNum,
        bbox: {
          x: Math.min(x + 0.15, 0.85), // value area starts right of label
          y,
          w: Math.max(0.95 - x - 0.15, 0.1),
          h: 0.025,
        },
        required: false,
        value: '',
        profileKey: inferProfileKey(cleanLabel),
        confidence: 0.6,
      } satisfies DetectedField);
    }
  }

  void coveredY; // suppress unused warning
  return extra;
}

export async function detectWithGoogleDocumentAI(
  pdfBytes: Uint8Array,
): Promise<DetectedField[]> {
  if (!PROJECT_ID || !PROCESSOR_ID) {
    throw new Error('Google Document AI not configured — set GOOGLE_CLOUD_PROJECT_ID and GOOGLE_DOCUMENT_AI_PROCESSOR_ID');
  }

  const { DocumentProcessorServiceClient } = await import('@google-cloud/documentai');

  // Build client options — prefer inline JSON, then explicit file path, then ADC
  const clientOptions: { credentials?: object; keyFilename?: string } = {};
  if (process.env.GOOGLE_SERVICE_ACCOUNT_JSON) {
    clientOptions.credentials = JSON.parse(process.env.GOOGLE_SERVICE_ACCOUNT_JSON) as object;
  } else if (process.env.GOOGLE_APPLICATION_CREDENTIALS) {
    clientOptions.keyFilename = process.env.GOOGLE_APPLICATION_CREDENTIALS;
  }

  const client = new DocumentProcessorServiceClient(clientOptions);
  const processorName = `projects/${PROJECT_ID}/locations/${LOCATION}/processors/${PROCESSOR_ID}`;

  const [result] = await client.processDocument({
    name: processorName,
    rawDocument: {
      content: Buffer.from(pdfBytes).toString('base64'),
      mimeType: 'application/pdf',
    },
  });

  const doc = result.document;
  const pages = doc?.pages ?? [];
  const fullText = doc?.text ?? '';
  const fields: DetectedField[] = [];
  const seenIds = new Set<string>();

  // ── Step 1: Form Parser key-value pairs (accurate bboxes) ──
  for (const page of pages) {
    const pageNum = Number(page.pageNumber ?? 1);

    for (const formField of page.formFields ?? []) {
      const vertices =
        formField.fieldValue?.boundingPoly?.normalizedVertices ?? [];
      if (vertices.length < 2) continue;

      const xs = vertices.map((v) => v.x ?? 0);
      const ys = vertices.map((v) => v.y ?? 0);
      const x = Math.min(...xs);
      const y = Math.min(...ys);
      const w = Math.max(...xs) - x;
      const h = Math.max(...ys) - y;

      const rawLabel =
        (formField.fieldName?.textAnchor as { content?: string } | null | undefined)?.content
          ?.trim()
          .replace(/:$/, '') ?? '';
      const rawValue =
        (formField.fieldValue?.textAnchor as { content?: string } | null | undefined)?.content
          ?.trim() ?? '';

      if (!rawLabel && !rawValue) continue;

      const label = rawLabel || `Field ${fields.length + 1}`;
      let id = label.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 55);
      if (!id) id = `field_${fields.length}`;
      const base = id;
      let suffix = 2;
      while (seenIds.has(id)) id = `${base}_${suffix++}`;
      seenIds.add(id);

      fields.push({
        id,
        label,
        type: inferFieldType(label, rawValue),
        page: pageNum,
        bbox: { x, y, w: Math.max(w, 0.05), h: Math.max(h, 0.02) },
        required: false,
        value: rawValue,
        profileKey: inferProfileKey(label),
        confidence: Number(
          (formField.fieldValue as { confidence?: number } | null | undefined)?.confidence ?? 0.85,
        ),
      } satisfies DetectedField);
    }
  }

  // ── Step 2: Text line label extraction (catches missed fields) ──
  const extra = extractFieldsFromLines(pages, fullText, fields, seenIds);
  fields.push(...extra);

  // Sort by page then vertical position
  fields.sort((a, b) => a.page !== b.page ? a.page - b.page : a.bbox.y - b.bbox.y);

  return fields;
}
