import type { SkillDefinition } from '@/types/skill';

export const section32Offer: SkillDefinition = {
  id: 'vic_section_32',
  name: 'Section 32 Statement',
  description:
    "Vendor's statement under Section 32 of the Sale of Land Act 1962 (VIC). Covers title details, planning, rates, and statutory disclosures.",
  icon: 'Scale',
  version: '0.1-draft',
  jurisdiction: 'VIC, Australia',
  documentType: "Vendor's Statement (Section 32)",

  sections: [
    {
      id: 'vendor_details',
      title: 'Vendor Details',
      description: 'Details of the vendor (seller) of the property.',
      fields: [
        {
          id: 'vendor_name',
          label: 'Vendor Name(s)',
          type: 'text',
          placeholder: 'e.g. Callan James Inglis',
          required: true,
          profileKey: 'full_name',
        },
        {
          id: 'vendor_address',
          label: 'Address',
          type: 'text',
          placeholder: 'e.g. 28 Durham Road, Kilsyth VIC 3137',
          required: true,
          profileKey: 'address_line_1',
        },
        {
          id: 'vendor_phone',
          label: 'Telephone',
          type: 'phone',
          profileKey: 'phone',
        },
        {
          id: 'vendor_email',
          label: 'Email',
          type: 'email',
          profileKey: 'email',
        },
      ],
    },
    {
      id: 'property_details',
      title: 'Property & Title',
      description: 'Property address and title reference information.',
      fields: [
        {
          id: 'property_address',
          label: 'Property Address',
          type: 'text',
          placeholder: 'e.g. 37 Sneddon Drive, Narre Warren South VIC 3805',
          required: true,
        },
        {
          id: 'title_volume',
          label: 'Certificate of Title — Volume',
          type: 'text',
          placeholder: 'e.g. 10249',
        },
        {
          id: 'title_folio',
          label: 'Certificate of Title — Folio',
          type: 'text',
          placeholder: 'e.g. 843',
        },
        {
          id: 'lot_number',
          label: 'Lot Number',
          type: 'text',
          placeholder: 'e.g. 129',
        },
        {
          id: 'plan_number',
          label: 'Plan Number',
          type: 'text',
          placeholder: 'e.g. 335322J',
        },
      ],
    },
  ],

  fieldMappings: [
    { skillFieldId: 'vendor_name', pdfFieldName: 'Vendor Name' },
    { skillFieldId: 'vendor_address', pdfFieldName: 'Vendor Address' },
    { skillFieldId: 'vendor_phone', pdfFieldName: 'Vendor Telephone' },
    { skillFieldId: 'vendor_email', pdfFieldName: 'Vendor Email' },
    { skillFieldId: 'property_address', pdfFieldName: 'Property Address' },
    { skillFieldId: 'title_volume', pdfFieldName: 'Title Volume' },
    { skillFieldId: 'title_folio', pdfFieldName: 'Title Folio' },
    { skillFieldId: 'lot_number', pdfFieldName: 'Lot Number' },
    { skillFieldId: 'plan_number', pdfFieldName: 'Plan Number' },
  ],

  computedFields: [],
};
