# Directive: Spec Site Pipeline (Agent Teams)

## Overview

Automated pipeline that takes ranked HVAC leads and, for each one, builds a custom spec website + personalized outreach email + Gmail draft — entirely autonomously using **Claude Code Agent Teams** with 4 specialist teammates per lead.

**Who it's for:** Ted (TedCA) — selling website redesigns to HVAC contractors.

**Architecture:** 4-teammate specialist team per lead — Researcher, Designer, Judge, and Ops. Each teammate focuses on their specialty. The Judge ensures honest quality evaluation. One team per lead, finish before moving to the next.

---

## Setup

### Prerequisites

| Requirement | Check Command | Fix If Missing |
|-------------|---------------|----------------|
| Playwright Chromium | `python3 -c "from playwright.sync_api import sync_playwright; print('OK')"` | `pip install playwright && python3 -m playwright install chromium` |
| Gmail OAuth token | `ls gmail_token.json` | Run `python3 execution/create_gmail_draft.py --to test@test.com --subject test --html "<p>test</p>"` to trigger OAuth flow |
| OpenRouter API key | `grep OPENROUTER_API_KEY .env` | Add `OPENROUTER_API_KEY=sk-or-...` to `.env` (optional — fallback template works without it) |
| Pillow | `python3 -c "from PIL import Image; print('OK')"` | `pip install Pillow` |
| Netlify token | `grep NETLIFY_AUTH_TOKEN .env` | Add `NETLIFY_AUTH_TOKEN=...` and `NETLIFY_SITE_ID=...` to `.env` |
| tmux | `which tmux` | `brew install tmux` |
| Agent Teams enabled | Check `~/.claude/settings.json` | Must have `"env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}` and `"teammateMode": "tmux"` |

### How to Run

Start Claude Code in tmux, then say:

> "Read the next unprocessed HOT lead from `.tmp/hvac_ranked_20260215_214015.json` (check `.tmp/processed_leads.json` to skip already-done leads). Follow `directives/spec_site_pipeline.md`. Create an agent team with 4 teammates: Researcher, Designer, Judge, and Ops. Use delegate mode. Assign palette #{next index} and hero style from the rotation table."

Press **Shift+Tab** for delegate mode (lead only coordinates).

### tmux Layout (5 panes)

```
┌──────────────────────┬──────────────────────┐
│                      │                      │
│    LEAD (coord)      │   RESEARCHER         │
│    Assigns tasks     │   Scraping website   │
│    Monitors progress │   Pulling reviews    │
│    Moves to next     │   Running analysis   │
│                      │                      │
├──────────────────────┼──────────────────────┤
│                      │                      │
│    DESIGNER          │   JUDGE              │
│    Building HTML     │   Evaluating site    │
│    Fixing issues     │   Sending feedback   │
│    from Judge        │   to Designer        │
│                      │                      │
├──────────────────────┴──────────────────────┤
│                                             │
│    OPS (Email + Deploy + Sheet)             │
│    Generating email, deploying, drafting    │
│                                             │
└─────────────────────────────────────────────┘
```

---

## Inputs

| Input | Source | Description |
|-------|--------|-------------|
| Ranked leads JSON | `.tmp/hvac_ranked_*.json` | Output of `qualify_and_rank_leads.py` — array of lead objects with `lead_score`, `lead_tier`, etc. |
| Lead filter | User specifies | Which leads to process: by tier (`hot`, `warm`), by count (top N), or by name |
| Output directory | `.tmp/{slug}/` | Per-lead working directory. Slug = lowercase hyphenated company name |
| Processed leads | `.tmp/processed_leads.json` | Auto-maintained by `track_lead_status.py` — skip already-done leads |

### Lead Object Shape

