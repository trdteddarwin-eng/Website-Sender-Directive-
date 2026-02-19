#!/usr/bin/env python3
"""
AI Voice Receptionist — Gamma.ai Proposal Prompt Generator

Collects client discovery answers interactively, then generates a
ready-to-paste prompt for Gamma.ai's free presentation generator.

Usage:
    python3 execution/receptionist_proposal_generator.py

Output:
    - Prints the Gamma prompt to terminal
    - Copies to clipboard (macOS)
    - Saves to .tmp/gamma_prompt_[client].txt
"""

import os
import subprocess
from datetime import datetime

# ── Cost constants (keep in sync with receptionist_pricing_calculator.py) ──
VOICE_ENGINE = 0.07
LLM_GEMINI = 0.006
INBOUND_TELEPHONY = 0.01
KB_ADDON = 0.005


def ask(question, default=None):
    """Prompt for free text input."""
    suffix = f" [{default}]" if default else ""
    answer = input(f"  {question}{suffix}: ").strip()
    return answer if answer else default


def ask_number(question, default=None):
    """Prompt for a number."""
    while True:
        raw = ask(question, default)
        try:
            return float(raw) if "." in str(raw) else int(raw)
        except (ValueError, TypeError):
            print("  Please enter a number.")


def ask_yes_no(question, default=True):
    """Prompt for yes/no."""
    hint = "Y/n" if default else "y/N"
    raw = input(f"  {question} [{hint}]: ").strip().lower()
    if raw == "":
        return default
    return raw in ("y", "yes")


def ask_list(question, count=5):
    """Prompt for a numbered list of items."""
    print(f"  {question}")
    items = []
    for i in range(1, count + 1):
        item = input(f"    {i}. ").strip()
        if not item:
            break
        items.append(item)
    return items


def collect_discovery():
    """Run through all discovery questions and return answers dict."""
    d = {}

    print("\n" + "=" * 60)
    print("  AI VOICE RECEPTIONIST — CLIENT DISCOVERY")
    print("  Answer these from your discovery call notes.")
    print("=" * 60)

    # ── Business Basics ──
    print("\n── BUSINESS BASICS ──")
    d["client_name"] = ask("Client / practice name")
    d["practice_type"] = ask("Type of practice (e.g., general dentist, medical clinic, specialist)")
    d["locations"] = ask_number("How many locations?", 1)
    d["providers"] = ask_number("How many doctors / providers?", 1)
    d["hours"] = ask("Business hours (e.g., Mon-Fri 8am-5pm)")
    d["after_hours"] = ask_yes_no("Do they need after-hours (24/7) coverage?", False)
    d["country"] = ask("Country / city (e.g., Panama City, San Juan PR)", "Panama City")

    # ── Call Volume ──
    print("\n── CALL VOLUME ──")
    d["calls_per_day"] = ask_number("Estimated calls per day", 30)
    d["unanswered"] = ask_number("How many go unanswered / voicemail per day?", 10)
    d["avg_duration"] = ask_number("Average call duration in minutes", 2)
    d["direction"] = ask("Mostly inbound, outbound, or both?", "inbound")

    # ── What the AI Handles ──
    print("\n── WHAT THE AI NEEDS TO HANDLE ──")
    d["top_reasons"] = ask_list("Top reasons patients call (enter up to 5):", 5)
    d["booking"] = ask_yes_no("Do they need appointment booking?", True)
    d["scheduling_system"] = ask("What scheduling system? (e.g., Dentrix, Google Calendar, paper)", "manual")
    d["direct_booking"] = ask_yes_no("Should AI book directly into the system (vs. just collect info)?", False)
    d["insurance_questions"] = ask_yes_no("Handle insurance questions?", False)
    d["emergency_routing"] = ask_yes_no("Emergency call routing to on-call doctor?", False)
    d["message_delivery"] = ask("How should messages reach staff? (email, SMS, WhatsApp, app)", "email")

    # ── Language ──
    print("\n── LANGUAGE & TONE ──")
    d["spanish_pct"] = ask_number("Percentage of calls in Spanish (%)", 70)
    d["english_pct"] = 100 - d["spanish_pct"]
    d["auto_detect"] = ask_yes_no("Auto-detect language (vs. ask caller)?", True)
    d["tone"] = ask("Desired tone (e.g., warm and professional, formal, friendly)", "warm and professional")
    d["greeting"] = ask("Custom greeting (leave blank if none)")

    # ── Technical ──
    print("\n── TECHNICAL ──")
    d["current_phone"] = ask("Current phone system (landline, VoIP, cell, PBX)", "VoIP")
    d["keep_number"] = ask_yes_no("Do they want to keep their current number?", True)
    d["fallback"] = ask("What happens when AI can't handle? (transfer to human, take message)", "transfer to human")
    d["sms_followups"] = ask_yes_no("Need SMS follow-ups after calls?", False)
    d["integrations"] = ask("Other software to integrate? (CRM, EHR, WhatsApp, etc.)", "none")

    # ── Pain Points (for selling) ──
    print("\n── PAIN POINTS & VALUE ──")
    d["avg_patient_value"] = ask_number("Average value of a new patient visit ($)", 200)
    d["receptionist_salary"] = ask_number("Current receptionist monthly salary ($)", 800)

    return d


