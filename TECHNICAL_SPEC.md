# Slate — Technical Specification

**AI-Powered Form Automation Platform**
*Architecture & Development Plan*

---

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT (Browser)                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Next.js  │  │  PDF.js  │  │  Fabric  │  │  Stripe.js    │  │
│  │  React UI │  │  Viewer  │  │  Canvas  │  │  Payments     │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTPS / WebSocket
┌────────────────────────┴────────────────────────────────────────┐
│                     API LAYER (Next.js API Routes)              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  Auth     │  │  Forms   │  │  Credits │  │  Templates    │  │
│  │  Routes   │  │  Routes  │  │  Routes  │  │  Routes       │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                      SERVICE LAYER                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │  PDF      │  │  AI      │  │  Payment │  │  Template     │  │
│  │  Service  │  │  Service │  │  Service │  │  Service      │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
┌────────────────────────┴────────────────────────────────────────┐
│                      DATA LAYER                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌───────────────┐  │
│  │PostgreSQL│  │  Redis   │  │  S3 /    │  │  Claude API   │  │
│  │(Supabase)│  │  Cache   │  │  Storage │  │  (Anthropic)  │  │
│  └──────────┘  └──────────┘  └──────────┘  └───────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

### Frontend
| Technology | Purpose | Why |
|-----------|---------|-----|
| **Next.js 15** (App Router) | Framework | SSR, API routes, file-based routing, React Server Components |
| **TypeScript** | Language | Type safety, better DX, catch errors at compile time |
| **Tailwind CSS v4** | Styling | Rapid UI development, design system consistency |
| **Framer Motion** | Animations | Apple-style fluid transitions and micro-interactions |
| **PDF.js** | PDF rendering | Mozilla's PDF renderer, renders PDFs in canvas/SVG |
| **Fabric.js** | Canvas interaction | Drag-and-drop field overlays on PDF canvas |
| **Zustand** | State management | Lightweight, simple, no boilerplate |
| **React Hook Form** | Form handling | Performant form state management |
| **Lucide Icons** | Iconography | Clean, minimal SVG icon set |

### Backend
| Technology | Purpose | Why |
|-----------|---------|-----|
| **Next.js API Routes** | API server | Co-located with frontend, serverless-ready |
| **Supabase** | Database + Auth | PostgreSQL, auth, realtime, storage — all-in-one |
| **pdf-lib** | PDF manipulation | Fill form fields, flatten PDFs, server-side |
| **Anthropic Claude API** | AI field detection | Best-in-class document understanding |
| **Stripe** | Payments | Credit pack purchases, usage tracking |
| **Redis (Upstash)** | Caching & rate limiting | Session cache, rate limiting, job queues |
| **Vercel** | Hosting | Edge deployment, serverless functions, CDN |
| **AWS S3** | File storage | PDF storage, filled form storage |

### DevOps & Tooling
| Technology | Purpose |
|-----------|---------|
| **GitHub Actions** | CI/CD |
| **Vitest** | Unit testing |
| **Playwright** | E2E testing |
| **ESLint + Prettier** | Code quality |
| **Sentry** | Error monitoring |
| **PostHog** | Product analytics |
| **Resend** | Transactional email |

---

## Project Structure