```json
{
  "first_name": "Clint",
  "last_name": "Little",
  "email": "clittle13@gmail.com",
  "job_title": "Hvac Service Manager",
  "phone": "+1 214-341-9300",
  "company_name": "United Mechanical, Dallas Texas",
  "website": "https://unitedmechanical.com",
  "employee_count": 46,
  "company_description": "Dallas, Texas based mechanical contractor...",
  "city": "Dallas",
  "state": "Texas",
  "is_qualified_hvac": "yes",
  "lead_score": 87,
  "lead_tier": "hot"
}
```

---

## Tools / Scripts Reference

| Script | Purpose | Key Args | Cost |
|--------|---------|----------|------|
| `execution/scrape_website_content.py` | Scrape company website via Playwright | `--url`, `--max_pages 5`, `--output` | **Free** |
| `execution/scrape_google_reviews.py` | Scrape Google Maps reviews via Playwright | `--business_name`, `--location`, `--max_reviews 10`, `--output` | **Free** |
| `execution/analyze_lead_for_roi.py` | AI analysis of pain points + ROI | `--website_data`, `--reviews_data`, `--company_name`, `--output` | ~$0.01 |
| `execution/combine_research.py` | Merge all data → research.json | `--lead_json '{...}'`, `--website`, `--reviews`, `--analysis`, `--output` | **Free** |
| `execution/screenshot_website.py` | Playwright screenshot (or placeholder) | `--url`, `--output`, `--compress` | **Free** |
| `execution/generate_outreach_email.py` | Generate personalized HTML email | `--company_data`, `--old_screenshot`, `--new_screenshot`, `--output_dir` | ~$0.005 |
| `execution/create_gmail_draft.py` | Create Gmail draft with inline CID images | `--to`, `--subject`, `--html_file`, `--attach path:cid` | **Free** |
| `execution/deploy_spec_site.py` | Deploy to Netlify | `--html`, `--slug`, `--output` | **Free** |
| `execution/track_lead_status.py` | Dedup + status tracking | `--slug`, `--status`, `--check`, `--list` | **Free** |
| `execution/generate_followup_email.py` | Follow-up emails (Day 3/7/14) | `--research`, `--touchpoint 2|3|4`, `--spec_url`, `--output_dir` | **Free** |
| `execution/update_sheet.py` | Update Google Sheet | JSON file + `--sheet_name` | **Free** |

---

## The 4 Teammates

### Teammate 1: RESEARCHER

**Focus**: Gather all intel about the lead's company

**Tasks:**
1. Scrape company website using `execution/scrape_website_content.py` (Playwright, free)
2. Scrape Google reviews using `execution/scrape_google_reviews.py` (Playwright, free)
3. Run AI analysis using `execution/analyze_lead_for_roi.py`
   - If API fails (401/403), generate analysis directly — read website + review data, identify pain points, suggest opportunities, estimate ROI, write icebreaker
4. Combine all data into research.json using `execution/combine_research.py`
5. Screenshot old website using `execution/screenshot_website.py --compress`

**Idempotency**: Before each step, check if the output file already exists. Skip if done.

**Communication:**
- → Messages **Designer**: "Research complete. Key findings: {services}, {pain points}, {review highlights}. research.json and old-site.png ready at .tmp/{slug}/"
- → Messages **Judge**: "Research ready for reference when evaluating the site"
- → Messages **Ops**: "Lead email: {email}, company: {company_name}, research ready"

**Dead websites:** Common for HOT leads. If website scrape returns 0 pages, use `company_description` from lead data as fallback. The placeholder screenshot is a selling point — "before: site down, after: professional site."

### Teammate 2: DESIGNER

**Focus**: Build the spec site using the `/frontend-design` skill

**Tasks:**
1. Read research.json to understand the company
2. **Invoke the `/frontend-design` skill** to build a professional single-page HTML spec site
   - Pass all company data (services, reviews, phone, address, etc.)
   - Use the assigned palette and hero style (see Palette Rotation below)
   - Real company data, reviews, services — no placeholders
   - Self-contained HTML (inline CSS, Google Fonts only)
   - Mobile-responsive with working hamburger menu (include JS toggle!)
   - Save to `.tmp/{slug}/index.html`
