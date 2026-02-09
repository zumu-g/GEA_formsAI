export interface FormField {
  id: string;
  formId: string;
  fieldName: string;
  fieldType: 'text' | 'checkbox' | 'radio' | 'date' | 'signature' | 'dropdown';
  pageNumber: number;
  x: number;
  y: number;
  width: number;
  height: number;
  isRequired: boolean;
  aiDetected: boolean;
  value?: string;
}

export interface Form {
  id: string;
  userId: string;
  originalName: string;
  storagePath: string;
  fileSize: number;
  pageCount: number;
  detectedFields: FormField[];
  status: 'uploaded' | 'detecting' | 'ready' | 'error';
  createdAt: string;
}

export interface FillSession {
  id: string;
  userId: string;
  formId: string;
  templateId?: string;
  profileId?: string;
  filledData: Record<string, string>;
  outputPath?: string;
  creditsUsed: number;
  fillMethod: 'manual' | 'template' | 'ai_auto' | 'batch' | 'recurring' | 'api';
  createdAt: string;
}

export interface FieldMapping {
  fieldId: string;
  profileKey: string;
  value?: string;
}
