import { UnstructuredClient } from 'unstructured-client';

export interface UnstructuredElement {
  type: string;
  text: string;
  metadata: Record<string, unknown>;
}

export async function parseDocument(
  fileBytes: Uint8Array,
  filename: string
): Promise<UnstructuredElement[]> {
  const apiKey = process.env.UNSTRUCTURED_API_KEY;
  if (!apiKey) {
    throw new Error('UNSTRUCTURED_API_KEY not configured');
  }

  const serverURL = process.env.UNSTRUCTURED_API_URL ?? 'https://api.unstructuredapp.io';

  const client = new UnstructuredClient({
    serverURL,
    security: { apiKeyAuth: apiKey },
  });

  const response = await client.general.partition({
    partitionParameters: {
      files: {
        content: fileBytes,
        fileName: filename,
      },
    },
  });

  if (typeof response === 'string') {
    return [];
  }

  return response.map((el: Record<string, unknown>) => ({
    type: typeof el['type'] === 'string' ? el['type'] : 'Unknown',
    text: typeof el['text'] === 'string' ? el['text'] : '',
    metadata:
      el['metadata'] !== null &&
      typeof el['metadata'] === 'object' &&
      !Array.isArray(el['metadata'])
        ? (el['metadata'] as Record<string, unknown>)
        : {},
  }));
}

export function extractTextForLLM(elements: UnstructuredElement[]): string {
  return elements
    .filter((el) => el.text.trim().length > 0)
    .map((el) => `[${el.type}] ${el.text}`)
    .join('\n\n');
}
