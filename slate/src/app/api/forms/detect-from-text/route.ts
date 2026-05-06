export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import type { DetectedField } from '@/types/smartFill';

export async function POST(request: NextRequest) {
  let body: { description?: string };
  try { body = await request.json(); }
  catch { return NextResponse.json({ error: 'Invalid JSON' }, { status: 400 }); }

  const { description } = body;
  if (!description?.trim()) return NextResponse.json({ error: 'description is required' }, { status: 400 });

  const client = new Anthropic(
    process.env.ANTHROPIC_API_KEY ? { apiKey: process.env.ANTHROPIC_API_KEY } : {}
  );

  const prompt = `Convert this list of form field names into a structured JSON array.
Input: "${description}"

Return ONLY a JSON array. Each element:
{
  "id": "snake_case_id",
  "label": "Human Readable Label",
  "type": "text|checkbox|date|currency|signature|textarea",
  "required": false,
  "profileKey": "full_name|email|phone|address_line_1|company_name|abn|date_of_birth|licence_number or null",
  "confidence": 0.7
}

Rules:
- Infer type from label: "date" for dates, "signature" for signatures, "checkbox" for yes/no fields, "currency" for amounts
- profileKey: map obvious personal info fields to profile keys, null otherwise
- Start response with [ immediately`;

  try {
    const response = await client.messages.create({
      model: 'claude-sonnet-4-6',
      max_tokens: 2048,
      messages: [{ role: 'user', content: prompt }],
    });

    const text = response.content.find(b => b.type === 'text')?.text ?? '';
    const arrayMatch = text.match(/\[[\s\S]*\]/);
    if (!arrayMatch) return NextResponse.json({ fields: [] });

    const raw: unknown[] = JSON.parse(arrayMatch[0]);
    const fields: DetectedField[] = raw.map((item, index) => {
      const f = item as Record<string, unknown>;
      return {
        id: String(f.id ?? `field_${index}`),
        label: String(f.label ?? `Field ${index + 1}`),
        type: (f.type as DetectedField['type']) ?? 'text',
        page: 1,
        bbox: { x: 0.05, y: index * 0.08, w: 0.90, h: 0.05 },
        required: Boolean(f.required ?? false),
        value: '',
        profileKey: f.profileKey != null ? String(f.profileKey) : undefined,
        confidence: Number(f.confidence ?? 0.7),
      } satisfies DetectedField;
    });

    return NextResponse.json({ fields });
  } catch (err) {
    console.error('[detect-from-text] Failed:', err);
    return NextResponse.json({ fields: [], error: 'Detection failed' });
  }
}
