import { Stagehand } from '@browserbasehq/stagehand';

export interface StagehandFillResult {
  success: boolean;
  steps: string[];
  error?: string;
}

export async function fillWebFormWithStagehand(
  url: string,
  instructions: string,
  data: Record<string, unknown>
): Promise<StagehandFillResult> {
  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    return { success: false, steps: [], error: 'ANTHROPIC_API_KEY not configured' };
  }

  const browserbaseApiKey = process.env.STAGEHAND_BROWSERBASE_API_KEY;
  const browserbaseProjectId = process.env.STAGEHAND_BROWSERBASE_PROJECT_ID;
  const useBrowserbase = !!(browserbaseApiKey && browserbaseProjectId);

  const stagehand = new Stagehand({
    env: useBrowserbase ? 'BROWSERBASE' : 'LOCAL',
    ...(useBrowserbase && {
      apiKey: browserbaseApiKey,
      projectId: browserbaseProjectId,
    }),
    model: {
      modelName: 'claude-sonnet-4-6',
      apiKey,
    },
    verbose: 0,
    disablePino: true,
  });

  const steps: string[] = [];

  try {
    await stagehand.init();

    const page = await stagehand.context.newPage(url);
    steps.push(`Navigated to ${url}`);

    for (const [field, value] of Object.entries(data)) {
      await stagehand.act(`Fill the "${field}" field with: ${String(value)}`);
      steps.push(`Filled field "${field}"`);
    }

    if (instructions) {
      await stagehand.act(instructions);
      steps.push(`Executed instructions: ${instructions}`);
    }

    void page;
    return { success: true, steps };
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Unknown error';
    return { success: false, steps, error: message };
  } finally {
    await stagehand.close();
  }
}
