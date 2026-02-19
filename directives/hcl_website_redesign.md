# HCL Mechanical Services — Website Redesign Directive

## Overview

- **Client:** HCL Mechanical Services LLC (Houston, TX)
- **Project:** Full website redesign — commercial/industrial HVAC contractor
- **Tech stack:** Next.js 16 + React 19 + Tailwind v4 + Framer Motion
- **Dev server:** Port 3004
- **Project folder:** `hcl-redesign/`

## Goal

Build a professional, trust-first website for a commercial/industrial HVAC mechanical contractor. The site must convey authority, heritage, and reliability — not a trendy startup or dark-themed agency aesthetic. Every design decision should answer: "Would a facilities director trust this company with a $2M chiller plant?"

## Inputs

- Company data in `hcl-redesign/lib/brand.ts` (services, stats, markets, licenses, team info)
- Existing component files in `hcl-redesign/components/`
- Design tokens defined in `hcl-redesign/app/globals.css`
- Animation variants in `hcl-redesign/lib/animations.ts`

## Design System

| Token            | Value                | Usage                              |
|------------------|----------------------|------------------------------------|
| Primary          | `#0C2340` (deep navy)| Header, footer, section backgrounds|
| Accent           | `#D4922A` (warm amber/gold) | CTAs, highlights, accent bars |
| Surface          | `#F5F6F8` (light gray) | Alternating section backgrounds |
| Background       | `#FFFFFF` (white)    | Default page background            |
| Text             | `#1A1A2E` (dark charcoal) | Body text, headings           |
| Muted            | `#6B7280`            | Secondary text, captions           |

**Fonts:**
- **Outfit** — Display/headings (Google Fonts)
- **DM Sans** — Body text (Google Fonts)

**Theme:** Light professional. NOT dark agency aesthetic. Light backgrounds, high contrast text, navy used sparingly for authority.

**Animations:**
- Subtle `fadeUp` on scroll entry
- Duration: 0.5s
- Y-offset: 20px
- Use Framer Motion `useInView` or `whileInView`
- Stagger children in card grids

## Section Order

The page sections must appear in this exact order:

1. **Header** — Sticky nav, phone number, CTA button
2. **Hero** — Split-screen layout, headline + stat cards
3. **TrustBar** — Animated counters (horizontal metrics strip)
4. **Services** — 2-column horizontal cards
5. **Markets Served** — 2x2 grid with accent bars
6. **Why HCL** — Differentiator cards + heritage story
7. **Reviews** — Real quotes from Indeed/Levelset
8. **Emergency CTA** — Full-width navy band with phone number
9. **FAQ** — Accordion with aria-expanded
10. **Footer** — 4-column grid, licenses, TIPS badge

## Component Files

| Component | File | Key Details |
|-----------|------|-------------|
| Header | `components/Header.tsx` | Sticky nav, mobile hamburger menu, always-visible phone number `(713) 586-8140`, CTA button |
| Hero | `components/Hero.tsx` | Split-screen layout, Houston-focused headline, hero image with stat overlay (projects, response time, emergency) |
| TrustBar | `components/TrustBar.tsx` | Horizontal metrics strip with count-up animation on scroll |
| Services | `components/Services.tsx` | 2-column horizontal card layout — icon on left, text on right. NO line-clamp on descriptions. |
| Markets | `components/Markets.tsx` | 2x2 grid with colored left accent bars. Must look visually distinct from Services. |
| WhyHCL | `components/WhyHCL.tsx` | 4 differentiator cards + heritage story paragraph + licenses list. Heritage story belongs HERE, not in a separate section. |
| Reviews | `components/Reviews.tsx` | Real quotes from Indeed/Levelset, "What People Say" heading |
| EmergencyCTA | `components/EmergencyCTA.tsx` | Full-width background image with navy overlay, "System Down? We Answer Immediately." headline, phone number prominently displayed |
| FAQ | `components/FAQ.tsx` | Accordion pattern, `aria-expanded` attribute for accessibility |
| Footer | `components/Footer.tsx` | Navy background, 4-column layout, geographic service area callout, licenses, TIPS badge |

