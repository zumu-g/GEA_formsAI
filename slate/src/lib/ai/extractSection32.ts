/**
 * Section 32 extraction via Claude.
 *
 * Reads either extracted document text (from docling / a searchable PDF) or the raw PDF
 * bytes (Claude reads PDFs — including scans — natively), and returns a typed
 * `Section32Extraction`. Reuses the shared Anthropic client (`./client`).
 *
 * Guarantees enforced by the prompt + post-processing:
 *  - Never fabricate values. Absent → `null`.
 *  - Unsure → `confidence: 'low'`; those fields are collected into `meta.uncertainFields`
 *    and rendered "[uncertain]" in the summary.
 */

import type { ContentBlockParam } from '@anthropic-ai/sdk/resources/messages/messages';
import { getAnthropicClient } from './client';
import type {
  ExtractedField,
  ExtractionMethod,
  ExtractionSource,
  Section32Data,
  Section32Extraction,
} from '@/types/section32Extraction';

const MODEL = 'claude-sonnet-4-6';

const EXTRACTION_PROMPT = `You are a conveyancing analyst extracting structured data from a Victorian (Australia) Section 32 Vendor's Statement (Sale of Land Act 1962). Read the document and return a SINGLE JSON object — no markdown, no preamble. Start with { and end with }.

The object MUST have exactly two top-level keys: "data" and "summary".

"data" is an object with these groups and fields. EVERY field is an object: { "value": <value-or-null>, "confidence": "high"|"low", "source": "text" }.

data.vendor: vendor_name, vendor_address, vendor_phone, vendor_email, vendor_solicitor_name, vendor_solicitor_firm, vendor_solicitor_address, vendor_solicitor_phone, vendor_solicitor_email
data.property: property_address, title_volume, title_folio, lot_number, plan_number, registered_proprietors, title_type, restrictions_caveats, easements, council_name
data.outgoings: council_rates, water_authority, water_rates, land_tax, owners_corp_fees, other_outgoings, mortgage_holder, mortgage_amount, mortgage_type
data.owners_corporation: applies (boolean true/false), details (string)
data.planning: zoning_code, planning_overlay, building_permits_7yrs (boolean), permit_details, owner_builder (boolean)
data.services: water, drainage, sewerage, electricity, gas, telephone — each a boolean (true = connected, false = explicitly not connected, null = not stated)
data.special: chattels_included, sunset_clause, special_conditions

CRITICAL RULES:
- NEVER fabricate or guess legal or financial values. If the document does not clearly state a field, set "value": null and "confidence": "high" (you are confident it is absent).
- If you find a value but are not fully confident it is correct or complete (ambiguous text, poor scan, conflicting figures), set "confidence": "low".
- Currency fields (council_rates, water_rates, land_tax, owners_corp_fees, other_outgoings, mortgage_amount): return the number only as a string without the "$" or commas (e.g. "1850.00"). If a range or unclear, use confidence "low".
- Boolean fields: true / false / null only.
- registered_proprietors: list ALL proprietors exactly as on the Certificate of Title.

"summary" is a plain-English paragraph (or short bulleted lines using "- ") summarising the property, title, key outgoings, planning, owners corporation, and any notable conditions. For ANY value you marked "confidence": "low", append " [uncertain]" immediately after that value in the summary. Do not invent facts in the summary.`;

/** Build the content blocks: a text block of extracted text, or the raw PDF document block. */
export function buildExtractionContent(opts: {
  documentText?: string;
  pdfBytes?: Uint8Array;
}): ContentBlockParam[] {
  const blocks: ContentBlockParam[] = [];

  if (opts.pdfBytes && opts.pdfBytes.length > 0) {
    blocks.push({
      type: 'document',
      source: {
        type: 'base64',
        media_type: 'application/pdf',
        data: Buffer.from(opts.pdfBytes).toString('base64'),
      },
    });
  } else if (opts.documentText) {
    blocks.push({
      type: 'text',
      text: `DOCUMENT TEXT:\n\n${opts.documentText}`,
    });
  }

  blocks.push({ type: 'text', text: EXTRACTION_PROMPT });
  return blocks;
}

/** Parse Claude's response into { data, summary }. Throws if no JSON object is found. */
function parseResponse(text: string): { data: Section32Data; summary: string } {
  let cleaned = text
    .replace(/^﻿/, '')
    .replace(/^```(?:json)?\s*/im, '')
    .replace(/```\s*$/m, '')
    .trim();

  const objMatch = cleaned.match(/\{[\s\S]*\}/);
  if (!objMatch) throw new Error('No JSON object found in extraction response.');
  cleaned = objMatch[0];

  const parsed = JSON.parse(cleaned) as { data?: Section32Data; summary?: string };
  if (!parsed.data) throw new Error('Extraction response missing "data".');
  return { data: parsed.data, summary: parsed.summary ?? '' };
}

/** Walk the data tree and collect dotted paths of every low-confidence, non-null field. */
function collectUncertainFields(data: Section32Data): string[] {
  const out: string[] = [];
  const isField = (v: unknown): v is ExtractedField<unknown> =>
    typeof v === 'object' && v !== null && 'value' in v && 'confidence' in v;

  for (const [group, groupVal] of Object.entries(data)) {
    if (!groupVal || typeof groupVal !== 'object') continue;
    for (const [key, fieldVal] of Object.entries(groupVal)) {
      if (isField(fieldVal) && fieldVal.value !== null && fieldVal.confidence === 'low') {
        out.push(`${group}.${key}`);
      }
    }
  }
  return out;
}

/** Stamp every field's `source` so downstream knows the extraction path. */
function stampSource(data: Section32Data, source: ExtractionSource): void {
  for (const groupVal of Object.values(data)) {
    if (!groupVal || typeof groupVal !== 'object') continue;
    for (const fieldVal of Object.values(groupVal)) {
      if (fieldVal && typeof fieldVal === 'object' && 'value' in fieldVal) {
        (fieldVal as ExtractedField).source = source;
      }
    }
  }
}

export interface ExtractSection32Options {
  /** Extracted document text (preferred when a clean text layer exists). */
  documentText?: string;
  /** Raw PDF bytes (used for scanned docs — Claude reads them natively as a fallback). */
  pdfBytes?: Uint8Array;
  /** How the input was obtained — recorded in meta. */
  method: ExtractionMethod;
  /** Whether the source PDF was scanned/image-based. */
  scanned: boolean;
  /** Whether ocrmypdf produced the text layer. */
  ocrUsed: boolean;
  pageCount?: number;
}

export async function extractSection32(opts: ExtractSection32Options): Promise<Section32Extraction> {
  const client = getAnthropicClient();

  const response = await client.messages.create({
    model: MODEL,
    max_tokens: 8192,
    messages: [
      {
        role: 'user',
        content: buildExtractionContent({
          documentText: opts.documentText,
          pdfBytes: opts.pdfBytes,
        }),
      },
    ],
  });

  const textBlock = response.content.find((b) => b.type === 'text');
  if (!textBlock || textBlock.type !== 'text') {
    throw new Error('Empty extraction response from Claude.');
  }

  const { data, summary } = parseResponse(textBlock.text);

  const source: ExtractionSource = opts.method === 'vision' ? 'vision' : opts.ocrUsed ? 'ocr' : 'text';
  stampSource(data, source);

  return {
    data,
    summary,
    meta: {
      scanned: opts.scanned,
      ocrUsed: opts.ocrUsed,
      method: opts.method,
      uncertainFields: collectUncertainFields(data),
      pageCount: opts.pageCount,
    },
  };
}
