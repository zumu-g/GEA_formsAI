export const runtime = 'nodejs';

import { NextRequest, NextResponse } from 'next/server';
import Anthropic from '@anthropic-ai/sdk';
import type { DetectedField } from '@/types/smartFill';

const client = new Anthropic(
  process.env.ANTHROPIC_API_KEY ? { apiKey: process.env.ANTHROPIC_API_KEY } : {}
);

export async function POST(request: NextRequest) {
  try {
    const body = await request.json() as {
      fields: DetectedField[];
      profileData: Record<string, string>;
    };

    const { fields, profileData } = body;

    if (!Array.isArray(fields) || fields.length === 0) {
      return NextResponse.json({ values: {} });
    }

    const compactFields = fields.map(({ id, label, type }) => ({ id, label, type }));

    const prompt = `You are filling out a form on behalf of a user.
Given the form fields and the user's profile data, return a JSON object mapping each field id to the best value from the profile.
Only include fields you can confidently fill. Use empty string to skip.
Return JSON only — no other text.

Fields: ${JSON.stringify(compactFields)}
Profile: ${JSON.stringify(profileData)}`;

    const message = await client.messages.create({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 512,
      messages: [{ role: 'user', content: prompt }],
    });

    const rawText =
      message.content[0]?.type === 'text' ? message.content[0].text.trim() : '';

    // Strip markdown code fences if present
    const jsonText = rawText.replace(/^```(?:json)?\s*/i, '').replace(/\s*```\s*$/, '').trim();

    let parsed: unknown;
    try {
      parsed = JSON.parse(jsonText);
    } catch {
      return NextResponse.json({ values: {} });
    }

    if (typeof parsed !== 'object' || parsed === null || Array.isArray(parsed)) {
      return NextResponse.json({ values: {} });
    }

    // Keep only string values
    const values: Record<string, string> = {};
    for (const [key, val] of Object.entries(parsed as Record<string, unknown>)) {
      if (typeof val === 'string') {
        values[key] = val;
      }
    }

    return NextResponse.json({ values });
  } catch {
    return NextResponse.json({ values: {} });
  }
}
