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
  if (/\bacn\b/.test(l)) return 'abn';
  if (/date.of.birth|dob/.test(l)) return 'date_of_birth';
  if (/licence|license/.test(l)) return 'licence_number';
  if (/\bagent\b/.test(l)) return 'full_name';
  if (/\bvendor\b/.test(l)) return 'full_name';
  if (/city|suburb/.test(l)) return 'city';
  if (/\bstate\b/.test(l)) return 'state';
  if (/postcode|post.?code|zip/.test(l)) return 'zip_code';
  return undefined;
}

// Labels that are never fill targets
const SKIP_LABELS = new Set([
  'note', 'notes', 'see', 'refer', 'if', 'the', 'this', 'for',
  'and', 'or', 'to', 'of', 'in', 'on', 'at', 'by', 'with', 'upon', 'where',
  'pursuant', 'subject', 'whereby', 'herein', 'thereof', 'notwithstanding',
]);

// Keywords that relax the colon requirement for short lines
const FIELD_KEYWORDS_RELAXED = [
  'commission', 'rate', 'period', 'from', 'gst', 'postcode', 'suburb',
  'state', 'price', 'deposit',
];

// Known field keywords — used to strip garbled prefixes and identify valid labels
const FIELD_KEYWORDS_CLEAN = [
  'Email', 'Mobile', 'Phone', 'Fax', 'Address', 'Name', 'Date', 'Signature',
  'Agent', 'Vendor', 'ABN', 'ACN', 'Attention', 'Property', 'Licence', 'License',
  'GST', 'Commission', 'Price', 'Period', 'Suburb', 'State', 'Postcode',
];

// Verbs and conjunctions that indicate form text rather than field labels
const SENTENCE_PATTERN = /\b(is|are|was|were|been|sold|effective|upon|includes|requires|means|states|provides|acknowledges|warrants)\b/i;

// Returns true if a short string looks like a real form field label
function isCleanFieldLabel(label: string): boolean {
  if (!label || label.length < 2 || label.length > 30) return false;
  const words = label.toLowerCase().split(/\s+/).filter(Boolean);
  if (words.length > 4) return false;
  if (SKIP_LABELS.has(words[0])) return false;
  if (/^\d/.test(label)) return false;   // starts with digit
  if (/\d$/.test(label)) return false;   // ends with digit (clause numbers)
  const asciiRatio = (label.match(/[\x20-\x7E]/g) ?? []).length / label.length;
  if (asciiRatio < 0.85) return false;
  // Garbled words: long words with very few vowels
  const hasGarbled = words.some(w => {
    if (w.length < 5) return false;
    return (w.match(/[aeiou]/g) ?? []).length / w.length < 0.15;
  });
  if (hasGarbled) return false;
  // All-caps sequences > 3 chars that aren't known abbreviations
  const hasAllCapsGarble = words.some(w =>
    w.length > 3 && w === w.toUpperCase() && /[A-Z]{4,}/.test(w)
  );
  if (hasAllCapsGarble) return false;
  return true;
}

// Extract ALL potential field labels from a text line by splitting on ':'
// Returns labels found as "...lastword(s):" patterns throughout the line
function extractCandidatesFromLine(text: string): string[] {
  if (!text.includes(':')) return [];
  const parts = text.split(':');
  const candidates: string[] = [];

  for (let i = 0; i < parts.length - 1; i++) {
    const segment = parts[i];
    const words = segment.trim().split(/\s+/).filter(Boolean);
    if (words.length === 0) continue;

    // Try last 1–4 words as label; use shortest that passes quality checks
    for (let n = 1; n <= Math.min(4, words.length); n++) {
      const cand = words.slice(-n).join(' ').trim();
      if (isCleanFieldLabel(cand)) {
        candidates.push(cand);
        break;
      }
    }
  }

  return candidates;
}