```
slate/
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── (marketing)/              # Public marketing pages
│   │   │   ├── page.tsx              # Landing page
│   │   │   ├── pricing/page.tsx      # Pricing page
│   │   │   └── about/page.tsx        # About page
│   │   ├── (auth)/                   # Authentication pages
│   │   │   ├── login/page.tsx
│   │   │   ├── signup/page.tsx
│   │   │   └── layout.tsx
│   │   ├── (dashboard)/              # Authenticated app
│   │   │   ├── dashboard/page.tsx    # Main dashboard
│   │   │   ├── fill/page.tsx         # Form filling workspace
│   │   │   ├── fill/[id]/page.tsx    # Active fill session
│   │   │   ├── templates/page.tsx    # Saved templates
│   │   │   ├── profiles/page.tsx     # Data profiles
│   │   │   ├── credits/page.tsx      # Credit balance & purchase
│   │   │   ├── settings/page.tsx     # Account settings
│   │   │   └── layout.tsx            # Dashboard layout with sidebar
│   │   ├── api/                      # API Routes
│   │   │   ├── auth/[...supabase]/route.ts
│   │   │   ├── forms/
│   │   │   │   ├── upload/route.ts   # PDF upload endpoint
│   │   │   │   ├── detect/route.ts   # AI field detection
│   │   │   │   ├── fill/route.ts     # Fill form fields
│   │   │   │   └── [id]/route.ts     # Get/update form
│   │   │   ├── templates/
│   │   │   │   ├── route.ts          # CRUD templates
│   │   │   │   └── [id]/route.ts     # Specific template
│   │   │   ├── profiles/
│   │   │   │   ├── route.ts          # CRUD data profiles
│   │   │   │   └── [id]/route.ts     # Specific profile
│   │   │   ├── credits/
│   │   │   │   ├── balance/route.ts  # Check balance
│   │   │   │   ├── purchase/route.ts # Buy credits (Stripe)
│   │   │   │   └── consume/route.ts  # Deduct credits
│   │   │   └── webhooks/
│   │   │       └── stripe/route.ts   # Stripe webhook handler
│   │   ├── layout.tsx                # Root layout
│   │   └── globals.css               # Global styles + Tailwind
│   ├── components/
│   │   ├── ui/                       # Design system primitives
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── Dropdown.tsx
│   │   │   ├── Toast.tsx
│   │   │   └── Spinner.tsx
│   │   ├── layout/                   # Layout components
│   │   │   ├── Navbar.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── Container.tsx
│   │   ├── pdf/                      # PDF-specific components
│   │   │   ├── PDFViewer.tsx         # PDF.js canvas renderer
│   │   │   ├── PDFUploader.tsx       # Drag-and-drop upload zone
│   │   │   ├── FieldOverlay.tsx      # Draggable field overlay
│   │   │   ├── FieldPanel.tsx        # Side panel with detected fields
│   │   │   └── FillPreview.tsx       # Preview filled form
│   │   ├── forms/                    # Form-filling components
│   │   │   ├── DataMapper.tsx        # Map data to fields
│   │   │   ├── ProfileSelector.tsx   # Select saved data profile
│   │   │   ├── ManualEntry.tsx       # Manual text entry for fields
│   │   │   └── BatchUpload.tsx       # CSV batch upload
│   │   ├── credits/                  # Credit components
│   │   │   ├── CreditBalance.tsx     # Display current balance
│   │   │   ├── CreditPurchase.tsx    # Purchase credit packs
│   │   │   └── UsageHistory.tsx      # Credit usage log
│   │   └── templates/                # Template components
│   │       ├── TemplateCard.tsx
│   │       ├── TemplateGrid.tsx
│   │       └── TemplateSave.tsx
│   ├── lib/                          # Core libraries
│   │   ├── supabase/
│   │   │   ├── client.ts             # Browser Supabase client
│   │   │   ├── server.ts             # Server Supabase client
│   │   │   └── middleware.ts         # Auth middleware
│   │   ├── pdf/
│   │   │   ├── parser.ts             # Parse PDF structure
│   │   │   ├── filler.ts             # Fill PDF fields with pdf-lib
│   │   │   ├── renderer.ts           # Render PDF pages to images
│   │   │   └── detector.ts           # Detect form field coordinates
│   │   ├── ai/
│   │   │   ├── client.ts             # Anthropic API client
│   │   │   ├── fieldDetection.ts     # AI field detection pipeline
│   │   │   ├── autoFill.ts           # AI auto-fill logic
│   │   │   └── prompts.ts            # System prompts for AI
│   │   ├── stripe/
│   │   │   ├── client.ts             # Stripe client
│   │   │   ├── products.ts           # Credit pack definitions
│   │   │   └── webhooks.ts           # Webhook handlers
│   │   ├── storage/
│   │   │   └── s3.ts                 # S3 upload/download
│   │   └── utils/
│   │       ├── credits.ts            # Credit calculation helpers
│   │       ├── validation.ts         # Input validation schemas (Zod)
│   │       └── errors.ts             # Error handling utilities
│   ├── hooks/                        # React hooks
│   │   ├── useCredits.ts             # Credit balance hook
│   │   ├── usePDF.ts                 # PDF loading/rendering hook
│   │   ├── useTemplate.ts            # Template CRUD hook
│   │   ├── useProfile.ts             # Data profile hook
│   │   └── useFieldDetection.ts      # AI field detection hook
│   ├── stores/                       # Zustand stores
│   │   ├── formStore.ts              # Active form session state
│   │   ├── creditStore.ts            # Credit balance state
│   │   └── uiStore.ts               # UI state (modals, sidebar)
│   └── types/                        # TypeScript types
│       ├── form.ts                   # Form, Field, Mapping types
│       ├── template.ts               # Template types
│       ├── profile.ts                # Data profile types
│       ├── credit.ts                 # Credit, Transaction types
│       └── api.ts                    # API request/response types
├── public/
│   ├── fonts/                        # Inter font files
│   └── images/                       # Static images
├── supabase/
│   └── migrations/                   # Database migrations
│       └── 001_initial_schema.sql
├── tests/
│   ├── unit/                         # Vitest unit tests
│   └── e2e/                          # Playwright E2E tests
├── next.config.ts
├── tailwind.config.ts
├── tsconfig.json
├── package.json
└── .env.example
```

