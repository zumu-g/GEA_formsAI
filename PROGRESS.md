# Slate — Development Progress

**Last updated:** 29 April 2026
**Current phase:** Phase 2 (Skills + OCR Integration)
**Status:** Skills wizard working with 4 skills, pdfme + Zerox integrated, 6 open-source tools integrated, needs coordinate calibration and end-to-end testing.

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

**Bug fixes applied after code review:**
- Upload formId mismatch, checkbox values, error state handling
- Blob URL cleanup, sidebar navigation gating, defaultValue initialization
- PDF filler robust checkbox detection

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

### COMPLETED — Tool Integrations (29 Apr 2026)

**6 Open-Source Form Filling Tools Integrated:**
1. **Stagehand** (22k★, MIT) — TypeScript SDK for AI-driven web form automation. Native Next.js integration. Replaces/complements Skyvern. `src/lib/services/stagehandClient.ts`
2. **Playwright MCP** — MCP server enabling Claude to drive a browser directly. `@playwright/mcp` installed.
3. **browser-use** (91k★, MIT) — Python + Playwright AI web form agent. `POST /web-fill` on Python backend.
4. **Docling** (58.7k★, MIT, IBM Research) — Structured PDF extraction with bounding box coordinates. `POST /docling/extract` on Python backend. Directly enables pdfme coordinate calibration.
5. **MarkItDown** (118k★, MIT, Microsoft) — DOCX/XLSX/PPTX/HTML → Markdown for LLM context. `POST /convert` on Python backend.
6. **Unstructured** (14.6k★, Apache 2.0) — Semantic document partitioning. `src/lib/services/unstructuredClient.ts`.

---

## RESUME HERE — Next Steps

### Immediate (Calibration & Testing)
1. **Calibrate pdfme coordinates** — Use `POST /docling/extract` (Python backend) with real PDFs to get actual mm positions, then update `pdfmeTemplates.ts`
2. **End-to-end test** — /skills → upload PDF → fill wizard → generate → verify output
3. **Test Zerox OCR** — Call `/api/forms/detect-fields` with a PDF (GraphicsMagick now installed)

### Short Term
4. **Wire Supabase Storage** — Replace in-memory pdfStore with real storage
5. **Run Supabase migration** — Execute SQL schema
6. **Connect Stripe** — Credit purchases

### Medium Term
7. **pdfme Designer UI** — `@pdfme/ui` for visual template creation
8. **Deploy** — Vercel for app (note: Zerox needs self-hosted for GraphicsMagick)
9. **More skills** — Power of Attorney, Lease Agreement

---

## Infrastructure Status

| Service | Status | Notes |
|---------|--------|-------|
| **Supabase** | Created | URL + anon key in .env.local. SQL migration needs to be run. |
| **Anthropic (Claude)** | Configured | Used by skills wizard, Zerox OCR, and form_filling_app. All models updated to claude-sonnet-4-6. |
| **pdfme** | Installed | @pdfme/generator + common + schemas. Coordinates need calibration. |
| **Zerox** | Installed | GraphicsMagick installed (1.3.46_1). Uses Anthropic via customModelFunction. |
| **form_filling_app** | Installed | FastAPI backend. Needs `ANTHROPIC_API_KEY` to run. |
| **Skyvern** | Installed | Needs Docker Desktop + API key. |
| **Stripe** | Not configured | Need account + keys |
| **Stagehand** | Installed | `@browserbasehq/stagehand` npm. Runs locally via Playwright, no extra keys needed. |
| **browser-use** | Installed | Python venv. `POST /web-fill` endpoint. |
| **Docling** | Installed | Python venv. `POST /docling/extract` endpoint. |
| **MarkItDown** | Installed | Python venv. `POST /convert` endpoint. |
| **GraphicsMagick** | Installed | brew install graphicsmagick (1.3.46_1). Required for Zerox PDF-to-image conversion. |

---

## Key Files

```
slate/src/
├── app/(dashboard)/skills/          # Skills listing + [skillId] execution
├── app/api/forms/detect-fields/     # Zerox OCR field detection
├── app/api/forms/fill/              # Fill API (pdfme + AcroForm paths)
├── components/skills/               # SkillCard, SkillWizard, SkillSectionForm,
│                                    # SkillReview, SkillPdfUpload, VoiceInputButton
├── hooks/useVoiceInput.ts           # Web Speech API
├── lib/
│   ├── ocr/                         # zeroxService.ts, fieldDiscovery.ts
│   ├── pdf/                         # pdfmeGenerator.ts, pdfmeTemplates.ts, filler.ts
│   └── skills/                      # index.ts, utils.ts, vic-contract-of-sale-offer.ts,
│                                    # section-32-offer.ts, reconciliation-report.ts,
│                                    # transfer-of-land.ts
├── stores/skillStore.ts             # Zustand wizard session
└── types/skill.ts                   # SkillDefinition, PdfmeFieldMapping
```

---

*To resume development, start from "RESUME HERE" above.*
