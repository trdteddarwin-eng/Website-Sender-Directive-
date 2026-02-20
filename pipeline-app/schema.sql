-- TedCA Pipeline Web App — Supabase Schema
-- Run this in the Supabase SQL Editor to initialize all tables.

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. leads
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    slug TEXT UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    phone TEXT,
    company_name TEXT,
    website TEXT,
    city TEXT,
    state TEXT,
    industry TEXT DEFAULT 'HVAC',
    employee_count INT,
    lead_score INT DEFAULT 0,
    lead_tier TEXT DEFAULT 'cold',
    score_breakdown JSONB DEFAULT '{}',
    pipeline_status TEXT DEFAULT 'pending',
    is_qualified BOOLEAN DEFAULT TRUE,
    disqualification_reason TEXT,
    raw_data JSONB DEFAULT '{}',
    imported_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add columns that may be missing on existing tables
ALTER TABLE leads ADD COLUMN IF NOT EXISTS full_name TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS company_description TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS send_step TEXT;

CREATE INDEX IF NOT EXISTS idx_leads_slug ON leads(slug);
CREATE INDEX IF NOT EXISTS idx_leads_tier ON leads(lead_tier);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(pipeline_status);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(lead_score DESC);

-- 2. pipeline_runs
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    status TEXT DEFAULT 'running',
    agents JSONB DEFAULT '{}',
    palette_index INT DEFAULT 0,
    hero_style_index INT DEFAULT 0,
    judge_score INT,
    research_path TEXT,
    html_path TEXT,
    old_screenshot_path TEXT,
    new_screenshot_path TEXT,
    log JSONB DEFAULT '[]',
    started_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_lead ON pipeline_runs(lead_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status ON pipeline_runs(status);

-- 3. spec_sites
CREATE TABLE IF NOT EXISTS spec_sites (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    deploy_url TEXT,
    deploy_id TEXT,
    judge_score INT,
    palette_index INT,
    hero_style TEXT,
    html_path TEXT,
    screenshot_path TEXT,
    deployed_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_spec_sites_lead ON spec_sites(lead_id);

-- 4. emails
CREATE TABLE IF NOT EXISTS emails (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    slug TEXT NOT NULL,
    touchpoint INT DEFAULT 1,
    subject TEXT,
    html_content TEXT,
    html_path TEXT,
    status TEXT DEFAULT 'draft',
    gmail_draft_id TEXT,
    gmail_message_id TEXT,
    gmail_thread_id TEXT,
    tracking_pixel_url TEXT,
    open_count INT DEFAULT 0,
    last_opened_at TIMESTAMPTZ,
    attachments JSONB DEFAULT '[]',
    scheduled_send_date DATE,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_emails_lead ON emails(lead_id);
CREATE INDEX IF NOT EXISTS idx_emails_status ON emails(status);
CREATE INDEX IF NOT EXISTS idx_emails_touchpoint ON emails(touchpoint);

-- 5. email_sequences
CREATE TABLE IF NOT EXISTS email_sequences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    slug TEXT UNIQUE NOT NULL,
    status TEXT DEFAULT 'active',
    current_touchpoint INT DEFAULT 1,
    next_send_date DATE,
    spec_site_url TEXT,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    paused_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    stopped_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_sequences_status ON email_sequences(status);
CREATE INDEX IF NOT EXISTS idx_sequences_next ON email_sequences(next_send_date);

-- 6. replies
CREATE TABLE IF NOT EXISTS replies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE CASCADE,
    email_id UUID REFERENCES emails(id) ON DELETE SET NULL,
    gmail_message_id TEXT,
    gmail_thread_id TEXT,
    from_email TEXT,
    subject TEXT,
    body_preview TEXT,
    body_full TEXT,
    sentiment TEXT DEFAULT 'neutral',
    received_at TIMESTAMPTZ,
    detected_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_replies_lead ON replies(lead_id);

-- 7. activity_log
CREATE TABLE IF NOT EXISTS activity_log (
    id BIGSERIAL PRIMARY KEY,
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    slug TEXT,
    event_type TEXT NOT NULL,
    event_data JSONB DEFAULT '{}',
    agent TEXT,
    message TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_activity_slug ON activity_log(slug);
CREATE INDEX IF NOT EXISTS idx_activity_type ON activity_log(event_type);
CREATE INDEX IF NOT EXISTS idx_activity_created ON activity_log(created_at DESC);

-- 8. auto_replies
CREATE TABLE IF NOT EXISTS auto_replies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    lead_id UUID REFERENCES leads(id) ON DELETE SET NULL,
    slug TEXT,
    account TEXT,
    incoming_uid TEXT UNIQUE,
    incoming_from TEXT,
    incoming_subject TEXT,
    incoming_body_preview TEXT,
    sentiment TEXT DEFAULT 'neutral',
    reply_subject TEXT,
    reply_body TEXT,
    status TEXT DEFAULT 'draft',
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_auto_replies_uid ON auto_replies(incoming_uid);
CREATE INDEX IF NOT EXISTS idx_auto_replies_status ON auto_replies(status);
