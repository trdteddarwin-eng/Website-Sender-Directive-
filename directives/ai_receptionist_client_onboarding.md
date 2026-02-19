# AI Voice Receptionist — Client Onboarding SOP

## Purpose

Step-by-step process for onboarding a new AI voice receptionist client, from discovery through go-live.

## Prerequisites

- Access to Retell AI dashboard
- Twilio account (for phone numbers)
- Pricing calculator: `execution/receptionist_pricing_calculator.py`
- Proposal template: `ai-receptionist-service/proposal_template.md`
- Discovery questionnaire (see Phase 1 below)

---

## Phase 1: Discovery Call

### Objective
Understand the client's needs, call volume, and technical requirements to scope and price correctly.

### Instructions
Run through ALL discovery questions below. Group them naturally in conversation — don't read like a checklist. Take notes.

### A. Business Basics
1. What type of practice? (General dentist, specialist, medical clinic, multi-doctor, etc.)
2. How many locations? (Each location may need its own phone number)
3. How many doctors/providers? (Affects scheduling complexity)
4. Business hours? (e.g., Mon-Fri 8am-5pm, Sat mornings, etc.)
5. Do you need after-hours coverage? (AI answers 24/7, or only during business hours?)

### B. Call Volume & Direction
6. How many calls do you get per day? (Even a rough estimate)
7. How many go unanswered or to voicemail? (This is the pain point — helps you sell)
8. Mostly inbound or also outbound? (Inbound = booking, questions. Outbound = reminders, confirmations)
9. Average call length? (Most receptionist calls are 1-3 minutes. KEY for pricing)
10. Seasonal spikes? (Back-to-school, holidays, etc.)

### C. What the Receptionist Needs to Do
11. Top 5 reasons people call?
12. Appointment booking needed? If yes:
    - What scheduling system? (Dentrix, Open Dental, custom, paper)
    - Should AI book directly or just collect info for manual booking?
13. Call routing/transfers needed? (Menu-based or AI-determined)
14. Handle insurance questions? (Requires knowledge base with accepted plans)
15. Take messages and send to staff? (Via email, SMS, or app notification)
16. Emergency call handling? (Route emergencies to on-call doctor)

### D. Language & Tone
17. Percentage of calls in Spanish vs English?
18. Auto-detect language or ask the caller?
19. Desired tone? (Formal/professional, warm/friendly, etc.)
20. Specific greeting? (e.g., "Buenos días, Clínica Dental Sonrisa, ¿en qué le puedo ayudar?")

### E. Technical & Integration
21. Current phone system? (Landline, VoIP, cell phone, existing PBX)
22. Keep current phone number? (Number porting may be needed)
23. Fallback when AI can't handle? (Transfer to human, take message, etc.)
24. SMS follow-ups needed? (Text confirmation after booking)
25. Software integrations? (CRM, EHR, Google Calendar, WhatsApp, etc.)

### F. Compliance & Data
26. Handle patient health information on calls? (Privacy regulations)
27. Must inform callers they're speaking to AI? (Check local regulations)
28. Need call recordings? (Quality assurance, training, disputes)

### Output
Save discovery notes to `.tmp/discovery_notes_[client_name].md`

---

## Phase 2: Pricing

### Objective
Calculate your costs and determine client pricing.

### Steps
1. Run the pricing calculator:
   ```bash
   python execution/receptionist_pricing_calculator.py
   ```
2. Enter values from the discovery call
3. Review the output — especially:
   - Total monthly cost to you
   - Suggested client price range
   - Recommended tier
4. Adjust tier/pricing based on:
   - Local market rates (e.g., Panama receptionist salary ~$600-1,000/mo)
   - Client's perceived value and budget
   - Competitive positioning ("cheaper than a human, works 24/7")
5. Quote is auto-saved to `.tmp/last_pricing_quote.txt`

### Pricing Anchors for Panama Market
- Full-time receptionist: ~$600-1,000/month (salary + benefits)
- AI receptionist: works 24/7, bilingual, never sick, no benefits
- Position as: "Replace or augment your receptionist for less"

---

## Phase 3: Proposal

### Objective
Create and send a professional proposal.

### Steps
1. Copy the proposal template:
   ```bash
   cp ai-receptionist-service/proposal_template.md .tmp/proposal_[client_name].md
   ```
