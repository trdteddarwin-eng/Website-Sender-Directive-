# Cold Email Lead Gen — End-to-End SOP

## Overview
Automated cold email pipeline for TedCA targeting local service businesses (plumbers, HVAC, roofers, landscapers) in the US. Offer: AI/automation services. Goal: scale to 3,000 emails/day across 46 SMTP accounts.

## Pipeline Steps

### Standard Pipeline
```
Scrape leads → Upload to Sheet → Enrich emails → Casualize → Generate icebreakers → Send → Track → Follow up
```

### Enhanced Pipeline (ROI-Focused)
```
Scrape leads → Map to template → Scrape websites → Scrape Google reviews → AI analysis → ROI icebreakers → Send
```

The enhanced pipeline scrapes each lead's website and Google reviews, then uses AI to identify pain points and generate ROI-focused icebreakers based on real problems mentioned in their reviews.

---

## Step 1: Scrape Leads

### Test scrape (25 leads)
```bash
python3 execution/scrape_apify.py \
  --query "Plumber" --location "New York, US" \
  --max_items 25 --no-email-filter --output_prefix test_plumbers
```
Verify 80%+ are real local service businesses before running full scrape.

### Full parallel scrape (3,500+ leads)
```bash
python3 execution/scrape_apify_parallel.py \
  --query "Plumber" --location "United States" \
  --max_items 1000 --strategy regions --no-email-filter

python3 execution/scrape_apify_parallel.py \
  --query "HVAC" --location "United States" \
  --max_items 1000 --strategy regions --no-email-filter

python3 execution/scrape_apify_parallel.py \
  --query "Roofing contractor" --location "United States" \
  --max_items 800 --strategy regions --no-email-filter

python3 execution/scrape_apify_parallel.py \
  --query "Landscaping" --location "United States" \
  --max_items 700 --strategy regions --no-email-filter
```

### Upload to Google Sheet
```bash
python3 execution/update_sheet.py --input .tmp/leads_TIMESTAMP.json --name "TedCA Cold Email Leads"
```
Save the resulting Google Sheet URL — all subsequent steps use it.

---

## Step 2: Enrich Emails

```bash
python3 execution/enrich_emails.py "SHEET_URL"
```

- Auto-selects bulk API for 200+ rows, concurrent for smaller batches
- Writes found emails back to the `email` column
- Expect 40-60% hit rate depending on industry

---

## Step 3: Casualize Names

```bash
python3 execution/casualize_batch.py "SHEET_URL"
```

Creates columns: `casual_first_name`, `casual_company_name`, `casual_city_name`
Used in email template personalization.

---

## Step 4: Generate Icebreakers

```bash
python3 execution/generate_icebreakers.py \
  --sheet_url "SHEET_URL" \
  --industry "local services"
```

- Uses Claude Haiku (cheap, fast)
- Batches of 50, 5 parallel workers
- Writes to `icebreaker` column
- One-line, specific, conversational — no generic compliments

---

## Step 4b: Enhanced ROI Pipeline (Optional)

For higher-quality, ROI-focused outreach, use the enhanced pipeline that scrapes websites and Google reviews, then generates icebreakers based on real pain points.

### Option A: Full Pipeline (Recommended)
```bash
python3 execution/full_enrichment_pipeline.py \
  --sheet_url "SHEET_URL" \
  --max_reviews_per_lead 5 \
  --max_pages_per_site 5 \
  --workers 3 \
  --skip_email_enrichment
```

This orchestrator script:
1. Reads leads from the sheet
2. Scrapes each company's website for services/about info
3. Scrapes Google reviews (2-5 per lead)
4. Uses AI to identify pain points and ROI opportunities
5. Generates ROI-focused icebreakers
6. Updates the sheet with enriched columns

### Option B: Individual Scripts

**Step 1: Map Apify output to template**
```bash
python3 execution/map_to_template.py \
  --input .tmp/leads_*.json \
  --output .tmp/leads_mapped.json \
  --require_email \
  --require_website
```

**Step 2: Scrape website content**
```bash
python3 execution/scrape_website_content.py \
  --url "https://example-hvac.com" \
  --max_pages 5 \
  --output .tmp/website_data.json
```

**Step 3: Scrape Google reviews**
```bash
python3 execution/scrape_google_reviews.py \
  --business_name "ABC HVAC" \
  --location "Austin, TX" \
  --max_reviews 5 \
  --output .tmp/reviews.json
```

**Step 4: AI analysis**
```bash
python3 execution/analyze_lead_for_roi.py \
  --website_data .tmp/website_data.json \
  --reviews_data .tmp/reviews.json \
  --company_name "ABC HVAC" \
  --output .tmp/analysis.json
```

