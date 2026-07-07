export interface DetectedField {
  id: string;           // snake_case unique id e.g. "purchaser_name"
  label: string;        // Human readable label e.g. "Purchaser Name(s)"
  type: 'text' | 'checkbox' | 'date' | 'currency' | 'signature' | 'textarea';
  page: number;         // 1-indexed
  bbox: {               // Normalised 0-1 of page dimensions (top-left origin)
    x: number;
    y: number;
    w: number;
    h: number;
  };
  required: boolean;
  value: string;        // Current fill value (starts empty)
  profileKey?: string;  // Matches key in DataProfile.data e.g. "full_name", "email", "phone"
  confidence: number;   // 0-1
}

export interface PageDimension {
  width: number;  // PDF points
  height: number; // PDF points
}

export interface VisionDetectResult {
  fields: DetectedField[];
  pageImages: string[];  // base64 PNG strings, one per page (index 0 = page 1)
  pageCount: number;
  pageDimensions: PageDimension[];  // index 0 = page 1
  error?: string;
}

export type DetectionMethod = 'acroform' | 'pdfplumber' | 'commonforms' | 'docai' | 'docling' | 'vision' | 'zerox' | 'empty';

export interface SmartDetectResult {
  fields: DetectedField[];
  pageImages: string[];
  pageCount: number;
  pageDimensions: PageDimension[];
  detectionMethod: DetectionMethod;
  error?: string;
}