## Data Files

| File | Purpose |
|------|---------|
| `lib/brand.ts` | All HCL company data: company info, services array, stats/metrics, markets served, differentiators, licenses, FAQ items |
| `lib/animations.ts` | Shared Framer Motion animation variants (`fadeUp`, `staggerContainer`) |
| `app/globals.css` | Tailwind v4 config with `@theme` directive for custom design tokens |
| `app/layout.tsx` | Google Font imports (Outfit + DM Sans), metadata, OG/Twitter meta tags, JSON-LD structured data, root layout wrapper |
| `app/page.tsx` | Main page — imports and renders all sections in the correct order |
| `app/robots.ts` | Generates robots.txt allowing all crawlers, references sitemap |
| `app/sitemap.ts` | Generates XML sitemap with all page sections |
| `public/images/` | Stock photos for Hero, EmergencyCTA, and visual credibility |

## Tools / Scripts

- **Next.js CLI** — `npx next dev -p 3004` (dev), `npx next build` (verify)
- **Playwright / Puppeteer / agent-browser** — Screenshots for deliverables
- **Lucide React** — Icon library for all section icons
- **Framer Motion** — Scroll-triggered animations

## Workflow Steps

### Step 1: Research & Planning

- Analyze competitor HVAC contractor websites (Comfort Systems, Coolsys, Limbach)
- Identify industry design patterns: light themes, trust signals, phone number visibility, service grids
- Define color palette, typography, and section order based on research findings
- Confirm all company data is accurate in `lib/brand.ts`

### Step 2: Design System + Layout

- Update `app/globals.css` with Tailwind v4 `@theme` tokens matching the design system above
- Update `app/layout.tsx` with Outfit + DM Sans font imports and metadata
- Update `lib/brand.ts` with complete, accurate company data
- Update `lib/animations.ts` with `fadeUp` and `staggerContainer` variants
- Set section order in `app/page.tsx`

### Step 3: Build Components (Parallel)

Build or update all 10 components listed in the Component Files table above. Every component must:
- Use the design system tokens (`brand-primary`, `brand-accent`, `brand-surface`, etc.)
- Use Lucide React icons (not FontAwesome, not custom SVGs)
- Use Framer Motion for scroll-triggered `fadeUp` animations
- Be fully responsive (mobile-first)
- Have proper TypeScript types (no `any`)

### Step 4: Build Verification

Run `npx next build` from the `hcl-redesign/` directory. The build **must compile with zero errors**. Fix any TypeScript or build errors before proceeding.

Verify the dev server loads correctly at `http://localhost:3004`.

### Step 5: Judge Agent Review (CRITICAL — RUN EVERY TIME)

After every build, launch a judge agent to review the live website. This step is **mandatory** and must not be skipped.

**Judge Agent Prompt:**

```
You are a senior web design critic specializing in B2B commercial/industrial service company websites. Review the HCL Mechanical Services website at http://localhost:3004.

Evaluate on these criteria (score each 1-10):
1. Professional Authority — Does it look like a $34M mechanical contractor, not a startup or agency?
2. Trust Signals — Are licenses, certifications, heritage, and team size prominently displayed?
3. Phone Visibility — Is (713) 586-8140 visible in header, hero, emergency CTA, and footer?
4. Mobile UX — Does the mobile experience work (hamburger menu, tap-to-call, readable text)?
5. Visual Hierarchy — Is the section flow logical? Do CTAs stand out?
6. Industry Fit — Does it match HVAC industry patterns (light theme, navy+amber, icon cards, service grid)?
7. Content Completeness — Are all required sections present (Services, Markets, Why HCL, Emergency CTA, FAQ)?
8. Differentiation from Templates — Does it avoid generic HVAC template patterns?

Provide:
- Overall score out of 100
- Top 5 issues to fix (ranked by severity)
- Specific code changes recommended for each issue
```

