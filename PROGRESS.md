# Slate — Development Progress

**Last updated:** 15 May 2026
**Current phase:** Phase 2 (Field Detection + Fill Pipeline)
**Status:** Field detection pipeline extended with pdfplumber + CommonForms. Favourite Fields feature shipped. Design critique complete (16/40 — action plan ready). Next: /harden P0 bugs → /layout restructure → /typeset + /colorize identity pass.

---

## Where We Are

### COMPLETED — Phase 1 (MVP Foundation)
- Next.js 16 + TypeScript + Tailwind v4 + Framer Motion
- Apple-style design system, landing page, dashboard layout
- Auth (Supabase with dev mode bypass), middleware route protection
- PDF upload, AI field detection (Claude vision + PyMuPDF), PDF filler (pdf-lib)
- Streaming fill (SSE), Skyvern web form automation
- In-memory PDF store (bridge until Supabase Storage wired)
- Credit system, Data Profiles CRUD, Templates CRUD
- Zustand state management, TypeScript types for all entities

### COMPLETED — Skills Feature (26 Mar - 4 Apr 2026)

**4 Form Filling Skills:**
1. **Contract of Sale Offer (VIC)** — 5 sections, 25+ fields (purchaser, solicitor, payment, conditions, signing)
2. **Section 32 Statement (VIC)** — 7 sections (complete)
3. **Trust Reconciliation Report** — 5 sections (header, bank account, cash book, ledger balances, sign-off)
4. **Transfer of Land** — VIC transfer of land skill

**Features:**
- Step-by-step wizard UI with section sidebar, progress bar, validation, review
- Voice input via Web Speech API (en-AU), mic button per field
- Auto-fill from user DataProfile on session start
- Computed fields (e.g. balance = price - deposit)
- pdfme coordinate-based PDF generation (text overlay at exact mm positions)
- Zerox OCR + Claude vision for smart field discovery
- Checkbox support in PDF filler (try/catch approach)

### COMPLETED — Library Integration (30 Mar 2026)

**pdfme** (`@pdfme/generator`, `@pdfme/common`, `@pdfme/schemas`):
- Coordinate-based PDF generation — original PDF as background, text overlaid at mm positions
- Works on any PDF (scanned, flattened, no AcroForm needed)
- Fill API supports both pdfme and AcroForm paths
- Templates defined for Contract of Sale + Reconciliation Report

**Zerox** (`zerox`):
- OCR via Claude vision using `customModelFunction` (no new API keys)
- Field discovery: PDF → images → markdown → AI field extraction
- `POST /api/forms/detect-fields` endpoint
- GraphicsMagick installed (brew install graphicsmagick ✓)
- NOTE: `zerox` npm package may not be installed — Step 3 now fails fast with a clear error

### COMPLETED — Tool Integrations (29 Apr 2026)

**6 Open-Source Form Filling Tools Integrated:**
1. **Stagehand** (22k★, MIT) — TypeScript SDK for AI-driven web form automation. Native Next.js integration. `src/lib/services/stagehandClient.ts`
2. **Playwright MCP** — MCP server enabling Claude to drive a browser directly. `@playwright/mcp` installed.
3. **browser-use** (91k★, MIT) — Python + Playwright AI web form agent. `POST /web-fill` on Python backend.
4. **Docling** (58.7k★, MIT, IBM Research) — Structured PDF extraction with bounding box coordinates. `POST /docling/extract` on Python backend. Also now used for **form field detection** (Step 2.5).
5. **MarkItDown** (118k★, MIT, Microsoft) — DOCX/XLSX/PPTX/HTML → Markdown for LLM context. `POST /convert` on Python backend.
6. **Unstructured** (14.6k★, Apache 2.0) — Semantic document partitioning. `src/lib/services/unstructuredClient.ts`.

### COMPLETED — Smart Fill / AI Overlay Feature (May 2026)

- Google Document AI Form Parser integration (`src/lib/services/googleDocumentAI.ts`)
- Smart Fill panel with field overlay viewer (`SmartFillPanel`, `SmartPDFViewer`)
- Draw-to-add field — crosshair mode with AI label detection
- Inline value preview on PDF overlays
- Signature drawing canvas
- AI auto-fill button with inline PDF preview after generation

### COMPLETED — Favourite Fields Feature (14 May 2026)

**Persistent favourites with drag-and-drop across sessions:**
- `slate/src/lib/favouriteFields.ts` — localStorage CRUD (key: `slate_favourite_fields`). Upserts by normalised field name. Functions: `getFavourites`, `saveFavourite`, `removeFavourite`, `isFavourite`
- `slate/src/components/fill/FavouritesPanel.tsx` — collapsible panel above FieldsPanel. Each favourite is native HTML5 draggable (`application/slate-favourite` data type), shows name + type badge + value preview, hover-reveal delete
- `FieldsPanel.tsx` modified — star icon on each field row (outlined/filled gold), drag-over drop zone with dashed purple border highlight
- `fill/[formId]/page.tsx` modified — loads favourites on mount, star toggles save/remove, drop appends field with saved value (skips duplicates)
- No new npm dependencies — uses native HTML5 drag-drop