3. Receive feedback from Judge → make targeted fixes → resubmit
4. Repeat until Judge approves (max 3 rounds)

**Critical rules for the spec site:**
1. All content must be customer-facing — write for the facility manager, not Ted
2. Phone number in header, hero, emergency CTA, and footer
3. Real reviews verbatim — don't fabricate or over-paraphrase
4. Self-contained HTML — one file, inline CSS, Google Fonts only
5. Mobile hamburger menu must have working JavaScript toggle
6. **NO scroll-reveal animations** (opacity:0 + IntersectionObserver) — they break screenshots. Use CSS page-load animations only, or skip animations entirely.

**Communication:**
- ← Receives research from **Researcher**
- → Messages **Judge**: "Site ready for review at .tmp/{slug}/index.html"
- ← Receives feedback from **Judge**: "Score 58/100. Issues: {list}"
- → Messages **Judge**: "Fixed all issues, please re-evaluate"

### Teammate 3: JUDGE

**Focus**: Independent quality gatekeeper — evaluates EVERYTHING before it goes out

#### Phase A — Spec Site Evaluation

Wait for Designer to submit the spec site, then:

1. **Read the HTML source** — check structure, typography, scripts, responsiveness
2. **Take a screenshot** using `execution/screenshot_website.py` — visually inspect
3. **Cross-reference** with research.json to verify data accuracy

**Score against 10 quality criteria (1-10 each, 100 max):**

| Category | # | Criterion | What to Check |
|----------|---|-----------|---------------|
| **Design & Visual (40pts)** | 1 | Professional Authority (10) | Looks like a real contractor's site, not a template? |
| | 2 | Design Quality (10) | Polished, distinctive, correct palette used, not cookie-cutter? |
| | 3 | Typography & Spacing (10) | Fonts readable, consistent sizing, proper spacing, no cramped sections? |
| | 4 | Visual Hierarchy (10) | Clear sections, strong CTAs, logical flow, nothing buried? |
| **Content & Trust (30pts)** | 5 | Content Quality (10) | Real company data throughout, no placeholder/lorem text? |
| | 6 | Trust Signals (10) | Phone visible in header/hero/footer, reviews shown, years in business, Google rating? |
| | 7 | Data Accuracy (10) | Info matches research.json? Correct phone, address, services, reviewer names? |
| **Technical (30pts)** | 8 | Mobile Responsiveness (10) | Clean on mobile viewport? Hamburger menu has working JS toggle? |
| | 9 | Completeness (10) | All required sections: Header, Hero, Trust Bar, Services, About, Reviews, CTA, Footer? |
| | 10 | Functionality (10) | All links work, click-to-call on phone numbers, no broken elements, menu toggles? |

**Pass threshold: 75/100**

- If score < 75: message Designer with **specific issues + how to fix each one**
- If score >= 75: **approve** and take final screenshot
- Max 3 evaluation rounds — if still below 75 after round 3, approve with a note

#### Phase B — Screenshot Verification

1. Take screenshot of new site using `execution/screenshot_website.py --compress`
2. **Visually verify**: Does it show the website correctly? Are all sections visible?
   - Scroll-reveal animations can cause blank sections — if found, flag to Designer: "Remove opacity:0 animations"
3. Take screenshot of old site too (if not already done by Researcher)
4. For dead websites: old-site.png will show a "Website Unavailable" placeholder — this is expected

#### Phase C — Email Evaluation (after Ops generates email)

1. Read the outreach email HTML
2. Verify:
   - Subject line is personalized (not generic)
   - `to` field is a valid email address (not empty or "there")
   - `first_name` is the actual lead's name
   - Email references specific details about the company
   - Before/after screenshots referenced correctly (CID links)
   - Tracking pixel is present
   - Spec site URL is included
   - CTA is clear and compelling
