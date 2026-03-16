import { NextRequest, NextResponse } from 'next/server';
import { getTask } from '@/lib/services/skyvernClient';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ taskId: string }> }
) {
  try {
    const { taskId } = await params;
    const task = await getTask(taskId);

    return NextResponse.json({
      success: true,
      data: task,
    });
  } catch (error) {
    console.error('Web fill status error:', error);
    return NextResponse.json(
      { success: false, error: { code: 'STATUS_FAILED', message: 'Failed to get task status.' } },
      { status: 500 }
    );
  }
}
