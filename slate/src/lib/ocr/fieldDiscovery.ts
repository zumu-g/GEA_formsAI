import Anthropic from '@anthropic-ai/sdk';
import type { ZeroxDocumentResult } from './zeroxService';

export interface DiscoveredField {
  fieldName: string;
  fieldType: 'text' | 'checkbox' | 'date' | 'currency' | 'signature' | 'textarea';
  page: number;
  approximatePosition: 'top' | 'middle' | 'bottom';
  context: string;
  currentValue?: string;
  suggestedSkillFieldId?: string;
}

/**
 * Given Zerox OCR markdown output, use Claude to identify all fillable fields
 * and their approximate positions within the document.
 */
export async function discoverFields(
  ocrResult: ZeroxDocumentResult,
  skillFieldIds?: string[]
): Promise<DiscoveredField[]> {
  const client = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
  });

  const matchPrompt = skillFieldIds?.length
    ? `\n\nAlso match each discovered field to the most appropriate ID from this list: ${skillFieldIds.join(', ')}. Put the match in "suggestedSkillFieldId".`
    : '';

  const response = await client.messages.create({
    model: 'claude-sonnet-4-5-20250929',
    max_tokens: 8192,
    system: `You are a form field discovery AI. Given markdown extracted from a PDF form via OCR, identify every FILLABLE field (empty or partially filled). Return a JSON array of objects.

Each object must have:
- "fieldName": the label text next to the field (e.g. "Purchaser Name(s)")
- "fieldType": one of "text", "checkbox", "date", "currency", "signature", "textarea"
- "page": the page number (from the "## Page N" headings)
- "approximatePosition": "top", "middle", or "bottom" of the page
- "context": surrounding text for disambiguation (1 sentence)
- "currentValue": any value already filled in, or null if empty${matchPrompt}

Return ONLY the JSON array, no other text.`,
    messages: [
      {
        role: 'user',
        content: ocrResult.fullMarkdown,
      },
    ],
  });

  const textBlock = response.content.find((c) => c.type === 'text');
  if (!textBlock || textBlock.type !== 'text') return [];

  try {
    // Extract JSON from the response (may be wrapped in ```json blocks)
    const jsonStr = textBlock.text
      .replace(/```json\n?/g, '')
      .replace(/```\n?/g, '')
      .trim();
    return JSON.parse(jsonStr);
  } catch {
    console.error('Failed to parse field discovery response');
    return [];
  }
}