3. If issues → message Ops to fix → re-evaluate
4. If good → **final approval** → message Lead: "All clear"

**Communication:**
- ← Receives research from **Researcher**
- ← Receives "ready for review" from **Designer**
- → Messages **Designer** (reject): "Score 62/100. Fix these: 1) Hamburger menu JS missing 2) Phone not in footer 3) Review #2 wrong name"
- → Messages **Designer** (approve): "Approved at 82/100. Site looks professional."
- ← Receives email from **Ops** for review
- → Messages **Ops** (issue): "Subject line too generic. Use a specific observation about their site."
- → Messages **Ops** (approve): "Email approved. Screenshots correct. Ready to create Gmail draft."
- → Messages **Lead**: "Lead fully approved. Site: {score}/100, email: verified."

### Teammate 4: OPS (Email + Deploy + Sheet)

**Focus**: Package everything and deliver — only after Judge approves each step

**Tasks:**
1. Wait for Judge to approve spec site
2. Deploy spec site using `execution/deploy_spec_site.py` → get live URL
3. Generate outreach email using `execution/generate_outreach_email.py`
   - Include: tracking pixel, spec site live URL, before/after screenshots
   - If API fails, write the email directly using research.json data
4. **Submit email to Judge for review** before creating Gmail draft
5. After Judge approves email:
   - Create Gmail draft using `execution/create_gmail_draft.py`
     - Validate email address before creating draft
     - Attach old-site.png and new-site.png as inline CID images
   - Update lead status using `execution/track_lead_status.py`
   - Generate follow-up email drafts (Day 3, 7, 14) using `execution/generate_followup_email.py`
   - Create Gmail drafts for each follow-up

**Communication:**
- ← Receives research from **Researcher**
- ← Receives site approval from **Judge**
- → Messages **Judge**: "Email ready for review at .tmp/{slug}/outreach-email.html"
- ← Receives email approval (or fixes) from **Judge**
- → Messages **Lead**: "Lead complete. Draft created, site live at {url}, status updated."

---

## Task Flow with Dependencies

```
Lead creates tasks:
  Task 1: "Research {company}" → assigned to Researcher (no blockers)
  Task 2: "Build spec site for {company}" → assigned to Designer (blocked by Task 1)
  Task 3: "Evaluate spec site for {company}" → assigned to Judge (blocked by Task 2)
  Task 4: "Generate email + deploy for {company}" → assigned to Ops (blocked by Task 3)
  Task 5: "Final review email for {company}" → assigned to Judge (blocked by Task 4)

Task 3 may loop back to Designer up to 3 times via messaging.
Task 5 may loop back to Ops if email needs fixes.
```

### Timeline

```
t=0    Researcher starts scraping website + reviews
t=2min Researcher finishes → messages Designer, Judge, Ops → marks Task 1 done
t=2min Task 2 unblocks → Designer invokes /frontend-design skill, builds HTML
t=5min Designer finishes first draft → messages Judge → marks Task 2 done
t=5min Task 3 unblocks → Judge reads HTML + takes screenshot
t=5min Judge evaluates → score 62/100 → messages Designer: "fix these 3 issues"
t=6min Designer fixes → messages Judge: "fixed, re-evaluate"
t=6min Judge re-evaluates → score 82/100 → APPROVED
t=6min Judge takes final screenshots → messages Ops → marks Task 3 done
t=6min Task 4 unblocks → Ops generates email, deploys to Netlify
t=8min Ops finishes email + deploy → messages Judge for email review → marks Task 4 done
t=8min Task 5 unblocks → Judge reviews email
t=8min Judge approves email → Ops creates Gmail draft + follow-ups
t=9min Ops completes → marks Task 5 done → messages Lead
t=9min Lead: "Lead complete. Moving to next..."
```

---

## Design Variety — Palette Rotation (REQUIRED)

Every lead gets a unique palette + hero style. This is **not optional** — cookie-cutter sites kill the pitch.