---

## Database Schema

```sql
-- ============================================
-- USERS (managed by Supabase Auth, extended)
-- ============================================
CREATE TABLE public.user_profiles (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name    TEXT,
    company_name    TEXT,
    avatar_url      TEXT,
    credit_balance  INTEGER DEFAULT 5,  -- Start with 5 free credits
    total_forms_filled INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================
-- DATA PROFILES (saved user information)
-- ============================================
CREATE TABLE public.data_profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,           -- "Personal", "Business", "Client - Acme Corp"
    data        JSONB NOT NULL,          -- { "full_name": "John Doe", "address": "123 Main St", ... }
    is_default  BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_data_profiles_user ON public.data_profiles(user_id);

-- ============================================
-- UPLOADED FORMS (original PDFs)
-- ============================================
CREATE TABLE public.forms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    original_name   TEXT NOT NULL,
    storage_path    TEXT NOT NULL,       -- S3 path to original PDF
    file_size       INTEGER NOT NULL,
    page_count      INTEGER NOT NULL,
    detected_fields JSONB,              -- AI-detected field metadata
    status          TEXT DEFAULT 'uploaded' CHECK (status IN ('uploaded', 'detecting', 'ready', 'error')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_forms_user ON public.forms(user_id);

-- ============================================
-- FORM FIELDS (detected or manually added)
-- ============================================
CREATE TABLE public.form_fields (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id     UUID NOT NULL REFERENCES public.forms(id) ON DELETE CASCADE,
    field_name  TEXT NOT NULL,           -- "Full Name", "Address Line 1"
    field_type  TEXT NOT NULL CHECK (field_type IN ('text', 'checkbox', 'radio', 'date', 'signature', 'dropdown')),
    page_number INTEGER NOT NULL,
    x           FLOAT NOT NULL,         -- X coordinate on page
    y           FLOAT NOT NULL,         -- Y coordinate on page
    width       FLOAT NOT NULL,
    height      FLOAT NOT NULL,
    is_required BOOLEAN DEFAULT FALSE,
    ai_detected BOOLEAN DEFAULT FALSE,  -- Was this detected by AI?
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_form_fields_form ON public.form_fields(form_id);

-- ============================================
-- TEMPLATES (saved form + field mappings)
-- ============================================
CREATE TABLE public.templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    form_id         UUID NOT NULL REFERENCES public.forms(id),
    name            TEXT NOT NULL,
    description     TEXT,
    field_mappings  JSONB NOT NULL,      -- Maps field_id -> profile data key
    is_public       BOOLEAN DEFAULT FALSE, -- Shared in template marketplace
    use_count       INTEGER DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_templates_user ON public.templates(user_id);
CREATE INDEX idx_templates_public ON public.templates(is_public) WHERE is_public = TRUE;

-- ============================================
-- FILL SESSIONS (each time a form is filled)
-- ============================================
CREATE TABLE public.fill_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    form_id         UUID NOT NULL REFERENCES public.forms(id),
    template_id     UUID REFERENCES public.templates(id),
    profile_id      UUID REFERENCES public.data_profiles(id),
    filled_data     JSONB NOT NULL,      -- The actual data filled into fields
    output_path     TEXT,                -- S3 path to filled PDF
    credits_used    INTEGER NOT NULL DEFAULT 1,
    fill_method     TEXT CHECK (fill_method IN ('manual', 'template', 'ai_auto', 'batch', 'recurring', 'api')),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_fill_sessions_user ON public.fill_sessions(user_id);

-- ============================================
-- CREDIT TRANSACTIONS
-- ============================================
CREATE TABLE public.credit_transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    amount          INTEGER NOT NULL,    -- Positive = credit added, Negative = credit used
    balance_after   INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('purchase', 'fill', 'template_create', 'referral', 'bonus', 'refund')),
    description     TEXT,
    stripe_payment_id TEXT,              -- For purchases
    fill_session_id UUID REFERENCES public.fill_sessions(id), -- For fills
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_credit_transactions_user ON public.credit_transactions(user_id);

-- ============================================
-- RECURRING FILLS
-- ============================================
CREATE TABLE public.recurring_fills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    template_id     UUID NOT NULL REFERENCES public.templates(id),
    profile_id      UUID NOT NULL REFERENCES public.data_profiles(id),
    schedule        TEXT NOT NULL,       -- Cron expression: "0 9 1 * *" (monthly)
    is_active       BOOLEAN DEFAULT TRUE,
    next_run_at     TIMESTAMPTZ NOT NULL,
    last_run_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_recurring_fills_next ON public.recurring_fills(next_run_at) WHERE is_active = TRUE;
```

