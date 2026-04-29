import type { SkillDefinition } from '@/types/skill';
import { SECTION_32_PDFME_MAPPINGS } from '@/lib/pdf/pdfmeTemplates';

export const section32Offer: SkillDefinition = {
  id: 'vic_section_32',
  name: 'Section 32 Statement',
  description:
    "Vendor's statement under Section 32 of the Sale of Land Act 1962 (VIC). Covers title details, planning, rates, and statutory disclosures.",
  icon: 'Scale',
  version: '1.0',
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
          validation: {
            pattern: '^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$',
            patternMessage: 'Please enter a valid email address.',
          },
        },
      ],
    },
    {
      id: 'vendor_solicitor',
      title: "Vendor's Legal Practitioner",
      description: 'Details of the vendor\'s solicitor or conveyancer.',
      fields: [
        {
          id: 'vendor_solicitor_name',
          label: 'Name',
          type: 'text',
          placeholder: 'e.g. Jane Smith',
        },
        {
          id: 'vendor_solicitor_firm',
          label: 'Firm Name',
          type: 'text',
          placeholder: 'e.g. Smith & Partners Conveyancing',
        },
        {
          id: 'vendor_solicitor_address',
          label: 'Address',
          type: 'text',
          placeholder: 'e.g. 1 Queen Street, Melbourne VIC 3000',
        },
        {
          id: 'vendor_solicitor_phone',
          label: 'Telephone',
          type: 'phone',
          placeholder: 'e.g. 03 9123 4567',
        },
        {
          id: 'vendor_solicitor_email',
          label: 'Email',
          type: 'email',
          placeholder: 'e.g. info@smithconveyancing.com.au',
        },
      ],
    },
    {
      id: 'property_details',
      title: 'Property & Title',
      description: 'Property address and Certificate of Title reference information.',
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
          label: 'Volume',
          type: 'text',
          placeholder: 'e.g. 10249',
        },
        {
          id: 'title_folio',
          label: 'Folio',
          type: 'text',
          placeholder: 'e.g. 843',
        },
        {
          id: 'lot_number',
          label: 'Lot Number',
          type: 'text',
        },
        {
          id: 'plan_number',
          label: 'Plan Number',
          type: 'text',
        },
        {
          id: 'title_type',
          label: 'Instrument of Ownership',
          type: 'text',
          placeholder: 'e.g. Freehold, Leasehold, Strata Title',
        },
        {
          id: 'council_name',
          label: 'Municipal Council',
          type: 'text',
          placeholder: 'e.g. Knox City Council',
        },
      ],
    },
    {
      id: 'outgoings_encumbrances',
      title: 'Outgoings & Encumbrances',
      description: 'Annual outgoings and any mortgages or encumbrances on the property.',
      fields: [
        {
          id: 'council_rates',
          label: 'Council Rates (per year)',
          type: 'currency',
          placeholder: 'e.g. 1850',
        },
        {
          id: 'water_authority',
          label: 'Water Authority',
          type: 'text',
          placeholder: 'e.g. South East Water',
        },
        {
          id: 'water_rates',
          label: 'Water Rates (per year)',
          type: 'currency',
          placeholder: 'e.g. 980',
        },
        {
          id: 'land_tax',
          label: 'Land Tax (if applicable)',
          type: 'currency',
          placeholder: '0.00',
          helpText: 'Leave blank if primary residence.',
        },
        {
          id: 'owners_corp_fees',
          label: 'Owners Corporation Fees (per year)',
          type: 'currency',
          placeholder: '0.00',
          helpText: 'Also known as body corporate fees. Leave blank if not applicable.',
        },
        {
          id: 'other_outgoings',
          label: 'Other Outgoings',
          type: 'currency',
          placeholder: '0.00',
        },
        {
          id: 'mortgage_holder',
          label: 'Mortgage Holder (if applicable)',
          type: 'text',
          placeholder: 'e.g. Commonwealth Bank',
        },
        {
          id: 'mortgage_amount',
          label: 'Approximate Mortgage Amount',
          type: 'currency',
          placeholder: 'e.g. 450000',
        },
        {
          id: 'mortgage_type',
          label: 'Mortgage Type',
          type: 'text',
          placeholder: 'e.g. Fixed, Variable, Interest Only',
        },
      ],
    },
    {
      id: 'planning_permits',
      title: 'Planning & Permits',
      description: 'Zoning, planning overlays, and building permits issued in the last 7 years.',
      fields: [
        {
          id: 'zoning_code',
          label: 'Zoning Code',
          type: 'text',
          placeholder: 'e.g. GRZ1 (General Residential Zone)',
          helpText: 'Find on VicPlan or council website.',
        },
        {
          id: 'planning_overlay',
          label: 'Planning Overlay (if any)',
          type: 'text',
          placeholder: 'e.g. BMO (Bushfire Management Overlay)',
          helpText: 'Enter N/A if no overlay applies.',
        },
        {
          id: 'building_permits_7yrs',
          label: 'Building Permits Issued (last 7 years)',
          type: 'checkbox',
          helpText: 'Check if any building permits were issued in the last 7 years.',
        },
        {
          id: 'permit_details',
          label: 'Permit Details',
          type: 'textarea',
          placeholder: 'Describe permit type, date, and work done...',
          helpText: 'Required if any permits were issued in the last 7 years.',
        },
        {
          id: 'owner_builder',
          label: 'Owner Builder',
          type: 'checkbox',
          helpText: 'Check if any works were done under an owner builder permit.',
        },
      ],
    },
    {
      id: 'services',
      title: 'Services',
      description: 'Services connected to the property.',
      fields: [
        {
          id: 'service_water',
          label: 'Water connected',
          type: 'checkbox',
        },
        {
          id: 'service_drainage',
          label: 'Drainage connected',
          type: 'checkbox',
        },
        {
          id: 'service_sewerage',
          label: 'Sewerage connected',
          type: 'checkbox',
        },
        {
          id: 'service_electricity',
          label: 'Electricity connected',
          type: 'checkbox',
        },
        {
          id: 'service_gas',
          label: 'Gas connected',
          type: 'checkbox',
        },
        {
          id: 'service_telephone',
          label: 'Telephone/NBN connected',
          type: 'checkbox',
        },
      ],
    },
    {
      id: 'special_conditions',
      title: 'Special Conditions & Notices',
      description: 'Chattels included in the sale and any special conditions or statutory notices.',
      fields: [
        {
          id: 'chattels_included',
          label: 'Chattels / Inclusions',
          type: 'textarea',
          placeholder: 'e.g. Dishwasher, blinds, air conditioner (model XYZ)...',
          helpText: 'List all fixtures and chattels included in the sale.',
        },
        {
          id: 'special_conditions',
          label: 'Special Conditions or Notices',
          type: 'textarea',
          placeholder: 'Enter any special conditions or statutory notices to be disclosed to the purchaser...',
        },
      ],
    },
  ],

  fieldMappings: [
    // Vendor details
    { skillFieldId: 'vendor_name', pdfFieldName: 'Vendor Name' },
    { skillFieldId: 'vendor_address', pdfFieldName: 'Vendor Address' },
    { skillFieldId: 'vendor_phone', pdfFieldName: 'Vendor Telephone' },
    { skillFieldId: 'vendor_email', pdfFieldName: 'Vendor Email' },
    // Vendor solicitor
    { skillFieldId: 'vendor_solicitor_name', pdfFieldName: 'Vendor Solicitor Name' },
    { skillFieldId: 'vendor_solicitor_firm', pdfFieldName: 'Vendor Solicitor Firm' },
    { skillFieldId: 'vendor_solicitor_address', pdfFieldName: 'Vendor Solicitor Address' },
    { skillFieldId: 'vendor_solicitor_phone', pdfFieldName: 'Vendor Solicitor Telephone' },
    { skillFieldId: 'vendor_solicitor_email', pdfFieldName: 'Vendor Solicitor Email' },
    // Property & title
    { skillFieldId: 'property_address', pdfFieldName: 'Property Address' },
    { skillFieldId: 'title_volume', pdfFieldName: 'Title Volume' },
    { skillFieldId: 'title_folio', pdfFieldName: 'Title Folio' },
    { skillFieldId: 'lot_number', pdfFieldName: 'Lot Number' },
    { skillFieldId: 'plan_number', pdfFieldName: 'Plan Number' },
    { skillFieldId: 'title_type', pdfFieldName: 'Instrument of Ownership' },
    { skillFieldId: 'council_name', pdfFieldName: 'Municipal Council' },
    // Outgoings & encumbrances
    { skillFieldId: 'council_rates', pdfFieldName: 'Council Rates', transform: 'currency_au' },
    { skillFieldId: 'water_authority', pdfFieldName: 'Water Authority' },
    { skillFieldId: 'water_rates', pdfFieldName: 'Water Rates', transform: 'currency_au' },
    { skillFieldId: 'land_tax', pdfFieldName: 'Land Tax', transform: 'currency_au' },
    { skillFieldId: 'owners_corp_fees', pdfFieldName: 'Owners Corporation Fees', transform: 'currency_au' },
    { skillFieldId: 'other_outgoings', pdfFieldName: 'Other Outgoings', transform: 'currency_au' },
    { skillFieldId: 'mortgage_holder', pdfFieldName: 'Mortgage Holder' },
    { skillFieldId: 'mortgage_amount', pdfFieldName: 'Mortgage Amount', transform: 'currency_au' },
    { skillFieldId: 'mortgage_type', pdfFieldName: 'Mortgage Type' },
    // Planning & permits
    { skillFieldId: 'zoning_code', pdfFieldName: 'Zoning Code' },
    { skillFieldId: 'planning_overlay', pdfFieldName: 'Planning Overlay' },
    { skillFieldId: 'building_permits_7yrs', pdfFieldName: 'Building Permits 7 Years Checkbox' },
    { skillFieldId: 'permit_details', pdfFieldName: 'Permit Details' },
    { skillFieldId: 'owner_builder', pdfFieldName: 'Owner Builder Checkbox' },
    // Services
    { skillFieldId: 'service_water', pdfFieldName: 'Service Water Checkbox' },
    { skillFieldId: 'service_drainage', pdfFieldName: 'Service Drainage Checkbox' },
    { skillFieldId: 'service_sewerage', pdfFieldName: 'Service Sewerage Checkbox' },
    { skillFieldId: 'service_electricity', pdfFieldName: 'Service Electricity Checkbox' },
    { skillFieldId: 'service_gas', pdfFieldName: 'Service Gas Checkbox' },
    { skillFieldId: 'service_telephone', pdfFieldName: 'Service Telephone Checkbox' },
    // Special conditions
    { skillFieldId: 'chattels_included', pdfFieldName: 'Chattels Included' },
    { skillFieldId: 'special_conditions', pdfFieldName: 'Special Conditions Text' },
  ],

  computedFields: [],

  pdfmeFieldMappings: SECTION_32_PDFME_MAPPINGS,
};
