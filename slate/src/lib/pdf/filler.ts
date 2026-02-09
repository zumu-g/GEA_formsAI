import { PDFDocument, rgb, StandardFonts } from 'pdf-lib';
import type { FormField } from '@/types/form';

interface FillData {
  field: FormField;
  value: string;
}

export async function fillPDF(
  pdfBytes: Uint8Array,
  fillData: FillData[]
): Promise<Uint8Array> {
  const pdfDoc = await PDFDocument.load(pdfBytes);
  const font = await pdfDoc.embedFont(StandardFonts.Helvetica);
  const pages = pdfDoc.getPages();

  // Try to fill AcroForm fields first
  const form = pdfDoc.getForm();
  const acroFields = form.getFields();

  for (const { field, value } of fillData) {
    // Try AcroForm field matching
    const acroField = acroFields.find(
      (af) => af.getName().toLowerCase() === field.fieldName.toLowerCase()
    );

    if (acroField) {
      try {
        const textField = form.getTextField(acroField.getName());
        textField.setText(value);
        continue;
      } catch {
        // Not a text field or other error — fall through to coordinate-based
      }
    }

    // Coordinate-based text placement
    const page = pages[field.pageNumber - 1];
    if (!page) continue;

    const { width: pageWidth, height: pageHeight } = page.getSize();

    // Convert percentage coordinates to absolute
    const x = (field.x / 100) * pageWidth;
    const y = pageHeight - ((field.y / 100) * pageHeight) - ((field.height / 100) * pageHeight);
    const fieldHeight = (field.height / 100) * pageHeight;

    // Calculate font size to fit field
    const fontSize = Math.min(fieldHeight * 0.7, 12);

    page.drawText(value, {
      x: x + 2,
      y: y + (fieldHeight - fontSize) / 2,
      size: fontSize,
      font,
      color: rgb(0.1, 0.1, 0.12),
    });
  }

  // Flatten form to prevent further editing
  try {
    form.flatten();
  } catch {
    // Form might not have AcroForm fields
  }

  return pdfDoc.save();
}

export async function extractFormFields(pdfBytes: Uint8Array) {
  const pdfDoc = await PDFDocument.load(pdfBytes);
  const form = pdfDoc.getForm();
  const fields = form.getFields();

  return fields.map((field) => ({
    name: field.getName(),
    type: field.constructor.name,
  }));
}

export async function getPDFPageCount(pdfBytes: Uint8Array): Promise<number> {
  const pdfDoc = await PDFDocument.load(pdfBytes);
  return pdfDoc.getPageCount();
}