**Step 5: Generate ROI icebreakers (batch)**
```bash
python3 execution/generate_roi_icebreakers.py \
  --sheet_url "SHEET_URL" \
  --workers 5
```

### New Columns Added by Enhanced Pipeline

| Column | Source | Description |
|--------|--------|-------------|
| website_summary | Website scrape | Key info from their site |
| services_offered | Website scrape | List of services |
| review_summary | Review scrape | Top reviews and complaints |
| pain_points | AI analysis | Identified problems (slow response, missed calls, etc.) |
| automation_opportunities | AI analysis | What AI/automation can solve |
| roi_estimate | AI analysis | Money/time they're losing |
| roi_icebreaker | AI analysis | Personalized ROI opener |

### Example Output

**Lead:** Texas Cool Air HVAC, Houston TX

**Reviews found:**
- "Called on Saturday, no one answered until Monday." (3 stars)
- "AC went out, took 2 days to get a tech out." (2 stars)

**AI Analysis:**
```json
{
  "pain_points": ["missed weekend calls", "slow scheduling"],
  "automation_opportunities": ["AI voice agent for 24/7 calls", "automated scheduling"],
  "roi_estimate": "Losing 3-5 emergency jobs/week (~$2,000/week in Texas summer)",
  "roi_icebreaker": "Saw a review about a weekend call going unanswered - in Texas summer, that's a $500 emergency job walking to a competitor. We built an AI that answers every call..."
}
```

### Cost Estimate (Per 100 Leads)

| Step | Service | Cost |
|------|---------|------|
| Lead scraping | Apify (leads-finder) | ~$2.50 |
| Website scraping | Apify (website-content-crawler) | ~$0.50 |
| Review scraping | Apify (google-maps-reviews-scraper) | ~$1.25 |
| AI analysis | Claude Haiku | ~$0.50 |
| ROI icebreakers | Claude Haiku | ~$0.30 |
| **TOTAL** | | **~$5.05** |

---

## Step 5: Send Emails

### Dry run (test template rendering + rotation logic)
```bash
python3 execution/send_cold_emails.py \
  --sheet_url "SHEET_URL" \
  --template_name "free_ai_audit" \
  --accounts_config execution/smtp_accounts.json \
  --step 1 \
  --max_sends 10 \
  --dry_run
```

### Real send — Step 1 (initial email)
```bash
python3 execution/send_cold_emails.py \
  --sheet_url "SHEET_URL" \
  --template_name "free_ai_audit" \
  --accounts_config execution/smtp_accounts.json \
  --step 1 \
  --daily_limit_per_account 50 \
  --delay_range 60-180
```

### Follow-up — Step 2 (3 days after step 1)
```bash
python3 execution/send_cold_emails.py \
  --sheet_url "SHEET_URL" \
  --template_name "free_ai_audit" \
  --accounts_config execution/smtp_accounts.json \
  --step 2 \
  --follow_up_days 3 \
  --delay_range 60-180
```

### Follow-up — Step 3 (7 days after step 1, i.e. 4 days after step 2)
```bash
python3 execution/send_cold_emails.py \
  --sheet_url "SHEET_URL" \
  --template_name "free_ai_audit" \
  --accounts_config execution/smtp_accounts.json \
  --step 3 \
  --follow_up_days 4 \
  --delay_range 60-180
```

---

## Step 6: Monitor

```bash
python3 execution/check_send_status.py \
  --sheet_url "SHEET_URL" \
  --accounts_config execution/smtp_accounts.json
```

Reports:
- Emails sent today per account
- Total sent, bounce rate
- Daily capacity remaining
- Alerts for high bounce rate (>2%) or accounts at limit

---

## Email Templates

Three offer sequences, each with 3 steps:

| Sequence | Offer | Template Name |
|----------|-------|---------------|
| Free AI Audit | Free ops audit showing where AI saves 10+ hrs/week | `free_ai_audit` |
| AI Appointment Demo | Live demo of AI that books jobs on autopilot | `appointment_demo` |
| Revenue Share Pilot | Build for free, pay only when it generates revenue | `revenue_share` |

Templates live in `execution/email_templates/{name}/step_{1,2,3}.txt`

**Format:** First line is `Subject: ...`, rest is body.

**Variables:**
- `{first_name}`, `{company}`, `{city}` — basic lead info
- `{icebreaker}` — standard AI-generated opener
- `{roi_icebreaker}` — ROI-focused opener (from enhanced pipeline)
- `{casual_first_name}`, `{casual_company_name}`, `{casual_city_name}` — casualized names
- `{email}`, `{website}` — contact info

---

## SMTP Accounts Config

File: `execution/smtp_accounts.json`