### Color Palettes

| # | Primary | Accent | Name |
|---|---------|--------|------|
| 0 | `#0B1D3A` Navy | `#D4922A` Amber | Navy/Amber |
| 1 | `#1B4332` Forest | `#D4A22A` Gold | Forest/Gold |
| 2 | `#2D2D2D` Charcoal | `#C0392B` Red | Charcoal/Red |
| 3 | `#1A365D` Deep Blue | `#E07C24` Orange | Blue/Orange |
| 4 | `#0D4F4F` Dark Teal | `#E8B930` Warm Yellow | Teal/Yellow |

### Hero Styles

| # | Style | Description |
|---|-------|-------------|
| 0 | Full-bleed | Gradient background, centered text, bold CTA |
| 1 | Split-layout | Text left, image/graphic right |
| 2 | Gradient-overlay | Background pattern/shape with text overlay |
| 3 | Diagonal-split | Angled sections, dynamic feel |

**Assignment:** Lead # modulo 5 = palette index. Lead # modulo 4 = hero style index. The Lead coordinator includes these in the task description:

> "Build spec site for Magnum Air. Use Palette #2 (Charcoal/Red: primary #2D2D2D, accent #C0392B). Hero style: Gradient-overlay."

---

## Pipeline Steps (Detailed)

### Step 0: Setup

```python
# Slug convention: lowercase, hyphenated company name
# "United Mechanical, Dallas Texas" → "united-mechanical"
slug = company_name.split(",")[0].strip()
slug = re.sub(r"[^a-z0-9]+", "-", slug.lower()).strip("-")
```

```bash
mkdir -p .tmp/{slug}
```

Check deduplication:
```bash
python3 execution/track_lead_status.py --slug {slug} --check
```

### Step 1: Research (Researcher)

#### 1a: Scrape Website Content
```bash
python3 execution/scrape_website_content.py \
  --url "{website_url}" \
  --max_pages 5 \
  --output .tmp/{slug}/website_data.json
```

If site is down: common for HOT leads. Use `company_description` from lead data. Create minimal website_data.json with `pages_scraped: 0`.

#### 1b: Scrape Google Reviews
```bash
python3 execution/scrape_google_reviews.py \
  --business_name "{company_name}" \
  --location "{city}, {state}" \
  --max_reviews 10 \
  --output .tmp/{slug}/reviews_data.json
```

If no reviews found, try with a Google Maps URL:
```bash
python3 execution/scrape_google_reviews.py \
  --url "https://www.google.com/maps/search/{company_name}+{city}+{state}" \
  --max_reviews 10 \
  --output .tmp/{slug}/reviews_data.json
```

#### 1c: AI Analysis
```bash
python3 execution/analyze_lead_for_roi.py \
  --website_data .tmp/{slug}/website_data.json \
  --reviews_data .tmp/{slug}/reviews_data.json \
  --company_name "{company_name}" \
  --output .tmp/{slug}/analysis.json
```

If API fails (returns `needs_manual_analysis: true`): generate the analysis directly from the data.

#### 1d: Combine into research.json
```bash
python3 execution/combine_research.py \
  --lead_json '{full lead JSON object}' \
  --website .tmp/{slug}/website_data.json \
  --reviews .tmp/{slug}/reviews_data.json \
  --analysis .tmp/{slug}/analysis.json \
  --output .tmp/{slug}/research.json
```

#### 1e: Screenshot Old Website
```bash
python3 execution/screenshot_website.py \
  --url "{website_url}" \
  --output .tmp/{slug}/old-site.png \
  --compress
```

### Step 2: Build Spec Website (Designer)

Invoke the `/frontend-design` skill with all company data from research.json. Include:
- Company name, phone, address, services
- Google rating + review count
- Top 3-5 real reviews (verbatim)
- Assigned palette + hero style
- All design requirements listed above

Save to `.tmp/{slug}/index.html`