---

## API Design

### Authentication
All authenticated endpoints require a Bearer token via Supabase Auth.

```
Authorization: Bearer <supabase_access_token>
```

### Endpoints

#### Forms

```
POST   /api/forms/upload          Upload a PDF
POST   /api/forms/detect          Run AI field detection on uploaded PDF
POST   /api/forms/fill            Fill a form and generate output PDF
GET    /api/forms/:id             Get form details and detected fields
DELETE /api/forms/:id             Delete an uploaded form
```

#### Templates

```
GET    /api/templates             List user's templates
POST   /api/templates             Create a new template
GET    /api/templates/:id         Get template details
PUT    /api/templates/:id         Update a template
DELETE /api/templates/:id         Delete a template
GET    /api/templates/public      Browse public template marketplace
```

#### Data Profiles

```
GET    /api/profiles              List user's data profiles
POST   /api/profiles              Create a new profile
GET    /api/profiles/:id          Get profile details
PUT    /api/profiles/:id          Update a profile
DELETE /api/profiles/:id          Delete a profile
```

#### Credits

```
GET    /api/credits/balance       Get current credit balance
POST   /api/credits/purchase      Create Stripe checkout for credit pack
GET    /api/credits/history       Get transaction history
POST   /api/credits/consume       Deduct credits (internal use)
```

#### Webhooks

```
POST   /api/webhooks/stripe       Handle Stripe payment events
```

### API Response Format

```typescript
// Success
{
  "success": true,
  "data": { ... }
}

// Error
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_CREDITS",
    "message": "You need 2 credits for AI auto-fill. Current balance: 1."
  }
}
```

---

## AI Pipeline: Field Detection

### How It Works

```
1. User uploads PDF
2. Server extracts PDF as images (one per page) using pdf-lib
3. Images sent to Claude API with structured prompt
4. Claude returns detected field coordinates, names, and types
5. Fields stored in database and rendered as overlays on PDF viewer
6. User can adjust/add/remove fields manually
```

### Claude API Prompt Strategy

```typescript
const FIELD_DETECTION_PROMPT = `
Analyze this PDF form image and identify all fillable fields.

For each field, return:
- name: Human-readable field name (e.g., "Full Name", "Date of Birth")
- type: One of "text", "checkbox", "radio", "date", "signature", "dropdown"
- page: Page number (1-indexed)
- bounds: { x, y, width, height } as percentages of page dimensions
- required: Whether the field appears to be required
- hint: Any placeholder text or helper text visible

Return as a JSON array. Be thorough — identify every single fillable area,
including blank lines intended for writing.
`;
```

### Auto-Fill Intelligence

