import { getAnthropicClient } from './client';
import { AUTO_FILL_SYSTEM_PROMPT } from './prompts';
import type { FormField } from '@/types/form';
import type { DataProfile } from '@/types/profile';

interface AutoFillMapping {
  fieldId: string;
  profileKey: string;
  value: string | null;
}

export async function autoFillFields(
  fields: FormField[],
  profile: DataProfile
): Promise<AutoFillMapping[]> {
  const client = getAnthropicClient();

  const fieldsSummary = fields.map((f) => ({
    id: f.id,
    name: f.fieldName,
    type: f.fieldType,
  }));

  const response = await client.messages.create({
    model: 'claude-sonnet-4-5-20250929',
    max_tokens: 2048,
    system: AUTO_FILL_SYSTEM_PROMPT,
    messages: [
      {
        role: 'user',
        content: `Map the following form fields to the user's data profile.

Form fields:
${JSON.stringify(fieldsSummary, null, 2)}

User profile data:
${JSON.stringify(profile.data, null, 2)}

Return a JSON array of { fieldId, profileKey, value } objects.`,
      },
    ],
  });

  const textContent = response.content.find((c) => c.type === 'text');
  if (textContent && textContent.type === 'text') {
    try {
      return JSON.parse(textContent.text) as AutoFillMapping[];
    } catch {
      console.error('Failed to parse auto-fill response');
      return [];
    }
  }

  return [];
}
