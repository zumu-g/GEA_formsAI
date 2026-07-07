import type { SkillDefinition } from '@/types/skill';
import { AUCTION_AUTHORITY_PDFME_MAPPINGS } from '@/lib/pdf/pdfmeTemplates';

export const auctionAuthority: SkillDefinition = {
  id: 'vic_auction_authority',
  name: 'Auction Authority',
  description:
    "Agent's authority to sell a property by auction under the Estate Agents Act 1980 (Vic). Draft only — field content is researched from statutory/industry sources, not a verbatim signed form. Confirm against a real copy before relying on it.",
  icon: 'Gavel',
  version: '0.1.0',
  jurisdiction: 'VIC, Australia',
  documentType: 'Auction Authority',
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
      description: 'The property being offered for sale by auction.',
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
      id: 'auction_details',
      title: 'Auction Details',
      description: 'Date, venue, and reserve for the auction.',
      fields: [
        {
          id: 'auctionDate',
          label: 'Auction Date',
          type: 'date',
          required: true,
        },
        {
          id: 'auction_time',
          label: 'Auction Time',
          type: 'text',
          placeholder: 'e.g. 11:00am',
        },
        {
          id: 'auction_venue',
          label: 'Auction Venue',
          type: 'text',
          placeholder: 'e.g. In-room, or on-site at the property',
        },
        {
          id: 'reserve_price',
          label: 'Reserve Price',
          type: 'currency',
          helpText: 'Often set closer to the auction date — may be left blank until confirmed with the vendor.',
        },
        {
          id: 'vendor_bid_disclosure',
          label: 'Vendor Bid Disclosure',
          type: 'checkbox',
          helpText: 'Tick to confirm the vendor has been informed of the vendor-bid disclosure requirement.',
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
      description: 'The authority ends 30 days after the auction date (statutory cap for auction authorities).',
      fields: [
        {
          id: 'authorityEndDate',
          label: 'Authority End Date',
          type: 'date',
          computed: true,
          helpText: 'Computed automatically as 30 days after the auction date.',
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
    { skillFieldId: 'auctionDate', pdfFieldName: 'Auction Date', transform: 'date_au' },
    { skillFieldId: 'auction_time', pdfFieldName: 'Auction Time' },
    { skillFieldId: 'auction_venue', pdfFieldName: 'Auction Venue' },
    { skillFieldId: 'reserve_price', pdfFieldName: 'Reserve Price', transform: 'currency_au' },
    { skillFieldId: 'vendor_bid_disclosure', pdfFieldName: 'Vendor Bid Disclosure Checkbox' },
    { skillFieldId: 'commission_amount', pdfFieldName: 'Commission Amount' },
    { skillFieldId: 'marketing_expenses', pdfFieldName: 'Marketing Expenses' },
    { skillFieldId: 'authorityEndDate', pdfFieldName: 'Authority End Date', transform: 'date_au' },
  ],

  computedFields: [
    {
      skillFieldId: 'authorityEndDate',
      formula: 'add_days',
      operands: ['auctionDate'],
      days: 30,
      pdfFieldName: 'Authority End Date',
    },
  ],

  pdfmeFieldMappings: AUCTION_AUTHORITY_PDFME_MAPPINGS,
};