```typescript
const AUTO_FILL_PROMPT = `
Given the following form fields and the user's data profile,
map each field to the most appropriate data value.

Form fields: ${JSON.stringify(fields)}
User profile: ${JSON.stringify(profile)}

For each field, return the field_id and the value to fill.
If a field cannot be confidently mapped, return null for its value.
Explain your mapping reasoning briefly.
`;
```

---

## Frontend Architecture

### Design System Tokens

```css
/* Apple-inspired design tokens */
:root {
  /* Colors */
  --color-primary: #1D1D1F;        /* Slate black */
  --color-accent: #5856D6;         /* Electric indigo */
  --color-accent-hover: #4A48C4;
  --color-surface: #FFFFFF;
  --color-surface-secondary: #F5F5F7;
  --color-surface-elevated: #FFFFFF;
  --color-border: #E5E5EA;
  --color-text-primary: #1D1D1F;
  --color-text-secondary: #86868B;
  --color-text-tertiary: #AEAEB2;
  --color-success: #34C759;
  --color-warning: #FF9F0A;
  --color-error: #FF3B30;

  /* Typography */
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'SF Mono', 'Fira Code', monospace;

  /* Spacing (8px grid) */
  --space-1: 0.25rem;   /* 4px */
  --space-2: 0.5rem;    /* 8px */
  --space-3: 0.75rem;   /* 12px */
  --space-4: 1rem;      /* 16px */
  --space-6: 1.5rem;    /* 24px */
  --space-8: 2rem;      /* 32px */
  --space-12: 3rem;     /* 48px */
  --space-16: 4rem;     /* 64px */
  --space-24: 6rem;     /* 96px */

  /* Radius */
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --radius-xl: 24px;
  --radius-full: 9999px;

  /* Shadows */
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --shadow-md: 0 4px 12px rgba(0,0,0,0.06);
  --shadow-lg: 0 12px 40px rgba(0,0,0,0.08);
  --shadow-xl: 0 24px 80px rgba(0,0,0,0.12);

  /* Transitions */
  --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-base: 250ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-slow: 350ms cubic-bezier(0.4, 0, 0.2, 1);
  --transition-spring: 500ms cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
```

### Key UI Components

#### PDF Workspace (Core Feature)
```
┌─────────────────────────────────────────────────────────┐
│  ← Back to Dashboard          Slate        Credits: 47  │
├──────────────────────┬──────────────────────────────────┤
│                      │                                  │
│   FIELD PANEL        │        PDF VIEWER                │
│                      │                                  │
│   ┌──────────────┐   │   ┌──────────────────────────┐  │
│   │ 📋 Full Name │   │   │                          │  │
│   │   drag me     │   │   │    [PDF Page Rendered]   │  │
│   └──────────────┘   │   │                          │  │
│   ┌──────────────┐   │   │    ┌─────────────────┐   │  │
│   │ 📋 Address   │   │   │    │ Detected Field  │   │  │
│   │   drag me     │   │   │    │ (blue overlay)  │   │  │
│   └──────────────┘   │   │    └─────────────────┘   │  │
│   ┌──────────────┐   │   │                          │  │
│   │ 📋 Date      │   │   │                          │  │
│   │   drag me     │   │   └──────────────────────────┘  │
│   └──────────────┘   │                                  │
│                      │   Page 1 of 3   ◀  ▶             │
│   + Add Field        │                                  │
│                      │──────────────────────────────────│
│   ─────────────────  │                                  │
│   DATA PROFILE       │   ┌──────────────────────────┐  │
│   ┌──────────────┐   │   │  [Fill Form]  [Save as   │  │
│   │ ▾ Personal   │   │   │               Template]  │  │
│   └──────────────┘   │   └──────────────────────────┘  │
│                      │                                  │
├──────────────────────┴──────────────────────────────────┤
│  AI Auto-Fill: 2 credits │ Manual Fill: 1 credit        │
└─────────────────────────────────────────────────────────┘
```

### Core User Flows

#### Flow 1: First-Time Form Fill
```
Landing Page → Sign Up (email/Google) → Dashboard
→ "Upload PDF" button → Drag & drop PDF
→ AI detects fields (loading animation)
→ PDF Workspace opens with detected fields highlighted
→ User drags data from profile panel onto fields
  OR types data manually into field panel
→ Preview filled form
→ "Fill Form" button (deducts 1-2 credits)
→ Download filled PDF
→ Prompt: "Save as template?" → Yes → Template saved
```

