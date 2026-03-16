import { NextRequest, NextResponse } from 'next/server';
import { createTask } from '@/lib/services/skyvernClient';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { url, instructions, profileData } = body;

    if (!url || !instructions) {
      return NextResponse.json(
        { success: false, error: { code: 'INVALID_INPUT', message: 'URL and instructions are required.' } },
        { status: 400 }
      );
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
