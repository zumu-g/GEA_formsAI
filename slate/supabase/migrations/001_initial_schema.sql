-- Slate Database Schema
-- Initial migration

-- User profiles (extends Supabase Auth)
CREATE TABLE public.user_profiles (
    id              UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name    TEXT,
    company_name    TEXT,
    avatar_url      TEXT,
    credit_balance  INTEGER DEFAULT 5 NOT NULL,
    total_forms_filled INTEGER DEFAULT 0 NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own profile" ON public.user_profiles FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users can update own profile" ON public.user_profiles FOR UPDATE USING (auth.uid() = id);

-- Data profiles
CREATE TABLE public.data_profiles (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    data        JSONB NOT NULL DEFAULT '{}',
    is_default  BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

ALTER TABLE public.data_profiles ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own profiles" ON public.data_profiles FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_data_profiles_user ON public.data_profiles(user_id);

-- Uploaded forms
CREATE TABLE public.forms (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    original_name   TEXT NOT NULL,
    storage_path    TEXT NOT NULL,
    file_size       INTEGER NOT NULL,
    page_count      INTEGER NOT NULL,
    detected_fields JSONB,
    status          TEXT DEFAULT 'uploaded' NOT NULL CHECK (status IN ('uploaded', 'detecting', 'ready', 'error')),
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

ALTER TABLE public.forms ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own forms" ON public.forms FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_forms_user ON public.forms(user_id);

-- Form fields
CREATE TABLE public.form_fields (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    form_id     UUID NOT NULL REFERENCES public.forms(id) ON DELETE CASCADE,
    field_name  TEXT NOT NULL,
    field_type  TEXT NOT NULL CHECK (field_type IN ('text', 'checkbox', 'radio', 'date', 'signature', 'dropdown')),
    page_number INTEGER NOT NULL,
    x           FLOAT NOT NULL,
    y           FLOAT NOT NULL,
    width       FLOAT NOT NULL,
    height      FLOAT NOT NULL,
    is_required BOOLEAN DEFAULT FALSE,
    ai_detected BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

ALTER TABLE public.form_fields ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own form fields" ON public.form_fields FOR ALL
    USING (EXISTS (SELECT 1 FROM public.forms WHERE forms.id = form_fields.form_id AND forms.user_id = auth.uid()));
CREATE INDEX idx_form_fields_form ON public.form_fields(form_id);

-- Templates
CREATE TABLE public.templates (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    form_id         UUID NOT NULL REFERENCES public.forms(id),
    name            TEXT NOT NULL,
    description     TEXT,
    field_mappings  JSONB NOT NULL DEFAULT '[]',
    is_public       BOOLEAN DEFAULT FALSE,
    use_count       INTEGER DEFAULT 0 NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

ALTER TABLE public.templates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own templates" ON public.templates FOR ALL USING (auth.uid() = user_id);
CREATE POLICY "Anyone can view public templates" ON public.templates FOR SELECT USING (is_public = TRUE);
CREATE INDEX idx_templates_user ON public.templates(user_id);
CREATE INDEX idx_templates_public ON public.templates(is_public) WHERE is_public = TRUE;

-- Fill sessions
CREATE TABLE public.fill_sessions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    form_id         UUID NOT NULL REFERENCES public.forms(id),
    template_id     UUID REFERENCES public.templates(id),
    profile_id      UUID REFERENCES public.data_profiles(id),
    filled_data     JSONB NOT NULL DEFAULT '{}',
    output_path     TEXT,
    credits_used    INTEGER NOT NULL DEFAULT 1,
    fill_method     TEXT CHECK (fill_method IN ('manual', 'template', 'ai_auto', 'batch', 'recurring', 'api')),
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

ALTER TABLE public.fill_sessions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own fill sessions" ON public.fill_sessions FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_fill_sessions_user ON public.fill_sessions(user_id);

-- Credit transactions
CREATE TABLE public.credit_transactions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    amount          INTEGER NOT NULL,
    balance_after   INTEGER NOT NULL,
    transaction_type TEXT NOT NULL CHECK (transaction_type IN ('purchase', 'fill', 'template_create', 'referral', 'bonus', 'refund')),
    description     TEXT,
    stripe_payment_id TEXT,
    fill_session_id UUID REFERENCES public.fill_sessions(id),
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

ALTER TABLE public.credit_transactions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can view own transactions" ON public.credit_transactions FOR SELECT USING (auth.uid() = user_id);
CREATE INDEX idx_credit_transactions_user ON public.credit_transactions(user_id);

-- Recurring fills
CREATE TABLE public.recurring_fills (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    template_id     UUID NOT NULL REFERENCES public.templates(id),
    profile_id      UUID NOT NULL REFERENCES public.data_profiles(id),
    schedule        TEXT NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE,
    next_run_at     TIMESTAMPTZ NOT NULL,
    last_run_at     TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW() NOT NULL
);

ALTER TABLE public.recurring_fills ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users can CRUD own recurring fills" ON public.recurring_fills FOR ALL USING (auth.uid() = user_id);
CREATE INDEX idx_recurring_fills_next ON public.recurring_fills(next_run_at) WHERE is_active = TRUE;

-- Auto-create profile on user signup
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.user_profiles (id, display_name, credit_balance)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name', 5);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
