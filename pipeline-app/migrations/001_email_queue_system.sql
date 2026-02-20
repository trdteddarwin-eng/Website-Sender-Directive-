-- Migration: Email Queue System + Multi-Sender Rotation
-- Run this in Supabase SQL Editor

-- Add sender tracking to emails table
ALTER TABLE emails ADD COLUMN IF NOT EXISTS sender_account text;
ALTER TABLE emails ADD COLUMN IF NOT EXISTS sent_via text DEFAULT 'smtp';
ALTER TABLE emails ADD COLUMN IF NOT EXISTS to_email text;

-- Add sender tracking to email_sequences
ALTER TABLE email_sequences ADD COLUMN IF NOT EXISTS sender_account text;

-- Daily queue table
CREATE TABLE IF NOT EXISTS daily_queue (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_date date NOT NULL DEFAULT CURRENT_DATE,
    lead_id uuid REFERENCES leads(id),
    slug text NOT NULL,
    sender_account text NOT NULL,
    email_id uuid REFERENCES emails(id),
    status text NOT NULL DEFAULT 'queued',  -- queued, approved, sent, skipped, failed
    approved_at timestamptz,
    sent_at timestamptz,
    created_at timestamptz DEFAULT now()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_emails_sent_at ON emails(sent_at);
CREATE INDEX IF NOT EXISTS idx_emails_sender ON emails(sender_account);
CREATE INDEX IF NOT EXISTS idx_emails_status ON emails(status);
CREATE INDEX IF NOT EXISTS idx_daily_queue_date ON daily_queue(queue_date);
CREATE INDEX IF NOT EXISTS idx_daily_queue_status ON daily_queue(status);