### COMPLETED — Field Detection Extended + Port Fix (14–15 May 2026)

**Port bug fixed:**
- `detect-smart/route.ts` default URL was `http://localhost:8000` — changed to `http://localhost:8001` to match the running backend. This caused page image loading to silently fail, forcing Vision into raw-PDF single-page fallback mode.

**Two new detection steps added (pipeline is now 7 steps):**

Detection order:
1. AcroForm (PyMuPDF) — instant, digital PDFs
2. **pdfplumber** (NEW) — finds drawn rectangles as form fields in vector PDFs; infers nearby label text. `pip install pdfplumber` ✓
3. **CommonForms v0.2.1** (NEW) — ML object-detection model (ONNX/rfdetr/ultralytics), purpose-built for blank field detection in ANY PDF including scanned. `pip install commonforms` ✓. Python 3.14 compatible.
4. Google Document AI — cloud, not configured
5. Docling — structured layout extraction
6. Zerox OCR — requires graphicsmagick, package not installed
7. Claude Vision — raw PDF or per-page images

**New files:**
- `pdf_processor.py`: `detect_fields_pdfplumber()`, `detect_fields_commonforms()`, `_find_nearby_label()` helper
- `main.py`: `POST /detect-fields-pdfplumber`, `POST /detect-fields-commonforms` endpoints
- `formFillingBackend.ts`: `detectFieldsPdfplumber()`, `detectFieldsCommonForms()` service functions
- `smartFill.ts`: `DetectionMethod` extended with `'pdfplumber' | 'commonforms'`
- `FieldsPanel.tsx`: METHOD_LABELS updated with pdfplumber + CommonForms badges

### COMPLETED — Field Detection Pipeline Repair (12 May 2026)

**Root causes fixed:**
- Fill workspace was calling old `/api/forms/detect` (no AI fallback) → now calls `/detect-smart`
- `pageImagesPromise` race condition in `detect-smart` — page images weren't ready on early exits → fixed with proper `await` before each return
- `zerox` npm package not installed → now fails fast with clear error instead of unhandled rejection
- Python backend default URL in `formFillingBackend.ts` was hardcoded to `:8000`, `.env.local` uses `:8001` → fixed

**Docling field detection (Step 2.5) added:**
- New `detect_fields_from_docling()` in `docling_processor.py` — extracts key-value regions and form-label text blocks with bounding boxes
- New `POST /detect-fields-docling` endpoint on Python backend
- Wired into `detect-smart` pipeline as Step 2.5

**Detection order is now:**
1. AcroForm (PyMuPDF) — instant, highest confidence
2. Google Document AI — cloud, accurate for form PDFs
3. **Docling** — structured layout extraction, works on flat/scanned PDFs
4. Zerox OCR — markdown-based, requires graphicsmagick
5. Claude Vision — raw PDF document block fallback

**UI improvements:**
- FieldsPanel shows detection method badge (e.g. "✦ Docling", "✦ AcroForm")
- Empty state updated: "Draw fields on the PDF or describe them to the AI"
- `detectionMethod` propagated from detect-smart → fill page → FieldsPanel

---

## RESUME HERE — Next Steps

### Immediate (Design — from critique, 16/40 score)
These are ordered. Do them in sequence:

1. **`/harden` — Fix P0 data-loss bugs**
   - Add confirmation dialog to Reset button (currently destroys session silently)
   - Allow removal of AI-detected fields (currently only `manual: true` fields have × button)
   - Replace raw tool names in chat transcript (`fill_pdf_form` → "Writing to form…", `extract_field_values` → "Reading field values…")

2. **`/layout` — Restructure right column**
   - Current order: FavouritesPanel → FieldsPanel → StreamingFillChat (WRONG)
   - Target order: FieldsPanel (primary) → StreamingFillChat (assistant) → FavouritesPanel (collapsible, default closed when empty)

3. **`/typeset` — Replace Inter**
   - Inter is the single biggest "AI made this" signal. Replace with a type pairing with personality.
   - Design context in `.impeccable.md` at project root (created 14 May)

4. **`/colorize` — Shift palette off Apple HIG**
   - Every neutral in `globals.css` is a verbatim Apple HIG token. Keep `#5856D6` accent.
   - Add subtle hue tint to neutrals to make them Slate's own.

5. **`/polish` — Final pass**
   - `formName` hardcodes `'Uploaded Form'` until detection resolves
   - FavouritesPanel should default to collapsed when `favourites.length === 0`
   - Sparkles icon at 9px is illegible — bump to 11–12px
   - Extract shared `TYPE_COLOURS` constant from FieldsPanel + FavouritesPanel
   - Add user-facing labels for detection method badge (hide "pdfplumber"/"Docling" from non-technical users)