// Extract additional fields from text lines (catches labels Form Parser misses)
function extractFieldsFromLines(
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  pages: any[],
  fullText: string,
  existingFields: DetectedField[],
  seenIds: Set<string>,
): DetectedField[] {
  const extra: DetectedField[] = [];

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

      // Get bounding box first — needed for bbox-based dedup and field position
      const poly = layout?.boundingPoly as Record<string, unknown> | undefined;
      const verts = (poly?.normalizedVertices ?? []) as Array<Record<string, number>>;
      if (verts.length < 2) continue;

      const xs = verts.map(v => v.x ?? 0);
      const ys = verts.map(v => v.y ?? 0);
      const lineY = Math.min(...ys);
      const lineX = Math.min(...xs);

      // Extract all label candidates from this line
      const rawCandidates = extractCandidatesFromLine(text);
      if (rawCandidates.length === 0) {
        // No colon-delimited candidates — check if it's a bare keyword
        if (text.length <= 35) {
          const textLower = text.toLowerCase();
          const isKeyword = FIELD_KEYWORDS_RELAXED.some(kw =>
            new RegExp(`\\b${kw}\\b`).test(textLower)
          );
          if (isKeyword && isCleanFieldLabel(text)) {
            rawCandidates.push(text);
          }
        }
        if (rawCandidates.length === 0) continue;
      }

      // For single-candidate lines, apply an extra gate: the candidate must
      // start the line (i.e. "Label: ..." not "...text label:") or be a known keyword
      const validCandidates: string[] = [];
      for (const cand of rawCandidates) {
        if (rawCandidates.length === 1) {
          const candLower = cand.toLowerCase();
          const startsLine = text.trim().toLowerCase().startsWith(candLower);
          const isKnownKeyword = FIELD_KEYWORDS_RELAXED.some(kw =>
            new RegExp(`\\b${kw}\\b`).test(candLower)
          );
          const isKnownClean = FIELD_KEYWORDS_CLEAN.some(kw =>
            kw.toLowerCase() === candLower
          );
          if (!startsLine && !isKnownKeyword && !isKnownClean) continue;
        }
        // Multi-candidate lines: trust extractCandidatesFromLine quality gate
        validCandidates.push(cand);
      }

      if (validCandidates.length === 0) continue;

      // Distribute value-area bbox across line width
      const valueStartX = Math.min(lineX + 0.15, 0.85);
      const totalValueW = Math.max(0.95 - lineX - 0.15, 0.1);
      const segW = totalValueW / validCandidates.length;

      for (let ci = 0; ci < validCandidates.length; ci++) {
        let rawLabel = validCandidates[ci];

        // Strip garbled prefix — if label ends with a known keyword word, use just that
        const lastWord = rawLabel.split(/\s+/).pop() ?? '';
        if (
          FIELD_KEYWORDS_CLEAN.some(kw => kw.toLowerCase() === lastWord.toLowerCase()) &&
          rawLabel.split(/\s+/).length > 1
        ) {
          rawLabel = lastWord;
        }

        // Deduplicate: skip if a field with same normalised label exists nearby (< 5% y)
        const normalised = rawLabel.toLowerCase().replace(/[^a-z0-9]/g, '');
        const isDuplicate = [...existingFields, ...extra].some(f =>
          f.page === pageNum &&
          f.label.toLowerCase().replace(/[^a-z0-9]/g, '') === normalised &&
          Math.abs(f.bbox.y - lineY) < 0.05
        );
        if (isDuplicate) continue;

        // Build unique id
        let id = rawLabel.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '').slice(0, 55);
        if (!id) continue;
        const base = id;
        let s = 2;
        while (seenIds.has(id)) id = `${base}_${s++}`;
        seenIds.add(id);

        extra.push({
          id,
          label: rawLabel,
          type: inferFieldType(rawLabel, ''),
          page: pageNum,
          bbox: {
            x: Math.min(valueStartX + ci * segW, 0.9),
            y: lineY,
            w: Math.max(segW, 0.1),
            h: 0.025,
          },
          required: false,
          value: '',
          profileKey: inferProfileKey(rawLabel),
          confidence: 0.6,
        } satisfies DetectedField);
      }
    }
  }

  return extra;
}

export async function detectWithGoogleDocumentAI(
  pdfBytes: Uint8Array,
): Promise<DetectedField[]> {
  if (!PROJECT_ID || !PROCESSOR_ID) {
    throw new Error('Google Document AI not configured — set GOOGLE_CLOUD_PROJECT_ID and GOOGLE_DOCUMENT_AI_PROCESSOR_ID');
  }

  const { DocumentProcessorServiceClient } = await import('@google-cloud/documentai');

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
      const vertices = formField.fieldValue?.boundingPoly?.normalizedVertices ?? [];
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

      // Quality filter: reject labels that look like form text, not field labels
      if (rawLabel) {
        const labelLower = rawLabel.toLowerCase();
        const labelWords = labelLower.trim().split(/\s+/).filter(Boolean);
        if (labelWords.length > 4) continue;                         // too wordy
        if (SKIP_LABELS.has(labelWords[0])) continue;               // non-field first word
        if (/\d$/.test(rawLabel.trim())) continue;                   // ends with digit (clause numbers)
        if (SENTENCE_PATTERN.test(labelLower)) continue;             // contains a verb
        // Contains sentence-level conjunction (but not slash combos like "Fax/Email")
        if (/ and | or /.test(rawLabel) && !/\//.test(rawLabel)) continue;
      }

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
