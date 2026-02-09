import { FieldMapping } from './form';

export interface Template {
  id: string;
  userId: string;
  formId: string;
  name: string;
  description?: string;
  fieldMappings: FieldMapping[];
  isPublic: boolean;
  useCount: number;
  createdAt: string;
  updatedAt: string;
}
