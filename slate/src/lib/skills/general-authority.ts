import type { SkillDefinition } from '@/types/skill';
import { GENERAL_AUTHORITY_PDFME_MAPPINGS } from '@/lib/pdf/pdfmeTemplates';

export const generalAuthority: SkillDefinition = {
  id: 'vic_general_authority',
  name: 'General (Non-Exclusive) Authority',
  description:
    "Open (non-exclusive) authority to sell a property under the Estate Agents Act 1980 (Vic). Draft only — field content is researched from statutory/industry sources, not a verbatim signed form. Confirm against a real copy before relying on it.",
  icon: 'FileText',
  version: '0.1.0',
  jurisdiction: 'VIC, Australia',
  documentType: 'General Authority',
  draftStatus: 'unverified',

  sections: [
    {
      id: 'vendor_details',
      title: 'Vendor Details',
      description: 'Details of the vendor(s) appointing the agent.',
      fields: [
        {
          id: 'vendor_name',
          label: 'Vendor Name(s)',
          type: 'text',
          required: true,
          profileKey: 'full_name',
        },
        {
          id: 'vendor_address',
          label: 'Vendor Address',
          type: 'text',
          required: true,
          profileKey: 'address_line_1',
        },
        {
          id: 'vendor_phone',
          label: 'Vendor Telephone',
          type: 'phone',
          profileKey: 'phone',
        },
      ],
    },
    {
      id: 'property_details',
      title: 'Property Details',
      description: 'The property being offered for sale.',
      fields: [
        {
          id: 'property_address',
          label: 'Property Address',
          type: 'text',
          required: true,
        },
        {
          id: 'chattels_included',
          label: 'Chattels Included in Sale',
          type: 'textarea',
        },
      ],
    },
    {
      id: 'non_exclusivity_clause',
      title: 'Non-Exclusivity Clause',
      description:
        'This authority is non-exclusive: commission is only payable if this agent is the effective/procuring cause of the sale. No sole-agency tail clause applies.',
      fields: [
        {
          id: 'non_exclusivity_clause',
          label: 'Non-Exclusivity Confirmed',
          type: 'checkbox',
          required: true,
          helpText: 'Confirms this is an open/general authority, distinct from an exclusive (sole) authority.',
        },
      ],
    },
    {
      id: 'commission_marketing',
      title: 'Commission & Marketing Expenses',
      description: 'Commission is negotiable and must be disclosed as required by the Estate Agents Act 1980.',
      fields: [
        {
          id: 'commission_amount',
          label: 'Commission (amount or %)',
          type: 'text',
          required: true,
          helpText: 'If a percentage, show a worked dollar example on the printed form.',
        },
        {
          id: 'marketing_expenses',
          label: 'Marketing/Advertising Expenses (itemised estimate)',
          type: 'textarea',
          helpText: 'Payable whether or not the property sells, as required by statute.',
        },
      ],
    },
    {
      id: 'authority_period',
      title: 'Authority Period',
      description: 'Open-ended — no statutory expiry cap. Terminable by either party.',
      fields: [
        {
          id: 'startDate',
          label: 'Authority Start Date (signing date)',
          type: 'date',
          required: true,
        },
      ],
    },
  ],

  fieldMappings: [
    { skillFieldId: 'vendor_name', pdfFieldName: 'Vendor Name' },
    { skillFieldId: 'vendor_address', pdfFieldName: 'Vendor Address' },
    { skillFieldId: 'vendor_phone', pdfFieldName: 'Vendor Telephone' },
    { skillFieldId: 'property_address', pdfFieldName: 'Property Address' },
    { skillFieldId: 'chattels_included', pdfFieldName: 'Chattels Included' },
    { skillFieldId: 'non_exclusivity_clause', pdfFieldName: 'Non-Exclusivity Clause Checkbox' },
    { skillFieldId: 'commission_amount', pdfFieldName: 'Commission Amount' },
    { skillFieldId: 'marketing_expenses', pdfFieldName: 'Marketing Expenses' },
    { skillFieldId: 'startDate', pdfFieldName: 'Authority Start Date', transform: 'date_au' },
  ],

  computedFields: [],

  pdfmeFieldMappings: GENERAL_AUTHORITY_PDFME_MAPPINGS,
};
