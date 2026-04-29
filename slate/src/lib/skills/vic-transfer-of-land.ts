import type { SkillDefinition } from '@/types/skill';
import { TRANSFER_OF_LAND_PDFME_MAPPINGS } from '@/lib/pdf/pdfmeTemplates';

export const vicTransferOfLand: SkillDefinition = {
  id: 'vic_transfer_of_land',
  name: 'Transfer of Land (VIC)',
  description:
    'Prepare the transfer of land document for Victorian property settlements. Records title details, transferor (vendor), transferee (purchaser), consideration, and encumbrances.',
  icon: 'ArrowRightLeft',
  version: '1.0',
  jurisdiction: 'VIC, Australia',
  documentType: 'Transfer of Land',

  sections: [
    {
      id: 'title_details',
      title: 'Title Details',
      description: 'Certificate of Title and property details.',
      fields: [
        {
          id: 'title_volume',
          label: 'Volume',
          type: 'text',
          placeholder: 'e.g. 10249',
          required: true,
        },
        {
          id: 'title_folio',
          label: 'Folio',
          type: 'text',
          placeholder: 'e.g. 843',
          required: true,
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
          id: 'property_address',
          label: 'Property Address',
          type: 'text',
          required: true,
        },
      ],
    },
    {
      id: 'transferor',
      title: 'Transferor (Vendor)',
      description: 'Details of the transferor — the party transferring the title.',
      fields: [
        {
          id: 'transferor_name',
          label: 'Transferor Name(s)',
          type: 'text',
          required: true,
        },
        {
          id: 'transferor_address',
          label: 'Transferor Address',
          type: 'text',
          required: true,
        },
      ],
    },
    {
      id: 'transferee',
      title: 'Transferee (Purchaser)',
      description: 'Details of the transferee — the party receiving the title.',
      fields: [
        {
          id: 'transferee_name',
          label: 'Transferee Name(s)',
          type: 'text',
          required: true,
          profileKey: 'full_name',
        },
        {
          id: 'transferee_address',
          label: 'Address to which certificate of title to be sent',
          type: 'text',
          required: true,
          profileKey: 'address_line_1',
        },
        {
          id: 'consideration',
          label: 'Consideration (Purchase Price)',
          type: 'currency',
          placeholder: 'e.g. 750000',
          required: true,
        },
      ],
    },
    {
      id: 'encumbrances',
      title: 'Encumbrances',
      description: 'Any encumbrances, easements, or covenants remaining on title after transfer.',
      fields: [
        {
          id: 'encumbrance_details',
          label: 'Encumbrances / Reservations',
          type: 'textarea',
          placeholder: 'e.g. Right of Way (Instrument No. AT1234567)...',
          helpText: 'List any easements, covenants or encumbrances that will remain on title after transfer. Enter NIL if none.',
        },
      ],
    },
    {
      id: 'execution',
      title: 'Execution',
      description: 'Date and witness details for execution of the transfer.',
      fields: [
        {
          id: 'execution_date',
          label: 'Date of Execution',
          type: 'date',
          placeholder: 'dd/mm/yyyy',
        },
        {
          id: 'witness_name',
          label: 'Witness Name',
          type: 'text',
        },
        {
          id: 'witness_address',
          label: 'Witness Address',
          type: 'text',
        },
      ],
    },
  ],

  fieldMappings: [
    // Title details
    { skillFieldId: 'title_volume', pdfFieldName: 'Title Volume' },
    { skillFieldId: 'title_folio', pdfFieldName: 'Title Folio' },
    { skillFieldId: 'lot_number', pdfFieldName: 'Lot Number' },
    { skillFieldId: 'plan_number', pdfFieldName: 'Plan Number' },
    { skillFieldId: 'property_address', pdfFieldName: 'Property Address' },
    // Transferor
    { skillFieldId: 'transferor_name', pdfFieldName: 'Transferor Name' },
    { skillFieldId: 'transferor_address', pdfFieldName: 'Transferor Address' },
    // Transferee
    { skillFieldId: 'transferee_name', pdfFieldName: 'Transferee Name' },
    { skillFieldId: 'transferee_address', pdfFieldName: 'Transferee Address' },
    { skillFieldId: 'consideration', pdfFieldName: 'Consideration', transform: 'currency_au' },
    // Encumbrances
    { skillFieldId: 'encumbrance_details', pdfFieldName: 'Encumbrance Details' },
    // Execution
    { skillFieldId: 'execution_date', pdfFieldName: 'Execution Date', transform: 'date_au' },
    { skillFieldId: 'witness_name', pdfFieldName: 'Witness Name' },
    { skillFieldId: 'witness_address', pdfFieldName: 'Witness Address' },
  ],

  computedFields: [],

  pdfmeFieldMappings: TRANSFER_OF_LAND_PDFME_MAPPINGS,
};