### Next (Infrastructure)
6. **End-to-end test** — upload flat PDF → verify pdfplumber/CommonForms detects fields → AI fill stream completes → download
7. **Wire Supabase Storage** — replace in-memory `pdfStore` (PDFs lost on server restart)
8. **Run Supabase SQL migration** — schema exists, never applied

### Short Term
9. **Connect Stripe** — credit purchases (no keys yet)
10. **Improve PDF viewer** — replace bare `<iframe>` with `react-pdf`/`pdfjs-dist` for zoom, page nav, field highlighting

### Medium Term
11. **Deploy** — Vercel for Next.js (Zerox/GraphicsMagick needs self-hosted — use Vision fallback on Vercel)
12. **More skills** — Power of Attorney, Lease Agreement

---

## Infrastructure Status

| Service | Status | Notes |
|---------|--------|-------|
| **Supabase** | Created | URL + anon key in .env.local. SQL migration needs to be run. |
| **Anthropic (Claude)** | Configured | claude-sonnet-4-6. Used by field detection, fill agent, Zerox. |
| **pdfme** | Installed | @pdfme/generator + common + schemas. Coordinates need calibration. |
| **Zerox** | Broken (npm) | zerox npm package likely not installed. GraphicsMagick installed ✓. Install with: `cd slate && npm install zerox` |
| **form_filling_app** | Running | FastAPI on port 8001. Start: see "Running Locally" below. |
| **Docling** | Active | docling==2.91.0 in Python venv. New /detect-fields-docling endpoint. |
| **Skyvern** | Not running | Needs Docker Desktop + API key. |
| **Stripe** | Not configured | Need account + keys |
| **Stagehand** | Installed | `@browserbasehq/stagehand` npm. Playwright locally. |
| **browser-use** | Installed | Python venv. `POST /web-fill` endpoint. |
| **MarkItDown** | Installed | Python venv. `POST /convert` endpoint. |
| **GraphicsMagick** | Installed | brew install graphicsmagick (1.3.46_1). Required for Zerox. |

---

## Running Locally

**Next.js (port 3000) — use Webpack to avoid Turbopack crash on iCloud path:**
```bash
cd slate && npm run dev -- --webpack
```

**Python backend (port 8001):**
```bash
cd form_filling_app/form-filling-exp/backend
ANTHROPIC_API_KEY=<key> ../.venv/bin/python3.14 -m uvicorn main:app --host 0.0.0.0 --port 8001
```

Note: The venv's `uvicorn` script has a broken shebang (iCloud path rename broke it). Always call `python3.14 -m uvicorn` directly, not `.venv/bin/uvicorn`.

---

## Key Files

```
slate/src/
├── app/(dashboard)/fill/
│   ├── [formId]/page.tsx        # Fill workspace — calls detect-smart on load
│   ├── smart/page.tsx           # Smart Fill with overlay viewer
│   └── history/page.tsx         # Fill history
├── app/api/forms/
│   ├── detect-smart/route.ts    # 5-step detection: AcroForm→DocAI→Docling→Zerox→Vision
│   ├── fill-stream/route.ts     # SSE fill stream → Python backend
│   ├── vision-detect/route.ts   # Standalone Claude Vision detection
│   └── detect/route.ts          # Legacy — use detect-smart instead
├── components/fill/
│   ├── FieldsPanel.tsx           # Field list with detection method badge
│   ├── PDFViewer.tsx
│   ├── SmartFillPanel.tsx
│   ├── SmartPDFViewer.tsx
│   └── StreamingFillChat.tsx
├── lib/
│   ├── ocr/                     # zeroxService.ts, fieldDiscovery.ts
│   ├── pdf/                     # pdfmeGenerator.ts, pdfmeTemplates.ts, filler.ts
│   ├── services/
│   │   ├── formFillingBackend.ts # analyzeForm, detectFieldsDocling, fillAgentStream…
│   │   ├── googleDocumentAI.ts
│   │   └── pdfStore.ts          # In-memory store (replace with Supabase Storage)
│   └── skills/                  # Skill definitions (VIC forms)
├── stores/skillStore.ts
└── types/
    ├── smartFill.ts             # DetectedField, DetectionMethod (acroform|docai|docling|vision|…)
    └── formFillingBackend.ts    # BackendFieldInfo, BackendAnalyzeResponse

form_filling_app/form-filling-exp/backend/
├── main.py                      # FastAPI app — endpoints including /detect-fields-docling
├── docling_processor.py         # detect_fields_from_docling() + pdf_bytes_to_structure()
├── pdf_processor.py             # AcroForm detection + Claude Vision fallback
├── agent.py                     # Claude Agent SDK fill agent
└── sessions_data/               # Persisted session PDFs
```

---

*To resume development, start from "RESUME HERE" above.*
