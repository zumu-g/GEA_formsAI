import { zerox } from 'zerox';
import Anthropic from '@anthropic-ai/sdk';
import * as fs from 'fs/promises';
import * as path from 'path';
import * as os from 'os';

export interface ZeroxPageResult {
  page: number;
  markdown: string;
}

export interface ZeroxDocumentResult {
  pages: ZeroxPageResult[];
  fullMarkdown: string;
  inputTokens: number;
  outputTokens: number;
}

/**
 * OCR a PDF into structured markdown using Zerox + Claude vision.
 * Uses customModelFunction to route through Anthropic API (no OpenAI/Bedrock needed).
 * Requires graphicsmagick for PDF-to-image conversion.
 */
export async function ocrWithZerox(
  pdfBytes: Uint8Array,
  filename: string = 'document.pdf'
): Promise<ZeroxDocumentResult> {
  // Zerox requires a file path — write to temp
  const tempDir = await fs.mkdtemp(path.join(os.tmpdir(), 'zerox-'));
  const tempPath = path.join(tempDir, filename);
  await fs.writeFile(tempPath, pdfBytes);

  const client = new Anthropic({
    apiKey: process.env.ANTHROPIC_API_KEY,
  });

  try {
    const result = await zerox({
      filePath: tempPath,
      customModelFunction: async ({ image, priorPage, maintainFormat }) => {
        const systemPrompt = maintainFormat && priorPage
          ? `Convert this PDF page to well-structured markdown. Preserve all text, labels, field names, checkboxes, tables, and layout. For form fields, note the field label and any current values or empty fields. Maintain consistent formatting with the previous page:\n\n${priorPage}`
          : 'Convert this PDF page to well-structured markdown. Preserve all text, labels, field names, checkboxes, tables, and layout structure. For form fields, note the field label and any current values or empty fields.';

        const response = await client.messages.create({
          model: 'claude-sonnet-4-5-20250929',
          max_tokens: 4096,
          messages: [
            {
              role: 'user',
              content: [
                {
                  type: 'image',
                  source: {
                    type: 'base64',
                    media_type: 'image/png',
                    data: image,
                  },
                },
                {
                  type: 'text',
                  text: systemPrompt,
                },
              ],
            },
          ],
        });

        const textBlock = response.content.find((c) => c.type === 'text');
        return {
          content: textBlock?.type === 'text' ? textBlock.text : '',
          inputTokens: response.usage.input_tokens,
          outputTokens: response.usage.output_tokens,
        };
      },
      cleanup: true,
      concurrency: 3,
      maintainFormat: false,
    });

    const pages: ZeroxPageResult[] = result.pages.map((p, idx) => ({
      page: idx + 1,
      markdown: p.content ?? '',
    }));

    return {
      pages,
      fullMarkdown: pages
        .map((p) => `## Page ${p.page}\n\n${p.markdown}`)
        .join('\n\n---\n\n'),
      inputTokens: result.inputTokens,
      outputTokens: result.outputTokens,
    };
  } finally {
    await fs.rm(tempDir, { recursive: true, force: true }).catch(() => {});
  }
}