def calculate_quick_cost(d):
    """Quick cost estimate based on discovery answers."""
    per_min = VOICE_ENGINE + LLM_GEMINI + INBOUND_TELEPHONY + KB_ADDON
    per_call = round(per_min * d["avg_duration"], 2)
    biz_days = 22
    monthly_calls = d["calls_per_day"] * biz_days
    if d["after_hours"]:
        monthly_calls += int(d["calls_per_day"] * 0.2 * 30)
    monthly_cost = round(monthly_calls * per_call, 2)
    monthly_cost += 8  # phone number

    if d["sms_followups"]:
        monthly_cost += 20

    return {
        "per_min": per_min,
        "per_call": per_call,
        "monthly_calls": monthly_calls,
        "monthly_cost": round(monthly_cost, 2),
        "suggested_price": round(monthly_cost * 4, -1),  # 4x markup
    }


def generate_gamma_prompt(d, cost):
    """Generate the Gamma.ai paste-ready prompt."""

    # Build feature list
    features = []
    features.append("Answers every inbound call instantly — zero hold time, zero missed calls")
    features.append(f"Bilingual: Spanish ({d['spanish_pct']}%) and English ({d['english_pct']}%) with automatic language detection")
    if d["after_hours"]:
        features.append("24/7 availability — nights, weekends, and holidays included")
    else:
        features.append(f"Available during business hours: {d['hours']}")
    if d["booking"]:
        if d["direct_booking"]:
            features.append(f"Books appointments directly into {d['scheduling_system']}")
        else:
            features.append("Collects appointment requests and sends to staff for booking")
    if d["insurance_questions"]:
        features.append("Answers insurance and coverage questions from a knowledge base")
    if d["emergency_routing"]:
        features.append("Detects emergencies and immediately routes to on-call provider")
    features.append(f"Sends call summaries to staff via {d['message_delivery']}")
    if d["sms_followups"]:
        features.append("Sends SMS confirmations to patients after booking")
    features.append(f"Graceful fallback: {d['fallback']} when needed")

    features_text = "\n".join(f"- {f}" for f in features)

    # Build reasons list
    reasons_text = "\n".join(f"- {r}" for r in d["top_reasons"]) if d["top_reasons"] else "- Appointment booking\n- General inquiries"

    # Lost revenue calculation
    lost_daily = d["unanswered"] * d["avg_patient_value"] * 0.3  # assume 30% convert
    lost_monthly = round(lost_daily * 22)

    # ROI
    roi_monthly = round(lost_monthly - cost["suggested_price"])

    # Greeting
    greeting_line = ""
    if d.get("greeting"):
        greeting_line = f'\nCustom greeting: "{d["greeting"]}"'

    prompt = f"""Create a professional, visually stunning business proposal presentation for an AI Voice Receptionist service.

Client: {d["client_name"]}
Industry: {d["practice_type"]}
Location: {d["country"]}
Locations: {d["locations"]}
Providers: {d["providers"]}

---

Slide 1: COVER
Title: AI Voice Receptionist for {d["client_name"]}
Subtitle: Never miss another patient call.
Include: Professional medical/dental office imagery. Clean, modern design.

---

Slide 2: THE PROBLEM
Title: Every Missed Call Is a Lost Patient
Key stats:
- {d["client_name"]} receives ~{d["calls_per_day"]} calls per day
- ~{d["unanswered"]} calls go unanswered or to voicemail daily
- That's ~{d["unanswered"] * 22} missed calls per month
- At ${d["avg_patient_value"]} average patient value, that's up to ${lost_monthly:,}/month in lost revenue
- Patients who reach voicemail often call the next practice instead
Make this slide impactful — show the cost of doing nothing.

---

Slide 3: THE SOLUTION
Title: Your AI-Powered Receptionist
An intelligent voice assistant that answers every call, in both Spanish and English, 24 hours a day — for a fraction of the cost of additional staff.
{greeting_line}
Key points:
- Answers instantly — no hold music, no voicemail
- Understands and speaks natural Spanish and English
- Handles the most common patient requests automatically
- Seamlessly transfers to your team when a human touch is needed

---

Slide 4: WHAT IT HANDLES
Title: Built for {d["practice_type"]} Workflows
Top reasons patients call {d["client_name"]}:
{reasons_text}

The AI receptionist handles all of these — accurately, consistently, every single time.

---

Slide 5: KEY FEATURES
Title: Everything Your Front Desk Needs
{features_text}

---

Slide 6: HOW IT WORKS
Title: Simple 3-Step Process
Step 1: Patient calls your office number → AI answers with your custom greeting
Step 2: AI handles the conversation — books appointments, answers questions, takes messages
Step 3: Your staff receives a summary with caller details and any action needed
Include a simple visual flow diagram.

---

Slide 7: BILINGUAL EXCELLENCE
Title: Fluent in Spanish & English
- {d["spanish_pct"]}% of your calls are in Spanish — our AI handles them natively
- Automatic language detection within the first sentence
- Natural Latin American Spanish accent — not robotic or awkward
- Medical and dental terminology in both languages
- Tone: {d["tone"]}
This is not a translation tool — it's a native speaker.

---

Slide 8: COST COMPARISON
Title: Smarter Than Hiring Another Receptionist
Compare side by side:

Human receptionist:
- ${d["receptionist_salary"]:,}/month salary + benefits
- Works 8 hours/day, 5 days/week
- Calls in sick, takes vacation
- Handles one call at a time
- Training required for bilingual support

AI receptionist:
- ${cost["suggested_price"]:,.0f}/month flat fee
- Works 24 hours/day, 7 days/week
- Never calls in sick, never takes breaks
- Handles unlimited simultaneous calls
- Bilingual from day one

Savings: ${d["receptionist_salary"] - cost["suggested_price"]:,.0f}/month vs. a full-time hire
(Or use it alongside your current staff to handle overflow and after-hours)

---

Slide 9: YOUR ROI
Title: The Numbers Speak for Themselves
- Missed calls recovered: ~{d["unanswered"] * 22}/month
- Potential revenue recovered: up to ${lost_monthly:,}/month
- Your investment: ${cost["suggested_price"]:,.0f}/month
- Net ROI: up to ${roi_monthly:,}/month in recovered revenue
- Payback: The system pays for itself with just {max(1, round(cost["suggested_price"] / d["avg_patient_value"]))} additional patients per month
Make this slide visually compelling with large numbers.

---

Slide 10: PRICING
Title: Simple, Predictable Pricing
Monthly service: ${cost["suggested_price"]:,.0f}/month
Includes:
- Up to {cost["monthly_calls"]:,} calls per month
- {"24/7 coverage" if d["after_hours"] else "Business hours coverage (" + d["hours"] + ")"}
- Bilingual support (Spanish + English)
- Knowledge base with your practice info
- Call summaries delivered to your team
- Dedicated local phone number
- Ongoing maintenance and optimization

One-time setup: $1,000
Includes: AI configuration, bilingual prompt tuning, knowledge base build, phone setup, testing

---

Slide 11: TIMELINE
Title: Live in 2 Weeks
Week 1: Discovery, setup, knowledge base creation, AI configuration
Week 2: Testing, bilingual tuning, soft launch with your team monitoring
Day 15+: Full launch — AI is your primary receptionist

---

Slide 12: NEXT STEPS
Title: Let's Get Started
1. Sign the service agreement
2. Send us your practice details (hours, services, insurance plans, FAQ)
3. We build and test your AI receptionist
4. Soft launch with your team for 3-5 days
5. Go live — never miss a call again

Call to action: "Ready to stop losing patients to voicemail?"

---

Design notes: Use a clean, modern, professional theme. Colors should feel trustworthy — blues, whites, subtle greens. Medical/healthcare imagery where appropriate. Large bold numbers on the ROI and pricing slides. Keep text minimal — let the visuals do the work."""

    return prompt


