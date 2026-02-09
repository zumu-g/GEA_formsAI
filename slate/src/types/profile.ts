export interface DataProfile {
  id: string;
  userId: string;
  name: string;
  data: Record<string, string>;
  isDefault: boolean;
  createdAt: string;
  updatedAt: string;
}

export const DEFAULT_PROFILE_FIELDS = [
  'full_name',
  'first_name',
  'last_name',
  'email',
  'phone',
  'address_line_1',
  'address_line_2',
  'city',
  'state',
  'zip_code',
  'country',
  'company_name',
  'job_title',
  'tax_id',
  'date_of_birth',
  'ssn_last_4',
] as const;

export type ProfileFieldKey = typeof DEFAULT_PROFILE_FIELDS[number];
