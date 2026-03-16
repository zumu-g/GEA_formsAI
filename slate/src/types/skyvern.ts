export type SkyvernTaskStatus = 'created' | 'queued' | 'running' | 'completed' | 'failed' | 'terminated';

export interface SkyvernTask {
  task_id: string;
  status: SkyvernTaskStatus;
  url: string;
  navigation_goal: string;
  extracted_information: Record<string, unknown> | null;
  created_at: string;
  completed_at: string | null;
  failure_reason: string | null;
}

export interface SkyvernCreateTaskRequest {
  url: string;
  navigation_goal: string;
  data_extraction_goal?: string;
  navigation_payload?: Record<string, string>;
}