**How to run:** Use the Task tool with an explore or general-purpose agent that can use agent-browser to view the live site and critique it.

**Action on results:**
- If score >= 80: Proceed to Step 6
- If score < 80: Fix the identified issues, rebuild, and re-run the judge agent
- **Never ship a website that scores below 80**

### Step 6: Screenshots

Capture screenshots for deliverables and outreach:

- **Hero screenshot:** `.tmp/hcl-redesign-hero.png` (1440x900 viewport, above the fold)
- **Full page screenshot:** `.tmp/hcl-redesign-full.png` (1440px wide, full scroll height)

Use Playwright, Puppeteer, or agent-browser for screenshots.

### Step 7: Outreach Email Update

Update the outreach email files that accompany the redesign pitch:

- `.tmp/hcl-outreach-email.md` — Plain text version
- `.tmp/hcl-outreach-email.html` — HTML version with embedded screenshot

**Email content should include:**
- What changed in the redesign
- What was added (sections, features, trust signals)
- How it improves lead generation and professional credibility
- Before/after contrast (old site down vs. new professional site)
- Call to action to review the live preview

## Content Rules — Customer-Facing (NOT Pitch Stats)

**Critical:** All website content must be written for the customer (facility managers, building owners, procurement teams) — NOT as a sales pitch to HCL's leadership.

### Stats That DO NOT Belong on the Website
| Bad Stat | Why It's Wrong |
|----------|---------------|
| "$34M+ Annual Revenue" | Customers don't care about your revenue |
| "300+ Union Employees (Humphrey)" | Parent company flex, irrelevant to a facility manager |
| "79+ Team Members" | Vague internal metric, not a customer benefit |

### Stats That DO Belong on the Website
| Good Stat | Why It Works |
|-----------|-------------|
| "2,500+ Projects Completed" | Track record = trust |
| "<4hr Emergency Response" | Speed of response = #1 concern |
| "20+ Years Serving Houston" | Longevity = stability |
| "24/7 Emergency Response" | Availability = reliability |
| "3 Licensed Trades" | Breadth of capability |

### Content Voice Rules
- Write as if a facility director is reading, not a sales prospect
- Lead with customer benefits (uptime, response time, project count), not company vanity metrics
- Heritage story should emphasize "what this means for you" — institutional resources + local responsiveness
- Never reference revenue, internal employee counts, or parent company size as primary selling points
- Certifications and licenses are customer-relevant (they prove compliance) — always include

## SEO Requirements

### Metadata (layout.tsx)
- Open Graph tags: og:title, og:description, og:image, og:url, og:type, og:locale, og:site_name
- Twitter Card tags: twitter:card, twitter:title, twitter:description, twitter:image
- Canonical URL via `metadataBase` + `alternates.canonical`
- Theme color in both metadata and viewport

### Structured Data (JSON-LD in layout.tsx)
- `HVACBusiness` schema (extends LocalBusiness) with name, address, phone, hours, geo, service area
- `FAQPage` schema mirroring the FAQ accordion content
- `Service` schemas for each service offered via `hasOfferCatalog`
- Keep FAQ schema in sync with `components/FAQ.tsx` — if FAQ content changes, update both

### Technical SEO Files
- `app/robots.ts` — MetadataRoute.Robots, allows all crawlers, references sitemap URL
- `app/sitemap.ts` — MetadataRoute.Sitemap with all sections, monthly changeFrequency

### Image SEO
- Every `<Image>` must have descriptive `alt` text including location keywords ("Houston", "Texas Medical Center")
- Hero image uses `priority` for LCP optimization
- All other images use default lazy loading
- Use `next/image` for automatic WebP/AVIF format serving
- Set `sizes` attribute on every image to prevent serving oversized images