def main():
    d = collect_discovery()
    cost = calculate_quick_cost(d)

    print("\n" + "=" * 60)
    print("  QUICK COST ESTIMATE")
    print("=" * 60)
    print(f"  Your cost per minute:    ${cost['per_min']:.3f}")
    print(f"  Your cost per call:      ${cost['per_call']:.2f}")
    print(f"  Estimated calls/month:   {cost['monthly_calls']:,}")
    print(f"  Your total monthly cost: ${cost['monthly_cost']:,.2f}")
    print(f"  Suggested client price:  ${cost['suggested_price']:,.0f}/month")
    print(f"  Your monthly margin:     ${cost['suggested_price'] - cost['monthly_cost']:,.0f}")

    print("\n⏳ Generating Gamma.ai prompt...")
    prompt = generate_gamma_prompt(d, cost)

    # Save to file
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    safe_name = d["client_name"].lower().replace(" ", "_") if d["client_name"] else "client"
    out_path = os.path.join(tmp_dir, f"gamma_prompt_{safe_name}.txt")
    with open(out_path, "w") as f:
        f.write(prompt)

    # Copy to clipboard (macOS)
    try:
        process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        process.communicate(prompt.encode("utf-8"))
        clipboard_ok = True
    except Exception:
        clipboard_ok = False

    print("\n" + "=" * 60)
    print("  GAMMA.AI PROMPT READY")
    print("=" * 60)
    if clipboard_ok:
        print("  ✅ Copied to clipboard!")
    print(f"  📄 Saved to: {out_path}")
    print()
    print("  HOW TO USE:")
    print("  1. Go to gamma.app")
    print("  2. Click 'Create new' → 'Paste in text'")
    print("  3. Paste the prompt (Cmd+V)")
    print("  4. Pick a theme and generate")
    print()

    # Also print the prompt so they can see it
    if ask_yes_no("\n  Show the full prompt in terminal?", False):
        print("\n" + "─" * 60)
        print(prompt)
        print("─" * 60)


if __name__ == "__main__":
    main()
