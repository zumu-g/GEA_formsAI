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

// Extended resume / professional profile keys
export const PROFILE_RESUME_KEYS = {
  linkedin_url: 'LinkedIn URL',
  website_url: 'Website / Portfolio',
  skills: 'Skills (comma-separated)',
  years_experience: 'Years of Experience',
  current_employer: 'Current Employer',
  current_role: 'Current Role',
  education_level: 'Highest Education',
  cover_letter_blurb: 'Cover Letter / Bio',
  abn: 'ABN',
  acn: 'ACN',
  licence_number: 'Licence Number',
  licence_type: 'Licence Type',
} as const;

export type ProfileResumeKey = keyof typeof PROFILE_RESUME_KEYS;

// All known profile keys (legacy + resume extensions)
export const ALL_PROFILE_KEYS = [
  ...DEFAULT_PROFILE_FIELDS,
  ...Object.keys(PROFILE_RESUME_KEYS) as ProfileResumeKey[],
] as const;