2. Fill in ALL bracketed placeholders with client-specific details from discovery notes
3. Check/uncheck feature boxes based on what was discussed
4. Insert pricing from Phase 2
5. Remove any sections that don't apply (e.g., SMS if not selected)
6. Review for accuracy and professionalism
7. Send to client (PDF export or Google Docs)

### Key Selling Points to Emphasize
- No missed calls — ever
- 24/7 coverage at fraction of human cost
- Bilingual with zero extra cost
- Instant answers, no hold time
- Professional, consistent experience every call

---

## Phase 4: Setup (After Client Approval)

### Objective
Build and deploy the AI receptionist agent.

### Steps

#### 4a. Retell AI Agent Configuration
1. Log into Retell AI dashboard
2. Create new agent
3. Configure:
   - **Voice**: Select natural Spanish voice (ElevenLabs recommended for Spanish)
   - **LLM**: Gemini 2.0 Flash (best cost/performance ratio) or per pricing agreement
   - **System prompt**: Build from discovery notes — include greeting, business info, FAQ, escalation rules
   - **Language detection**: Enable auto-detection for Spanish/English
   - **Fallback behavior**: Transfer to human / take message per client preference

#### 4b. Phone Number Setup
1. In Twilio or Retell:
   - Provision Panama local number (if available) or US number
   - If client wants to keep existing number: set up call forwarding to the Retell number
2. Test inbound calling

#### 4c. Knowledge Base
1. Create knowledge base in Retell with:
   - Office hours and location
   - Services offered
   - Accepted insurance plans
   - Common FAQ answers
   - Emergency procedures
2. Test knowledge retrieval accuracy

#### 4d. Integrations (if applicable)
- Email notifications for messages
- SMS via Twilio for booking confirmations
- Calendar integration for available slots (if direct booking)
- Webhook for CRM updates

#### 4e. Bilingual Testing
1. Test 10+ calls in Spanish — verify:
   - Greeting is natural
   - Medical/dental terms are correct
   - Tone matches client preference
   - Fallback to human works
2. Test 10+ calls in English — same checks
3. Test language switching mid-call
4. Test edge cases:
   - Mumbled speech
   - Background noise
   - Unexpected questions
   - Emergency keywords

---

## Phase 5: Soft Launch

### Objective
Run AI alongside existing staff for monitoring period.

### Steps
1. Route calls to AI receptionist
2. Have existing staff listen/monitor for first 2-3 days
3. Collect feedback on:
   - Accuracy of responses
   - Tone and naturalness
   - Any missed intents or confusion
   - Call quality / latency issues
4. Tune prompts and knowledge base based on feedback
5. Duration: 3-5 business days

---

## Phase 6: Go Live

### Steps
1. Switch AI to primary receptionist
2. Set up monitoring dashboard / alerts
3. Send client a "you're live" confirmation with:
   - Their AI receptionist phone number
   - How to reach you for support
   - Monthly report schedule
4. Schedule 1-week check-in call
5. Schedule 1-month review call

---

## Phase 7: Ongoing Management

### Monthly Tasks
- Review call volume and costs
- Send client monthly usage report
- Check for knowledge base updates needed (new services, changed hours, etc.)
- Review call recordings (if enabled) for quality
- Update pricing if volume significantly changes

### Quarterly Tasks
- Review and optimize LLM choice (cost vs quality)
- Test voice quality with new model releases
- Check for Retell AI platform updates
- Discuss expansion opportunities with client (more locations, outbound, etc.)

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Panama phone number unavailable on Retell/Twilio | Use US number with local forwarding, or SIP trunk |
| Spanish voice quality not natural enough | Test multiple ElevenLabs voices; consider custom voice cloning |
| Latency (US servers, Panama callers) | Test before launch; consider Retell edge regions if available |
| Panama AI disclosure regulations | Research before launch; add disclosure to greeting if required |
| Scheduling system integration complex | Start with message-taking; add direct booking as Phase 2 |
| Client's call volume exceeds estimate | Built-in overage pricing; review monthly and adjust tier |

---

## Tools Used

| Tool | Location | Purpose |
|------|----------|---------|
| Pricing Calculator | `execution/receptionist_pricing_calculator.py` | Calculate costs and generate pricing quotes |
| Proposal Template | `ai-receptionist-service/proposal_template.md` | Generate client proposals |
| Discovery Notes | `.tmp/discovery_notes_[client].md` | Store client discovery call notes |
| Pricing Quotes | `.tmp/last_pricing_quote.txt` | Last generated pricing quote |

---

*Last updated: 2026-02-07*
