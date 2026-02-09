import { getAnthropicClient } from './client';
import { FIELD_DETECTION_SYSTEM_PROMPT } from './prompts';
import type { FormField } from '@/types/form';

interface DetectedField {
  name: string;
  type: FormField['fieldType'];
  page: number;
  bounds: { x: number; y: number; width: number; height: number };
  required: boolean;
  hint?: string;
}

export async function detectFormFields(
  pageImages: { page: number; base64: string; mediaType: string }[]
): Promise<DetectedField[]> {
  const client = getAnthropicClient();
  const allFields: DetectedField[] = [];

  for (const pageImage of pageImages) {
    const response = await client.messages.create({
      model: 'claude-sonnet-4-5-20250929',
      max_tokens: 4096,
      system: FIELD_DETECTION_SYSTEM_PROMPT,
      messages: [
        {
          role: 'user',
          content: [
            {
              type: 'image',
              source: {
                type: 'base64',
                media_type: pageImage.mediaType as 'image/png' | 'image/jpeg' | 'image/gif' | 'image/webp',
                data: pageImage.base64,
              },
            },
            {
              type: 'text',
              text: `Analyze page ${pageImage.page} of this PDF form. Identify all fillable fields and return them as a JSON array.`,
            },
          ],
        },
      ],
    });

    const textContent = response.content.find((c) => c.type === 'text');
    if (textContent && textContent.type === 'text') {
      try {
        const fields = JSON.parse(textContent.text) as DetectedField[];
        allFields.push(...fields.map((f) => ({ ...f, page: pageImage.page })));
      } catch {
        console.error(`Failed to parse AI response for page ${pageImage.page}`);
      }
    }
  }

  return allFields;
}
