export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';

const PROMPT = `This is a cropped region from a paper form or PDF document.
Look at the image and identify the field label — the text that describes what should be filled in.

Reply with JSON only:
{"label": "field name here", "type": "text|textarea|date|currency|checkbox|signature"}

Rules:
- label: concise descriptive name (e.g. "Full Name", "Date of Birth", "Signature", "Agent")
- type: text (default), textarea (multi-line notes/address), date, currency (dollar amounts), checkbox (yes/no tick), signature
- If no clear label is visible, use "Field"
- JSON only — no other text`;

export async function POST(request: NextRequest) {
  let body: { imageBase64?: string };
  try { body = await request.json(); }
  catch { return NextResponse.json({ label: 'Field', type: 'text' }); }

  const { imageBase64 } = body;
  if (!imageBase64) return NextResponse.json({ label: 'Field', type: 'text' });

  const client = new Anthropic(
    process.env.ANTHROPIC_API_KEY ? { apiKey: process.env.ANTHROPIC_API_KEY } : {}
  );

  try {
    const response = await client.messages.create({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 128,
      messages: [{
        role: 'user',
        content: [
          {
            type: 'image',
            source: { type: 'base64', media_type: 'image/png', data: imageBase64 },
          },
          { type: 'text', text: PROMPT },
        ],
      }],
    });

    const text = response.content[0].type === 'text' ? response.content[0].text.trim() : '';
    const match = text.match(/\{[\s\S]*\}/);
    if (!match) return NextResponse.json({ label: 'Field', type: 'text' });

    const parsed = JSON.parse(match[0]) as { label?: string; type?: string };
    return NextResponse.json({
      label: typeof parsed.label === 'string' && parsed.label.trim() ? parsed.label.trim() : 'Field',
      type: parsed.type ?? 'text',
    });
  } catch {
    return NextResponse.json({ label: 'Field', type: 'text' });
  }
}
