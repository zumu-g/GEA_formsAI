import type { SkyvernTask, SkyvernCreateTaskRequest } from '@/types/skyvern';

const SKYVERN_URL = process.env.SKYVERN_API_URL || 'http://localhost:8080/api/v1';
const SKYVERN_API_KEY = process.env.SKYVERN_API_KEY || '';

async function skyvernFetch(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(`${SKYVERN_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...(SKYVERN_API_KEY && { 'x-api-key': SKYVERN_API_KEY }),
      ...init?.headers,
    },
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Skyvern API error ${res.status}: ${text}`);
  }

  return res;
}

export async function createTask(request: SkyvernCreateTaskRequest): Promise<SkyvernTask> {
  const res = await skyvernFetch('/tasks', {
    method: 'POST',
    body: JSON.stringify(request),
  });
  return res.json();
}

export async function getTask(taskId: string): Promise<SkyvernTask> {
  const res = await skyvernFetch(`/tasks/${taskId}`);
  return res.json();
}

export async function getTaskSteps(taskId: string): Promise<Record<string, unknown>[]> {
  const res = await skyvernFetch(`/tasks/${taskId}/steps`);
  return res.json();
}