#### Flow 2: Template Reuse
```
Dashboard → Templates tab → Select saved template
→ Choose data profile (or create new)
→ Preview auto-mapped fields
→ Adjust any fields if needed
→ "Fill Form" (1 credit)
→ Download
```

#### Flow 3: Recurring Fill
```
Template detail → "Make Recurring" button
→ Select schedule (weekly/monthly/custom)
→ Select data profile
→ Confirm credit auto-deduction
→ Recurring fill created → runs automatically
→ Filled PDFs available in "History" tab
```

---

## PDF Processing Pipeline

### Upload & Parse
```typescript
async function uploadAndParse(file: File, userId: string) {
  // 1. Validate file (PDF, <25MB, <100 pages)
  validatePDF(file);

  // 2. Upload to S3
  const storagePath = await uploadToS3(file, userId);

  // 3. Parse PDF metadata
  const pdfDoc = await PDFDocument.load(await file.arrayBuffer());
  const pageCount = pdfDoc.getPageCount();

  // 4. Extract existing form fields (AcroForm)
  const existingFields = extractAcroFormFields(pdfDoc);

  // 5. Render pages as images for AI detection
  const pageImages = await renderPagesToImages(pdfDoc);

  // 6. Store in database
  const form = await db.forms.create({
    userId, originalName: file.name, storagePath,
    fileSize: file.size, pageCount, status: 'uploaded'
  });

  return { form, existingFields, pageImages };
}
```

### Fill & Generate
```typescript
async function fillForm(formId: string, fieldValues: Record<string, string>) {
  // 1. Load original PDF
  const pdfDoc = await loadPDFFromS3(formId);

  // 2. Fill AcroForm fields (if they exist)
  fillAcroFormFields(pdfDoc, fieldValues);

  // 3. For non-AcroForm fields, draw text at coordinates
  drawTextOnPages(pdfDoc, fieldValues);

  // 4. Optionally flatten (make non-editable)
  flattenForm(pdfDoc);

  // 5. Save filled PDF
  const filledPdfBytes = await pdfDoc.save();
  const outputPath = await uploadToS3(filledPdfBytes, 'filled');

  return { outputPath, downloadUrl: generateSignedUrl(outputPath) };
}
```

---

## Security Architecture

### Data Protection
- **Encryption at rest:** AES-256 via Supabase/S3
- **Encryption in transit:** TLS 1.3 everywhere
- **PDF retention:** User-configurable, default 30 days, then auto-delete
- **PII handling:** Data profiles encrypted with user-specific keys
- **No training on user data:** Explicit policy — user PDFs never used for AI training

### Authentication & Authorization
- **Supabase Auth** with email/password and OAuth (Google, Microsoft)
- **Row-Level Security (RLS)** on all database tables
- **Rate limiting:** 100 requests/minute per user (Upstash Redis)
- **CSRF protection:** Built into Next.js
- **Content Security Policy:** Strict CSP headers

### Compliance Roadmap
- **Month 3:** SOC 2 Type I audit begins
- **Month 6:** GDPR compliance (data deletion, export, consent)
- **Month 12:** SOC 2 Type II certification
- **Month 18:** HIPAA BAA available (healthcare vertical)

---

## Development Phases

### Phase 1: MVP (Weeks 1-8)
**Goal:** Upload PDF → manually map fields → fill → download

