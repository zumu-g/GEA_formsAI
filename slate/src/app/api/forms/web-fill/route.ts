import { NextRequest, NextResponse } from 'next/server';
import { createTask } from '@/lib/services/skyvernClient';
import { fillWebFormWithStagehand } from '@/lib/services/stagehandClient';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { url, instructions, profileData, backend = 'skyvern' } = body;

    if (!url || !instructions) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'URL and instructions are required.' } },
        { status: 400 }
      );
    }

    if (backend === 'stagehand') {
      const result = await fillWebFormWithStagehand(url, instructions, profileData ?? {});

      if (!result.success) {
        return NextResponse.json(
          { success: false, error: { code: 'WEB_FILL_FAILED', message: result.error ?? 'Stagehand fill failed.' } },
          { status: 500 }
        );
      }

      return NextResponse.json({
        success: true,
        data: {
          taskId: crypto.randomUUID(),
          status: 'completed',
        },
      });
    }

    const task = await createTask({
      url,
      navigation_goal: instructions,
      navigation_payload: profileData,
    });

    return NextResponse.json({
      success: true,
      data: {
        taskId: task.task_id,
        status: task.status,
      },
    });
  } catch (error) {
    console.error('Web fill error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'WEB_FILL_FAILED', message: 'Failed to create web fill task.' } },
      { status: 500 }
    );
  }
}