### Step 3: Evaluate + Fix Loop (Judge ↔ Designer)

Judge reads HTML + takes screenshot + evaluates against 10 criteria.
- Below 75 → messages Designer with specific fixes
- Designer fixes → messages Judge to re-evaluate
- Max 3 rounds → approve with note if still under 75

### Step 4: Deploy + Email (Ops)

#### 4a: Deploy to Netlify
```bash
python3 execution/deploy_spec_site.py \
  --html .tmp/{slug}/index.html \
  --slug {slug} \
  --output .tmp/{slug}/deploy-info.json
```

#### 4b: Screenshot New Site
```bash
python3 execution/screenshot_website.py \
  --url "file://$(pwd)/.tmp/{slug}/index.html" \
  --output .tmp/{slug}/new-site.png \
  --compress
```

#### 4c: Generate Outreach Email
```bash
python3 execution/generate_outreach_email.py \
  --company_data .tmp/{slug}/research.json \
  --old_screenshot .tmp/{slug}/old-site.png \
  --new_screenshot .tmp/{slug}/new-site.png \
  --output_dir .tmp/{slug}/
```

#### 4d: Judge Reviews Email (Step 5)

Judge verifies email before Gmail draft is created.

#### 4e: Create Gmail Draft
```bash
python3 execution/create_gmail_draft.py \
  --to "{lead_email}" \
  --subject "{subject from email-meta.json}" \
  --html_file .tmp/{slug}/outreach-email.html \
  --attach ".tmp/{slug}/old-site.png:old-site-screenshot" \
  --attach ".tmp/{slug}/new-site.png:new-site-screenshot"
```

#### 4f: Generate Follow-up Drafts
```bash
python3 execution/generate_followup_email.py \
  --research .tmp/{slug}/research.json \
  --all \
  --spec_url "{deployed URL from deploy-info.json}" \
  --output_dir .tmp/{slug}/
```

Then create Gmail drafts for each follow-up.

#### 4g: Track Status
```bash
python3 execution/track_lead_status.py \
  --slug {slug} \
  --status completed \
  --url "{deployed URL}" \
  --draft_id "{draft ID from Gmail}"
```

---

## Email Tracking

Outreach emails include a tracking pixel and can use wrapped click links:

- **Open tracking**: `<img src="cid:tracking-pixel" />` — maps to Modal endpoint `/pixel?slug={slug}`
- **Click tracking**: Wrap spec site URLs through Modal `/click?slug={slug}&url={encoded_url}`
- **All activity streams to Slack** in real-time

Modal endpoints:
- `GET https://nick-90891--claude-orchestrator-pixel.modal.run?slug={slug}` — returns 1x1 PNG, logs to Slack
- `GET https://nick-90891--claude-orchestrator-click.modal.run?slug={slug}&url={url}` — redirects to URL, logs to Slack

---

## Follow-up Email Sequence

| Touch | Day | Type | Description |
|-------|-----|------|-------------|
| 1 | 0 | Main pitch | Spec site + before/after screenshots (generate_outreach_email.py) |
| 2 | 3 | Short bump | Spec site link, quick reminder |
| 3 | 7 | Pain point | Research-backed angle about revenue loss |
| 4 | 14 | Break-up | Last chance, archive warning |

All created as Gmail drafts. Ops creates drafts for touches 2-4 after touch 1 draft is created.

---

## Processing Multiple Leads

One team at a time. When all tasks complete for Lead A:
1. Lead cleans up the team
2. Lead reads next unprocessed lead via `track_lead_status.py --next {leads_json}`
3. Lead spawns new 4-teammate team
4. Repeat until all leads done

---

## Cost Estimate (Per Lead)

