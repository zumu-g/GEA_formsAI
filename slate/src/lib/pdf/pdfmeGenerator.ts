import { generate } from '@pdfme/generator';
import { text } from '@pdfme/schemas';
import type { Template, Font } from '@pdfme/common';
import type { PdfmeFieldMapping } from '@/types/skill';

function applyTransform(value: string, transform?: string): string {
  if (!value) return value;
  switch (transform) {
    case 'uppercase':
      return value.toUpperCase();
    case 'lowercase':
      return value.toLowerCase();
    case 'currency_au': {
      const num = parseFloat(value.replace(/[^0-9.]/g, ''));
      if (isNaN(num)) return value;
      return `$${num.toLocaleString('en-AU', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }
    case 'date_au':
      return value;
    default:
      return value;
  }
}

/**
 * Build a pdfme Template from original PDF bytes + coordinate-based field mappings.
 * The original PDF becomes the background; fields are overlaid at exact mm positions.
 */
export function buildTemplate(
  pdfBytes: Uint8Array,
  mappings: PdfmeFieldMapping[],
  pageCount: number
): Template {
  // Group mappings by page (0-indexed)
  const byPage = new Map<number, PdfmeFieldMapping[]>();
  for (const m of mappings) {
    const list = byPage.get(m.page) ?? [];
    list.push(m);
    byPage.set(m.page, list);
  }

  // Build schemas array — one entry per page
  const schemas: Template['schemas'] = [];
  for (let i = 0; i < pageCount; i++) {
    const pageMappings = byPage.get(i) ?? [];
    schemas.push(
      pageMappings.map((m) => ({
        name: m.schemaName,
        type: 'text' as const,
        position: m.position,
        width: m.width,
        height: m.height,
        fontSize: m.fontSize ?? 10,
        alignment: m.alignment ?? 'left',
        fontColor: '#1a1a1e',
      }))
    );
  }

  return {
    basePdf: pdfBytes.buffer.slice(pdfBytes.byteOffset, pdfBytes.byteOffset + pdfBytes.byteLength) as ArrayBuffer,
    schemas,
  };
}

/**
 * Build pdfme inputs from skill values + field mappings.
 * Applies transforms (currency, date, case).
 */
export function buildInputs(
  mappings: PdfmeFieldMapping[],
  values: Record<string, string>
): Record<string, string>[] {
  const inputs: Record<string, string> = {};

  for (const m of mappings) {
    const raw = values[m.skillFieldId];
    if (raw !== undefined && raw !== '' && raw !== 'false') {
      inputs[m.schemaName] = applyTransform(raw, m.transform);
    }
  }

  return [inputs];
}

/**
 * Generate a filled PDF using pdfme coordinate-based overlays.
 * Takes original PDF, field mappings with mm coordinates, and user values.
 * Returns filled PDF as Uint8Array.
 */
export async function generateFilledPdf(
  pdfBytes: Uint8Array,
  mappings: PdfmeFieldMapping[],
  values: Record<string, string>,
  pageCount: number
): Promise<Uint8Array> {
  const template = buildTemplate(pdfBytes, mappings, pageCount);
  const inputs = buildInputs(mappings, values);

  const pdf = await generate({
    template,
    inputs,
    plugins: { text },
  });

  return new Uint8Array(pdf);
}
