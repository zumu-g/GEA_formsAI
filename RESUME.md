# Slate — Resume Prompt

Copy and paste the following into a new Claude Code session to resume development with full context.

---

## Paste this:

> I'm resuming development on **Slate** — an AI-powered PDF form filler for legal and real estate professionals (conveyancers, solicitors, agents, admin staff). Read `PROGRESS.md` for the full history. Here's the current state:
>
> **What Slate does:** Users upload a PDF form, the app detects fillable fields via a 7-step pipeline, users can review/edit fields and drag in saved favourites, then instruct an AI agent (Claude) to fill the form via streaming. The filled PDF is downloaded.
>
> **Tech stack:**
> - Frontend: Next.js 16, React 19, TypeScript, Tailwind v4, Framer Motion, Lucide icons, Zustand
> - Backend: FastAPI (Python 3.14) on port 8001
> - AI: Claude via Anthropic SDK (`claude-sonnet-4-6`)
> - Storage: Supabase (auth wired; SQL migration NOT yet run; PDFs still in-memory via `pdfStore`)
> - PDF: PyMuPDF (fitz), pdfplumber, CommonForms v0.2.1, pdfme, pdf-lib
>
> **Running locally:**
> ```bash
> # Next.js (port 3000) — use Webpack to avoid Turbopack crash on iCloud path:
> cd slate && npm run dev -- --webpack
>
> # Python backend (port 8001):
> cd form_filling_app/form-filling-exp/backend
> ANTHROPIC_API_KEY=<key> ../.venv/bin/python3.14 -m uvicorn main:app --host 0.0.0.0 --port 8001
> ```
> Note: `.venv/bin/uvicorn` has a broken shebang (iCloud path rename). Always use `python3.14 -m uvicorn`.
>
> **What was completed in the last session (14–15 May 2026):**
>
> 1. **Favourite Fields** — Users can star any field+value during a fill session. Favourites persist in `localStorage` (`slate_favourite_fields`). They appear in a collapsible `FavouritesPanel` above the fields list. Each favourite is draggable (native HTML5) — drag it onto FieldsPanel to add it with the saved value pre-filled. Files: `slate/src/lib/favouriteFields.ts`, `slate/src/components/fill/FavouritesPanel.tsx`, modified `FieldsPanel.tsx` and `fill/[formId]/page.tsx`.
>
> 2. **Field detection extended** — Fixed port bug (detect-smart was calling :8000, backend runs on :8001). Added 2 new detection steps: **pdfplumber** (rect-based, digital PDFs) and **CommonForms** (ML/ONNX, works on scanned PDFs). Both installed in Python venv. Pipeline is now 7 steps: AcroForm → pdfplumber → CommonForms → DocAI → Docling → Zerox → Claude Vision.
>
> 3. **Design critique** — Full `/impeccable:critique` run. Score: **16/40**. Design context saved to `slate/.impeccable.md`. The verdict: every neutral in `globals.css` is a verbatim Apple HIG token; font is Inter; card chrome is identical across every panel; zero visual personality. Technically competent, immediately identifiable as AI-generated.
>
> **What to do next (in order):**
>
> **Priority 1 — `/harden` (two P0 bugs):**
> - Reset button destroys session silently with no confirmation (`fill/[formId]/page.tsx` `handleReset`)
> - AI-detected fields can't be removed (`FieldsPanel.tsx` — `FieldRow` only renders × when `field.manual === true`)
> - Raw tool names in chat (`fill_fields_smart`, `extract_field_values`) need user-friendly labels
>
> **Priority 2 — `/layout` (right column hierarchy is inverted):**
> - Current: FavouritesPanel → FieldsPanel → StreamingFillChat
> - Target: FieldsPanel → StreamingFillChat → FavouritesPanel (collapsed by default when empty)
>
> **Priority 3 — `/typeset` + `/colorize` (design identity):**
> - Replace Inter with a type pairing that has personality
> - Shift neutrals off Apple HIG tokens (keep `#5856D6` accent)
> - Design brief is in `slate/.impeccable.md`
>
> **Priority 4 — `/polish`:**
> - `formName` hardcodes `'Uploaded Form'` in `fill/[formId]/page.tsx`
> - FavouritesPanel should default to collapsed when `favourites.length === 0`
> - `TYPE_COLOURS` is duplicated in `FieldsPanel.tsx` and `FavouritesPanel.tsx` — extract to shared constant
> - Sparkles icon at 9px is illegible in the detection method badge
>
> **Priority 5 — Infrastructure:**
> - Run Supabase SQL migration (schema exists, never applied)
> - Wire Supabase Storage to replace in-memory `pdfStore`
> - End-to-end test with a real flat/scanned PDF
>
> **Key files:**
> ```
> slate/src/
> ├── app/(dashboard)/fill/[formId]/page.tsx     # Fill workspace — main page
> ├── app/api/forms/detect-smart/route.ts        # 7-step detection pipeline
> ├── app/api/forms/fill-stream/route.ts         # SSE fill stream → Python backend
> ├── components/fill/
> │   ├── FieldsPanel.tsx                        # Field list + star + drop zone
> │   ├── FavouritesPanel.tsx                    # Favourites with drag handles
> │   ├── PDFViewer.tsx                          # Bare iframe (TODO: replace with pdfjs)
> │   └── StreamingFillChat.tsx                  # AI instruction chat + SSE events
> ├── lib/
> │   ├── favouriteFields.ts                     # localStorage CRUD for favourites
> │   ├── fillHistory.ts                         # localStorage fill history
> │   ├── services/
> │   │   ├── formFillingBackend.ts              # TypeScript → Python backend calls
> │   │   └── pdfStore.ts                        # In-memory PDF store (replace with Supabase)
> │   └── services/googleDocumentAI.ts
> ├── types/smartFill.ts                         # DetectedField, DetectionMethod, SmartDetectResult
> └── .impeccable.md                             # Design context for impeccable skills
>
> form_filling_app/form-filling-exp/backend/
> ├── main.py                                    # FastAPI — all endpoints
> ├── pdf_processor.py                           # AcroForm, pdfplumber, CommonForms detection
> ├── docling_processor.py                       # Docling detection
> └── agent.py                                   # Claude Agent SDK fill agent
> ```
>
> Start by reading `PROGRESS.md` for full history, then pick up from Priority 1 above.
