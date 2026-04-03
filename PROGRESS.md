# Slate — Development Progress

**Last updated:** 4 April 2026
**Current phase:** Phase 2 (Skills + OCR Integration)
**Status:** Skills wizard working with 3 skills, pdfme + Zerox integrated, needs coordinate calibration and end-to-end testing.

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

**3 Form Filling Skills:**
1. **Contract of Sale Offer (VIC)** — 5 sections, 25+ fields (purchaser, solicitor, payment, conditions, signing)
2. **Section 32 Statement (VIC)** — Draft skeleton, 2 sections
3. **Trust Reconciliation Report** — 5 sections (header, bank account, cash book, ledger balances, sign-off)

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
- Needs GraphicsMagick system dependency

---

## RESUME HERE — Next Steps

### Immediate (Calibration & Testing)
1. **Calibrate pdfme coordinates** — Upload Reconciliation Report PDF, generate, check text placement. Adjust mm values in `pdfmeTemplates.ts`. Repeat for Contract of Sale.
2. **Install GraphicsMagick** — `arch -arm64 brew install graphicsmagick` (for Zerox)
3. **End-to-end test** — /skills → upload PDF → fill wizard → generate → verify output
4. **Test Zerox OCR** — Call `/api/forms/detect-fields` with a PDF

### Short Term
5. **Complete Section 32 skill** — Add remaining sections
6. **Wire Supabase Storage** — Replace in-memory pdfStore with real storage
7. **Run Supabase migration** — Execute SQL schema
8. **Connect Stripe** — Credit purchases

### Medium Term
9. **pdfme Designer UI** — `@pdfme/ui` for visual template creation
10. **Deploy** — Vercel for app (note: Zerox needs self-hosted for GraphicsMagick)
11. **More skills** — Transfer of Land, Power of Attorney, Lease Agreement

---

## Infrastructure Status

| Service | Status | Notes |
|---------|--------|-------|
| **Supabase** | Created | URL + anon key in .env.local. SQL migration needs to be run. |
| **Anthropic (Claude)** | Configured | Used by skills wizard, Zerox OCR, and form_filling_app |
| **pdfme** | Installed | @pdfme/generator + common + schemas. Coordinates need calibration. |
| **Zerox** | Installed | Needs `brew install graphicsmagick`. Uses Anthropic via customModelFunction. |
| **form_filling_app** | Installed | FastAPI backend. Needs `ANTHROPIC_API_KEY` to run. |
| **Skyvern** | Installed | Needs Docker Desktop + API key. |
| **Stripe** | Not configured | Need account + keys |

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
│                                    # section-32-offer.ts, reconciliation-report.ts
├── stores/skillStore.ts             # Zustand wizard session
└── types/skill.ts                   # SkillDefinition, PdfmeFieldMapping
```

---

*To resume development, start from "RESUME HERE" above.*