Structure per account:
```json
{
  "email": "ted@gettedca.com",
  "smtp_host": "smtp.zoho.com",
  "smtp_port": 587,
  "username": "ted@gettedca.com",
  "password": "password-here",
  "display_name": "Ted",
  "daily_limit": 50,
  "provider": "zoho",
  "active": true
}
```

- Google Workspace: `smtp.gmail.com:587` (use app password)
- Zoho Mail Lite: `smtp.zoho.com:587`

---

## Infrastructure Setup (One-Time)

### Domains (15 total)
- Register via Cloudflare or Porkbun (~$10/year, .com only)
- Naming: variations of TedCA brand (`gettedca.com`, `trytedca.com`, `tedcagroup.com`, `withtedca.com`, etc.)
- Forward to main site

### Zoho Mail Lite ($1/user/month)
- 3 mailboxes per domain = 45 total
- Naming: `ted@`, `hello@`, `team@`

### DNS (per domain)
- **MX**: Zoho mail servers
- **SPF**: `v=spf1 include:zoho.com ~all`
- **DKIM**: Generated in Zoho admin panel
- **DMARC**: `v=DMARC1; p=none; rua=mailto:dmarc@yourdomain.com`

### Warmup
- Use EmailWarmup.com (free, unlimited)
- Connect all 45 Zoho + existing Google Workspace
- 2-3 weeks before sending

---

## Ramp-Up Schedule

| Week | Action | Volume |
|------|--------|--------|
| 1 | GWS account only. Zoho accounts warming. | ~50/day |
| 2 | Add 5-10 Zoho accounts at 10/day each | ~100-150/day |
| 3 | Add 20-30 accounts at 25-30/day each | ~500-900/day |
| 4 | Add remaining, ramp to 40-50/day each | ~1,500-2,000/day |
| 5 | Full volume: 46 accounts x 50-65/day | ~2,500-3,000/day |

**Kill switches:** Pause any account if bounce rate >2% or spam complaints appear.

---

## Weekly Lead Pipeline

To sustain 3,000/day, scrape ~3,500 fresh leads per week:
1. Rotate verticals: plumbers, HVAC, roofers, landscapers, electricians, painters
2. Rotate geographic regions to avoid overlap
3. Run full pipeline: scrape → enrich → casualize → icebreakers → send
4. Remove bounced/unsubscribed leads from active sheets

---

## Files Reference

### Core Pipeline
| File | Purpose |
|------|---------|
| `execution/send_cold_emails.py` | Core SMTP sending engine with rotation |
| `execution/send_gmail_api.py` | Gmail API sender (alternative to SMTP) |
| `execution/generate_icebreakers.py` | AI icebreaker generation |
| `execution/check_send_status.py` | Sending progress / account health |
| `execution/smtp_accounts.json` | SMTP credentials for all accounts |
| `execution/email_templates/` | 3 sequences x 3 steps = 9 templates |

### Lead Scraping
| File | Purpose |
|------|---------|
| `execution/scrape_apify.py` | Test scraping |
| `execution/scrape_apify_parallel.py` | Parallel lead scraping |
| `execution/map_to_template.py` | Map Apify output to standard columns |

### Enhanced ROI Pipeline
| File | Purpose |
|------|---------|
| `execution/full_enrichment_pipeline.py` | Full orchestrator (website + reviews + AI) |
| `execution/scrape_website_content.py` | Scrape company websites |
| `execution/scrape_google_reviews.py` | Scrape Google Maps reviews |
| `execution/analyze_lead_for_roi.py` | AI analysis for pain points/ROI |
| `execution/generate_roi_icebreakers.py` | ROI-focused icebreaker generation |

### Data Processing
| File | Purpose |
|------|---------|
| `execution/enrich_emails.py` | Email enrichment (AnyMailFinder) |
| `execution/casualize_batch.py` | Data personalization |
| `execution/update_sheet.py` | Google Sheet upload |
| `execution/read_sheet.py` | Google Sheet read |

---

## Edge Cases & Lessons Learned

- **Zoho SMTP auth**: Use regular password, not app password (unless 2FA enabled)
- **Google Workspace SMTP**: Must use app password (Settings > Security > 2FA > App Passwords)
- **gspread rate limits**: Batch updates in chunks of 1000 max
- **Template rendering**: If a variable is missing, it renders as empty string (no crash)
- **Bounce handling**: Bounced leads are automatically skipped in future sends
- **Daily limit tracking**: Persists across runs via sheet tracking columns — safe to restart

---

## Cost Estimate

| Item | Monthly Cost |
|------|-------------|
| 15 domains (~$10/year each) | ~$13 |
| 40-45 Zoho mailboxes ($1/each) | ~$40-45 |
| EmailWarmup.com | Free |
| Existing Google Workspace | Already paid |
| **Total** | **~$55-60/month** |
