// Types mirroring the form_filling_app FastAPI backend

export interface BackendFieldInfo {
  field_id: string;
  field_type: 'text' | 'checkbox' | 'dropdown' | 'radio';
  page: number;
  label_context: string;
  friendly_label: string;
  current_value: string | null;
  options: string[] | null;
  native_field_name: string;
}

export interface BackendAnalyzeResponse {
  success: boolean;
  message: string;
  fields: BackendFieldInfo[];
  field_count: number;
}

export type StreamEventType =
  | 'init'
  | 'text'
  | 'tool_start'
  | 'tool_end'
  | 'complete'
  | 'pdf_ready'
  | 'error';

export interface StreamEvent {
  type: StreamEventType;
  data: Record<string, unknown>;
  timestamp: number;
}