- [x] Project scaffolding (Next.js 15, Supabase, Tailwind v4)
- [x] Authentication (signup, login, OAuth) — Supabase Auth wired up
- [x] Auth middleware — route protection, redirect logic
- [x] Auth callback route — OAuth code exchange
- [x] Sign out functionality
- [x] Landing page — hero, features, pricing, CTA sections
- [x] Basic dashboard — quick actions, credit balance, empty states
- [x] Design system — Button, Input, Card, Badge, Modal components
- [x] Layout system — Navbar, Sidebar, Footer
- [x] Credit system UI — balance display, purchase page, credit packs
- [x] Templates page — UI with search, empty state
- [x] Data profiles page — UI with create modal, field list
- [x] Settings page — profile, data retention, danger zone
- [x] PDF uploader component — drag-and-drop with validation
- [x] API route stubs — forms/upload, forms/detect, forms/fill, credits
- [x] Stripe webhook route (stub)
- [x] Database schema — 8 tables with RLS, auto user profile trigger
- [x] Supabase client setup (browser + server SSR)
- [x] AI pipeline code — field detection + auto-fill via Claude API
- [x] PDF filler service — pdf-lib with AcroForm + coordinate-based
- [x] Zustand stores — form state, credit state, UI state
- [x] TypeScript types — form, template, profile, credit, API
- [ ] **>>> RESUME HERE: Supabase setup** — run SQL migration, test signup/login
- [ ] PDF upload to Supabase Storage (connect upload API to real storage)
- [ ] PDF viewer with PDF.js (render uploaded PDFs in browser)
- [ ] Manual field placement (click on PDF to place field markers)
- [ ] Manual data entry per field (type values into placed fields)
- [ ] PDF filling end-to-end (fill + download working pipeline)
- [ ] Connect credit deduction to real database on form fill

### Phase 2: AI + Templates (Weeks 9-14)
**Goal:** AI detects fields, drag-and-drop mapping, save templates

- [x] AI field detection code written (Claude API vision + prompts)
- [x] AI auto-fill code written (semantic field-to-profile mapping)
- [ ] Connect AI detection to real upload flow (render pages → send to Claude)
- [ ] Drag-and-drop field mapping on PDF canvas (Fabric.js)
- [ ] Data profiles CRUD (connect UI to Supabase)
- [ ] Template creation (save form + field mapping)
- [ ] Template reuse (one-click fill from saved template)
- [ ] Credit purchase with Stripe (real checkout sessions)
- [ ] Stripe webhook handler (credit fulfillment on payment)

### Phase 3: Power Features (Weeks 15-20)
**Goal:** Recurring fills, batch processing, team features

- [ ] Recurring fill scheduling (cron-based auto-fills)
- [ ] Batch fill (CSV upload → fill many forms at once)
- [ ] Team invitations and shared templates
- [ ] Template marketplace (public templates)
- [ ] Usage analytics dashboard
- [ ] Referral system (give 5, get 5 credits)

### Phase 4: Scale & Polish (Weeks 21-26)
**Goal:** Performance, API, mobile responsiveness

- [ ] Public API with API keys
- [ ] API documentation
- [ ] Mobile-responsive workspace
- [ ] Performance optimization (lazy loading, caching)
- [ ] E2E test suite (Playwright)
- [ ] SOC 2 preparation
- [ ] Production monitoring (Sentry, PostHog)
- [ ] Deploy to Vercel

---

## Deployment Architecture

```
                    ┌─────────────┐
                    │   Vercel     │
                    │   CDN/Edge   │
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
       ┌──────┴──────┐   ┌┴──────┐  ┌──┴──────────┐
       │  Next.js     │   │ API   │  │  Static     │
       │  SSR Pages   │   │Routes │  │  Assets     │
       └──────────────┘   └───┬───┘  └─────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
       ┌──────┴──────┐ ┌─────┴─────┐ ┌───────┴──────┐
       │  Supabase    │ │  Upstash  │ │  AWS S3      │
       │  PostgreSQL  │ │  Redis    │ │  PDF Storage  │
       │  + Auth      │ │           │ │              │
       └─────────────┘  └───────────┘ └──────────────┘
```

### Environment Configuration

```env
# .env.example
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=

ANTHROPIC_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=

AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_REGION=

UPSTASH_REDIS_URL=
UPSTASH_REDIS_TOKEN=

NEXT_PUBLIC_APP_URL=https://useslate.com
```

---

## Performance Targets

| Metric | Target |
|--------|--------|
| Landing page load (LCP) | < 1.5s |
| Time to interactive | < 2.5s |
| PDF upload + parse | < 3s (10MB file) |
| AI field detection | < 8s |
| Form fill + download | < 2s |
| Lighthouse score | > 95 |
| API response time (p95) | < 200ms |
| Uptime | 99.9% |

---

*Confidential — GEA Technologies / Slate*
*Version 1.0 — February 2026*
