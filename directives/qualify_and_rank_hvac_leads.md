# Directive: Qualify & Rank HVAC Leads

## Goal
Filter a sheet of 479 leads down to real local HVAC service companies, enrich them with website + social media data, and rank them hottest-to-coldest based on likelihood to buy your services.

## Services You're Selling
1. **Website redesign** (SEO optimized)
2. **Static image ads** (social media)
3. **Website chatbot**
4. **AI receptionist**

## Inputs
- Google Sheet URL with leads (columns: company_name, job_title, company_description, company_industry, company_employee_count, website, company_linkedin, city, state, country)

## Tool
`execution/qualify_and_rank_leads.py`

## Phases

### Phase 1: Qualify (~$0.10)
Filters leads to real local HVAC service companies.

**Deterministic pre-filter (free):**
- No company name → disqualify
- Employee count >= 500 → disqualify (enterprise)
- Description contains manufacturer/distributor/wholesaler/staffing/software → disqualify

**Claude Haiku batch classification:**
- Batches of 20 leads
- Qualified = local/regional HVAC service company, under 500 employees
- Mechanical contractors that do HVAC work ARE qualified
- Companies doing HVAC + plumbing/electrical ARE qualified

**Output columns:** `is_qualified_hvac`, `disqualification_reason`

### Phase 2: Enrich & Score (~$1.50-2.00)
Only processes qualified leads from Phase 1.

**2a: Website scrape (free)**
- Scrapes each lead's website URL
- Claude Haiku rates website_quality (1-10) and seo_quality (1-10)
- Detects: chatbot presence, online booking, social media links

**2b: LinkedIn company profiles (Bright Data Datasets API)**
- Uses `company_linkedin` URLs from sheet
- Dataset ID: `gd_l1vikfnt1wgvvqz95w`
- Returns: follower count, last post date

**2c: Instagram discovery (free)**
- Extracts Instagram handles from website HTML
- Checks `<a>` tags for instagram.com links

**2d: Instagram profiles (Bright Data Datasets API)**
- Dataset ID: `gd_l1vikfch901nx3by4`
- Returns: follower count, last post date

**2e: Scoring (deterministic, 100 points)**

| Category | Max Points | Signals |
|----------|-----------|---------|
| Website need | 25 | Quality score, SEO score, site down = 25 |
| Social media gap | 20 | No Instagram (8), dead LinkedIn (7), no Facebook (5) |
| Chatbot & booking gap | 15 | No chatbot (10), no booking (5) |
| Decision maker | 15 | Owner/CEO (15), VP/Director (10), Manager (5) |
| Company size | 15 | 5-20 emp (15), 21-50 (12), 51-100 (8) |
| Location | 10 | US (10), Canada (7), UK/AU (4) |

**Tiers:**
- HOT (70-100): Bad website + no social + no chatbot + decision maker + right size
- WARM (40-69): Some signals, good fit but not desperate
- COLD (1-39): Good site + active social, or wrong fit

## Usage

```bash
# Phase 1 only (~$0.10)
python3 execution/qualify_and_rank_leads.py --sheet_url "URL" --phase 1

# Phase 2 only (~$1.50)
python3 execution/qualify_and_rank_leads.py --sheet_url "URL" --phase 2

# Both phases
python3 execution/qualify_and_rank_leads.py --sheet_url "URL" --phase both

# Test on 10 rows
python3 execution/qualify_and_rank_leads.py --sheet_url "URL" --phase both --start_row 2 --end_row 11 --dry_run
```

## Output Columns Added to Sheet

| Column | Phase | Example |
|--------|-------|---------|
| `is_qualified_hvac` | 1 | "yes" |
| `disqualification_reason` | 1 | "Enterprise - too large (94000 employees)" |
| `linkedin_followers` | 2 | "234" |
| `linkedin_last_post` | 2 | "2025-08-15" |
| `instagram_handle` | 2 | "@airservicesunlimited" |
| `instagram_followers` | 2 | "156" |
| `instagram_last_post` | 2 | "2025-11-02" |
| `has_chatbot` | 2 | "no" |
| `has_online_booking` | 2 | "no" |
| `website_quality_notes` | 2 | "Outdated design, no meta tags" |
| `social_media_notes` | 2 | "No Instagram; LI last post: 2025-08" |
| `lead_score` | 2 | "78" |
| `lead_tier` | 2 | "hot" |
| `score_breakdown` | 2 | "website:22, social:18, chatbot:15, role:15, size:15, location:10" |

## Dependencies
- `anthropic`, `gspread`, `google-auth`, `beautifulsoup4`, `requests`, `python-dotenv`
- `ANTHROPIC_API_KEY` or `OPENROUTER_API_KEY` in `.env`
- `BRIGHTDATA_API_TOKEN` in `.env` (for LinkedIn + Instagram datasets)
- `token.json` / `credentials.json` for Google Sheets OAuth

## Cost Estimate
- Phase 1: ~$0.10 (Claude Haiku batch classification)
- Phase 2: ~$1.50-2.00 (website AI analysis + Bright Data datasets)
- Total: ~$1.60-2.10

## Verification Examples
- Johnson Controls (94K employees) → disqualified (enterprise)
- Precise Technical Services (9 emp, HVAC, Spring TX) → qualified, likely HOT
- Air Services Unlimited (23 emp, HVAC, Vidor TX) → qualified, likely HOT
- SSW Advanced Technologies (170 emp, Consumer Goods) → disqualified (non-HVAC)

## Edge Cases & Learnings
- Companies with HVAC + plumbing/electrical should be qualified (common combo)
- Mechanical contractors doing HVAC work = qualified
- Some HVAC companies have very basic websites that return 403/timeout — score these as "website down" (25/25 website points)
- OpenRouter fallback works if ANTHROPIC_API_KEY is not set
- Bright Data dataset results are async — script polls every 10s for up to 5 minutes
