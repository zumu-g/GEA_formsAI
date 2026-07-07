/**
 * Section 32 extraction schema.
 *
 * This is the *read* side of `section-32-offer.ts` (the fill skill). Field IDs are
 * deliberately kept aligned with `section32Offer` field IDs so an extracted document
 * can round-trip back into the fill flow (extract → review → auto-fill) without a
 * mapping layer. See `slate/src/lib/skills/section-32-offer.ts`.
 *
 * Hard rules enforced by the extraction prompt:
 *  - Never fabricate legal/financial values. If a value is absent → `null`.
 *  - A value the model is unsure about is returned with `confidence: 'low'` and listed
 *    in `meta.uncertainFields`; the summary renders it with an `[uncertain]` marker.
 */

export type FieldConfidence = 'high' | 'low';

/** Where the extracted value ultimately came from. */
export type ExtractionSource = 'text' | 'ocr' | 'vision';

/**
 * A single extracted field. `value` is `null` when the document does not state it.
 * `confidence` is only meaningful when `value` is non-null.
 */
export interface ExtractedField<T = string> {
  value: T | null;
  confidence: FieldConfidence;
  /** Optional: which extraction stage produced this value. */
  source?: ExtractionSource;
  /** Optional free-text note, e.g. why a value is uncertain. */
  note?: string;
}

/** Vendor (seller) and their conveyancer. */
export interface VendorDetails {
  vendor_name: ExtractedField; // may list multiple names
  vendor_address: ExtractedField;
  vendor_phone: ExtractedField;
  vendor_email: ExtractedField;
  vendor_solicitor_name: ExtractedField;
  vendor_solicitor_firm: ExtractedField;
  vendor_solicitor_address: ExtractedField;
  vendor_solicitor_phone: ExtractedField;
  vendor_solicitor_email: ExtractedField;
}

/** Property identification + title particulars. */
export interface PropertyTitle {
  property_address: ExtractedField;
  title_volume: ExtractedField;
  title_folio: ExtractedField;
  lot_number: ExtractedField;
  plan_number: ExtractedField;
  registered_proprietors: ExtractedField;
  title_type: ExtractedField;
  restrictions_caveats: ExtractedField; // restrictive covenants / caveats
  easements: ExtractedField;
  council_name: ExtractedField;
}

/** Annual outgoings, mortgage and other encumbrances. */
export interface OutgoingsEncumbrances {
  council_rates: ExtractedField;
  water_authority: ExtractedField;
  water_rates: ExtractedField;
  land_tax: ExtractedField;
  owners_corp_fees: ExtractedField;
  other_outgoings: ExtractedField;
  mortgage_holder: ExtractedField;
  mortgage_amount: ExtractedField;
  mortgage_type: ExtractedField;
}

/** Owners corporation (body corporate) presence + details. */
export interface OwnersCorporation {
  /** Whether the property is affected by an owners corporation. */
  applies: ExtractedField<boolean>;
  details: ExtractedField; // OC number, manager, fees notes, etc.
}

/** Planning controls and permit history. */
export interface PlanningPermits {
  zoning_code: ExtractedField;
  planning_overlay: ExtractedField;
  /** Whether a building permit was issued in the last 7 years. */
  building_permits_7yrs: ExtractedField<boolean>;
  permit_details: ExtractedField;
  owner_builder: ExtractedField<boolean>;
}

/** Connected services (true = connected, false = explicitly not, null = not stated). */
export interface ServicesConnected {
  water: ExtractedField<boolean>;
  drainage: ExtractedField<boolean>;
  sewerage: ExtractedField<boolean>;
  electricity: ExtractedField<boolean>;
  gas: ExtractedField<boolean>;
  telephone: ExtractedField<boolean>;
}

export interface SpecialConditions {
  chattels_included: ExtractedField;
  sunset_clause: ExtractedField;
  special_conditions: ExtractedField;
}

export interface Section32Data {
  vendor: VendorDetails;
  property: PropertyTitle;
  outgoings: OutgoingsEncumbrances;
  owners_corporation: OwnersCorporation;
  planning: PlanningPermits;
  services: ServicesConnected;
  special: SpecialConditions;
}

export type ExtractionMethod = 'text' | 'ocrmypdf' | 'vision';

export interface Section32ExtractionMeta {
  /** True if the source PDF was treated as scanned/image-based. */
  scanned: boolean;
  /** True if ocrmypdf produced a searchable text layer before extraction. */
  ocrUsed: boolean;
  /** Which path produced the text the model read. */
  method: ExtractionMethod;
  /** Dotted paths (e.g. "outgoings.land_tax") of every low-confidence, non-null field. */
  uncertainFields: string[];
  /** Number of source pages, when known. */
  pageCount?: number;
}

export interface Section32Extraction {
  data: Section32Data;
  /** Plain-English summary; uncertain values are marked "[uncertain]". */
  summary: string;
  meta: Section32ExtractionMeta;
}