| Step | Service | Cost |
|------|---------|------|
| Website scrape | Playwright (local) | **Free** |
| Review scrape | Playwright (local) | **Free** |
| AI analysis | Anthropic Haiku | ~$0.01 |
| Email generation | OpenRouter (Haiku) | ~$0.005 |
| Screenshots | Playwright (local) | **Free** |
| Gmail drafts | Gmail API (local) | **Free** |
| Netlify hosting | Free tier | **Free** |
| Tracking pixel | Modal free tier | **Free** |
| Spec site generation | Claude via /frontend-design | **Included in session** |
| **TOTAL per lead** | | **~$0.01 + Claude session cost** |

---

## Deliverables (Per Lead)

```
.tmp/{slug}/
├── website_data.json       # Scraped website content
├── reviews_data.json       # Google reviews + business metadata
├── analysis.json           # AI-generated pain points, ROI, icebreaker
├── research.json           # Combined research (all above merged)
├── old-site.png            # Screenshot of current website (or placeholder)
├── index.html              # The spec site (self-contained HTML)
├── new-site.png            # Screenshot of the spec site
├── deploy-info.json        # Netlify deploy URL + metadata
├── outreach-email.html     # Personalized HTML email with CID refs
├── email-meta.json         # Subject, to, attachment manifest
├── followup-touch2.html    # Day 3 follow-up email
├── followup-touch2-meta.json
├── followup-touch3.html    # Day 7 follow-up email
├── followup-touch3-meta.json
├── followup-touch4.html    # Day 14 follow-up email
└── followup-touch4-meta.json
```

Plus: **Gmail drafts** (main + 3 follow-ups) in Ted's inbox, ready to review and send.

---

## Edge Cases & Lessons Learned

### Website Scraping
- **Site down / redirect loop:** Common for HOT leads. Fall back to `company_description`. The placeholder screenshot is a selling point.
- **Cloudflare / 403:** Playwright with default Chrome UA handles most. Some sites block all crawlers — use `company_description` as fallback.

### Review Scraping
- **No reviews found:** Skip reviews section in spec site, or use "Be Our First Reviewer" CTA.
- **Business name mismatch:** Check that reviews_data.json `business_name` roughly matches the lead's company name.

### AI Analysis
- **API key expired (401):** Script returns `needs_manual_analysis: true`. Researcher generates analysis directly.

### Website Building
- **Hamburger menu JS:** Always verify the mobile menu toggle works.
- **NO scroll-reveal animations:** opacity:0 + IntersectionObserver breaks Playwright screenshots. Use CSS page-load animations only.
- **Cookie-cutter designs:** ALWAYS use the palette rotation. Every lead must look different.

### Email Generation
- **Manual email fallback:** Always populate email-meta.json with real lead email and name. Read back the file to verify `to` is not empty.
- **Email validation:** create_gmail_draft.py now validates email format. Empty or malformed emails are rejected.

### Gmail Draft
- **Token refresh:** Tokens expire after ~1 hour. Auto-refresh works. If refresh fails, re-authenticate via OAuth flow.
- **Attachment size:** Gmail 25MB limit. Use `--compress` on screenshots to keep under limit.

---

## Verification Checklist

After running the pipeline for a lead, verify:

- [ ] `research.json` exists and has `company_name`, `services`, `reviews`, `pain_points`
- [ ] `old-site.png` exists (real screenshot or placeholder)
- [ ] `index.html` exists, is >10KB, contains real phone number
- [ ] `index.html` contains real review quotes (not placeholder text)
- [ ] `index.html` mobile menu works (has JavaScript toggle)
- [ ] Judge score >= 75/100 (or approved with note)
- [ ] `new-site.png` shows full website (no blank sections)
- [ ] `outreach-email.html` exists with CID image refs
- [ ] `email-meta.json` has correct `to` address and `subject`
- [ ] Gmail draft created (script prints draft ID)
- [ ] Spec site deployed to Netlify (URL in deploy-info.json)
- [ ] Follow-up drafts created (touches 2, 3, 4)
- [ ] Lead status updated in `.tmp/processed_leads.json`
- [ ] Palette is unique (not the same as the previous lead)