### Local SEO Signals
- NAP (Name, Address, Phone) must be consistent across: Header, Hero, Footer, JSON-LD schema
- Service area keywords in content: Houston, San Antonio, Texas Gulf Coast, Texas Medical Center
- Industry-specific keywords in h2/h3 headings and descriptions

## Images

Stock photos in `public/images/` provide visual credibility. Use `next/image` component for all images.

| File | Section | Specs |
|------|---------|-------|
| `hero-commercial.jpg` | Hero (right side) | `fill`, `priority`, `sizes="50vw"` |
| `industrial-pipes.jpg` | EmergencyCTA (background) | `fill`, `lazy`, `aria-hidden="true"` |
| `hvac-rooftop.jpg` | Available for Markets/Services | `lazy` |
| `data-center.jpg` | Available for Markets | `lazy` |
| `healthcare-facility.jpg` | Available for Markets | `lazy` |

**For production:** Replace stock photos with original photography — team photos, actual project sites, branded service vehicles. Budget $1,500-3,000 for a half-day commercial shoot.

## Edge Cases & Lessons Learned

- **Lucide icon typing:** When storing Lucide icons in `iconMap` objects, type them as `React.ComponentType<{ className?: string; style?: React.CSSProperties }>` to avoid TypeScript errors.
- **Tailwind v4 config:** Uses `@theme` directive inside `globals.css`, NOT the legacy `tailwind.config.js` file. Do not create a `tailwind.config.js`.
- **Accessibility zoom:** Do NOT use `maximumScale: 1` in layout metadata viewport config — it breaks pinch-to-zoom accessibility.
- **Accurate stats:** Stats must match actual company data. Example: 3 licenses, not 5. Cross-reference `lib/brand.ts`.
- **Visual distinction:** Services and Markets sections must use visually distinct layouts (horizontal cards vs. grid with accent bars) so the page does not feel repetitive.
- **Heritage story placement:** The heritage/history story belongs inside `WhyHCL.tsx`, not in a separate Stats or About section.
- **No line-clamp on services:** `line-clamp` on service descriptions hides important content. Let descriptions flow to full length.
- **Mobile requirements:** Must have hamburger menu, always-visible phone icon in header, and tap-to-call buttons throughout.
- **Phone number everywhere:** `(713) 586-8140` must appear in: Header, Hero, EmergencyCTA, and Footer. A facilities director should never have to scroll to find the phone number.
- **Customer-facing content only:** Never put pitch stats ($34M revenue, 300+ union employees) on the website. These are for Ted's outreach email, not the customer-facing site.
- **SEO is mandatory:** Every version of the site must include OG tags, JSON-LD structured data, robots.txt, and sitemap.xml. A website that can't be found on Google has no value.
- **Images via next/image:** All images must use the `next/image` component for automatic WebP/AVIF serving, lazy loading, and sizing. Never use raw `<img>` tags.
- **Outreach email length:** Keep the outreach email to 3-4 short paragraphs max. Lead with the customer's problem (dead website), pitch the solution with ROI stats, end with low-pressure CTA.

## Deliverables

1. Working website at `http://localhost:3004` — all 10 sections rendering correctly
2. Zero TypeScript/build errors (`npx next build` passes clean)
3. Judge agent review score >= 80
4. Hero screenshot at `.tmp/hcl-redesign-hero.png` (1440x900)
5. Full-page screenshot at `.tmp/hcl-redesign-full.png` (1440x full scroll)
6. Updated outreach email at `.tmp/hcl-outreach-email.md` (plain text)
7. Updated outreach email at `.tmp/hcl-outreach-email.html` (HTML with screenshot)

## Output

The primary output is a live, professional HVAC contractor website that passes the judge agent review and is ready to present to the client as a redesign proposal. Secondary outputs are the screenshots and outreach email for the sales pitch.
