import type { SkillDefinition } from '@/types/skill';
import { EXCLUSIVE_SALE_AUTHORITY_PDFME_MAPPINGS } from '@/lib/pdf/pdfmeTemplates';

export const exclusiveSaleAuthority: SkillDefinition = {
  id: 'vic_exclusive_sale_authority',
  name: 'Exclusive Sale Authority',
  description:
    "Exclusive (sole) agency authority to sell a property under the Estate Agents Act 1980 (Vic). Draft only — field content is researched from statutory/industry sources, not a verbatim signed form. Confirm against a real copy before relying on it.",
  icon: 'FileSignature',
  version: '0.1.0',
  jurisdiction: 'VIC, Australia',
  documentType: 'Exclusive Sale Authority',
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
      id: 'sole_agency_clause',
      title: 'Sole Agency Clause',
      description:
        'This authority is exclusive: the agent is entitled to commission even if the vendor or another party finds the buyer during the term.',
      fields: [
        {
          id: 'soleAgencyClause',
          label: 'Exclusivity Confirmed',
          type: 'checkbox',
          required: true,
          helpText: 'Confirms this is a sole/exclusive agency, distinct from a general (non-exclusive) authority.',
        },
        {
          id: 'tail_clause_days',
          label: 'Introduced-Prospect Tail Clause (days)',
          type: 'text',
          defaultValue: '120',
          helpText:
            'Negotiable default, not a statutory figure (unlike the 60-day expiry below) — the number of days after expiry that commission is still payable if a buyer introduced during the authority period purchases the property. Edit or clear per the agreement with the vendor.',
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
      description:
        'The authority ends 60 days after signing for a private-treaty sale (statutory cap). This cap does not apply if the property instead goes to auction — use the Auction Authority skill for that case.',
      fields: [
        {
          id: 'startDate',
          label: 'Authority Start Date (signing date)',
          type: 'date',
          required: true,
        },
        {
          id: 'authorityEndDate',
          label: 'Authority End Date',
          type: 'date',
          computed: true,
          helpText: 'Computed automatically as 60 days after the signing date.',
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
    { skillFieldId: 'soleAgencyClause', pdfFieldName: 'Sole Agency Clause Checkbox' },
    { skillFieldId: 'tail_clause_days', pdfFieldName: 'Tail Clause Days' },
    { skillFieldId: 'commission_amount', pdfFieldName: 'Commission Amount' },
    { skillFieldId: 'marketing_expenses', pdfFieldName: 'Marketing Expenses' },
    { skillFieldId: 'startDate', pdfFieldName: 'Authority Start Date', transform: 'date_au' },
    { skillFieldId: 'authorityEndDate', pdfFieldName: 'Authority End Date', transform: 'date_au' },
  ],

  computedFields: [
    {
      skillFieldId: 'authorityEndDate',
      formula: 'add_days',
      operands: ['startDate'],
      days: 60,
      pdfFieldName: 'Authority End Date',
    },
  ],

  pdfmeFieldMappings: EXCLUSIVE_SALE_AUTHORITY_PDFME_MAPPINGS,
};
