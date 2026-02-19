#!/usr/bin/env python3
"""
AI Voice Receptionist — Pricing Calculator
Calculates Retell AI costs and suggests client pricing based on usage parameters.
"""

import os
import sys
from datetime import datetime

# ============================================================
# RATE CONSTANTS — Update these when Retell/Twilio prices change
# ============================================================

# Voice engine (speech-to-text + text-to-speech) per minute
VOICE_ENGINE_RATE = 0.07

# LLM per-minute rates
LLM_RATES = {
    "gemini_flash": {"name": "Gemini 2.0 Flash", "rate": 0.006},
    "claude_haiku": {"name": "Claude Haiku", "rate": 0.02},
    "gpt4o":        {"name": "GPT-4o",         "rate": 0.05},
}

# Telephony per-minute rates
TELEPHONY_RATES = {
    "inbound":          {"name": "Inbound (any origin)",    "rate": 0.01},
    "outbound_us":      {"name": "Outbound US domestic",    "rate": 0.015},
    "outbound_pa_land": {"name": "Outbound Panama landline","rate": 0.045},
    "outbound_pa_mob":  {"name": "Outbound Panama mobile",  "rate": 0.34},
}

# Optional add-on per-minute rates
ADDON_RATES = {
    "knowledge_base": {"name": "Knowledge Base",      "rate": 0.005},
    "denoising":      {"name": "Advanced Denoising",   "rate": 0.005},
}

# Monthly fixed costs
FIXED_COSTS = {
    "phone_us":     {"name": "US phone number",           "cost": 2.00},
    "phone_panama": {"name": "Panama local number",       "cost": 8.00},
    "sms":          {"name": "SMS capability",             "cost": 20.00},
    "kb_extra":     {"name": "Extra knowledge base (each)","cost": 8.00},
}

# Pricing tier definitions
TIERS = {
    "starter": {
        "name": "Starter",
        "max_calls": 500,
        "includes": "Up to 500 calls/mo, business hours, inbound only",
        "price_range": (400, 500),
    },
    "professional": {
        "name": "Professional",
        "max_calls": 1500,
        "includes": "Up to 1,500 calls/mo, 24/7, inbound + basic outbound reminders",
        "price_range": (800, 1000),
    },
    "premium": {
        "name": "Premium",
        "max_calls": float("inf"),
        "includes": "Unlimited calls, 24/7, inbound + outbound, SMS, integrations",
        "price_range": (1500, 2000),
    },
}

SETUP_FEE_RANGE = (500, 1500)


def prompt_choice(prompt_text, options, default=None):
    """Prompt user to pick from a numbered list of options."""
    print(f"\n{prompt_text}")
    for i, (key, label) in enumerate(options, 1):
        marker = " (default)" if key == default else ""
        print(f"  {i}. {label}{marker}")
    while True:
        raw = input("Enter choice number: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            idx = int(raw) - 1
            if 0 <= idx < len(options):
                return options[idx][0]
        except ValueError:
            pass
        print("Invalid choice. Try again.")


def prompt_number(prompt_text, default=None, allow_float=False):
    """Prompt user for a numeric value."""
    suffix = f" [{default}]" if default is not None else ""
    while True:
        raw = input(f"{prompt_text}{suffix}: ").strip()
        if raw == "" and default is not None:
            return default
        try:
            return float(raw) if allow_float else int(raw)
        except ValueError:
            print("Please enter a valid number.")


def prompt_yes_no(prompt_text, default=True):
    """Prompt user for yes/no."""
    hint = "Y/n" if default else "y/N"
    raw = input(f"{prompt_text} [{hint}]: ").strip().lower()
    if raw == "":
        return default
    return raw in ("y", "yes")


def calculate_pricing(params):
    """Calculate all costs from the gathered parameters."""
    results = {}

    # --- Per-minute cost breakdown ---
    per_min = {}
    per_min["Voice Engine"] = VOICE_ENGINE_RATE

    llm = LLM_RATES[params["llm"]]
    per_min[f"LLM ({llm['name']})"] = llm["rate"]

    # Telephony — depends on direction
    if params["direction"] == "inbound":
        tel = TELEPHONY_RATES["inbound"]
    elif params["direction"] == "outbound":
        tel = TELEPHONY_RATES[params["outbound_dest"]]
    else:  # both
        # Weighted: assume 80% inbound, 20% outbound for "both"
        inbound_rate = TELEPHONY_RATES["inbound"]["rate"]
        outbound_rate = TELEPHONY_RATES[params["outbound_dest"]]["rate"]
        blended = 0.8 * inbound_rate + 0.2 * outbound_rate
        tel = {"name": "Blended (80% inbound / 20% outbound)", "rate": round(blended, 4)}
    per_min[f"Telephony ({tel['name']})"] = tel["rate"]

    # Add-ons
    if params["knowledge_base"]:
        per_min["Knowledge Base"] = ADDON_RATES["knowledge_base"]["rate"]
    if params["denoising"]:
        per_min["Advanced Denoising"] = ADDON_RATES["denoising"]["rate"]

    total_per_min = sum(per_min.values())
    results["per_min_breakdown"] = per_min
    results["total_per_min"] = round(total_per_min, 4)

    # --- Per-call cost ---
    avg_duration = params["avg_call_duration"]
    per_call = round(total_per_min * avg_duration, 2)
    results["per_call"] = per_call

    # --- Monthly usage cost ---
    calls_per_day = params["calls_per_day"]
    biz_days = params["biz_days"]
    if params["after_hours"]:
        # Assume after-hours adds ~20% more calls spread across 30 days
        total_monthly_calls = (calls_per_day * biz_days) + int(calls_per_day * 0.2 * 30)
    else:
        total_monthly_calls = calls_per_day * biz_days

    monthly_usage = round(total_monthly_calls * per_call, 2)
    results["total_monthly_calls"] = total_monthly_calls
    results["monthly_usage"] = monthly_usage

    # --- Monthly fixed costs ---
    fixed = {}
    if params["phone_type"] == "panama":
        fixed["Panama local number"] = FIXED_COSTS["phone_panama"]["cost"]
    else:
        fixed["US phone number"] = FIXED_COSTS["phone_us"]["cost"]

    if params["sms"]:
        fixed["SMS capability"] = FIXED_COSTS["sms"]["cost"]

    total_fixed = sum(fixed.values())
    results["fixed_breakdown"] = fixed
    results["total_fixed"] = total_fixed

    # --- Total monthly cost ---
    total_monthly = round(monthly_usage + total_fixed, 2)
    results["total_monthly_cost"] = total_monthly

    # --- Suggested pricing ---
    # 3x-5x markup on total cost
    suggested_low = round(total_monthly * 3, -1)   # round to nearest $10
    suggested_high = round(total_monthly * 5, -1)
    results["suggested_price_low"] = max(suggested_low, 300)   # floor at $300
    results["suggested_price_high"] = max(suggested_high, 500)

    # Margin
    results["margin_low"] = results["suggested_price_low"] - total_monthly
    results["margin_high"] = results["suggested_price_high"] - total_monthly

    # --- Recommended tier ---
    if total_monthly_calls <= 500:
        rec_tier = TIERS["starter"]
    elif total_monthly_calls <= 1500:
        rec_tier = TIERS["professional"]
    else:
        rec_tier = TIERS["premium"]
    results["recommended_tier"] = rec_tier

    return results


def format_report(params, results):
    """Format results into a readable report string."""
    lines = []
    sep = "=" * 60

    lines.append(sep)
    lines.append("  AI VOICE RECEPTIONIST — PRICING QUOTE")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(sep)

    lines.append("\n── CONFIGURATION ──")
    lines.append(f"  Call direction:      {params['direction']}")
    lines.append(f"  Calls/day:           {params['calls_per_day']}")
    lines.append(f"  Avg call duration:   {params['avg_call_duration']} min")
    lines.append(f"  Business days/month: {params['biz_days']}")
    lines.append(f"  After-hours:         {'Yes' if params['after_hours'] else 'No'}")
    lines.append(f"  LLM:                 {LLM_RATES[params['llm']]['name']}")
    lines.append(f"  Phone number:        {'Panama local' if params['phone_type'] == 'panama' else 'US'}")
    lines.append(f"  Knowledge base:      {'Yes' if params['knowledge_base'] else 'No'}")
    lines.append(f"  Denoising:           {'Yes' if params['denoising'] else 'No'}")
    lines.append(f"  SMS:                 {'Yes' if params['sms'] else 'No'}")

    lines.append("\n── PER-MINUTE COST BREAKDOWN ──")
    for component, rate in results["per_min_breakdown"].items():
        lines.append(f"  {component:<40} ${rate:.4f}/min")
    lines.append(f"  {'─' * 40} {'─' * 12}")
    lines.append(f"  {'TOTAL PER MINUTE':<40} ${results['total_per_min']:.4f}/min")

    lines.append(f"\n── PER-CALL COST ──")
    lines.append(f"  Avg {params['avg_call_duration']}-min call:  ${results['per_call']:.2f}")

    lines.append(f"\n── MONTHLY USAGE ──")
    lines.append(f"  Estimated calls/month: {results['total_monthly_calls']:,}")
    lines.append(f"  Usage cost:            ${results['monthly_usage']:,.2f}")

    lines.append(f"\n── MONTHLY FIXED COSTS ──")
    if results["fixed_breakdown"]:
        for item, cost in results["fixed_breakdown"].items():
            lines.append(f"  {item:<40} ${cost:.2f}")
    else:
        lines.append("  (none)")
    lines.append(f"  {'─' * 40} {'─' * 12}")
    lines.append(f"  {'TOTAL FIXED':<40} ${results['total_fixed']:.2f}")

    lines.append(f"\n{sep}")
    lines.append(f"  TOTAL MONTHLY COST TO YOU:  ${results['total_monthly_cost']:,.2f}")
    lines.append(sep)

    lines.append(f"\n── SUGGESTED CLIENT PRICING ──")
    lines.append(f"  Charge client:  ${results['suggested_price_low']:,.0f} – ${results['suggested_price_high']:,.0f}/month")
    lines.append(f"  Your margin:    ${results['margin_low']:,.0f} – ${results['margin_high']:,.0f}/month")

    tier = results["recommended_tier"]
    lines.append(f"\n── RECOMMENDED TIER ──")
    lines.append(f"  {tier['name']}")
    lines.append(f"  {tier['includes']}")
    lines.append(f"  Suggested price range: ${tier['price_range'][0]:,} – ${tier['price_range'][1]:,}/month")

    lines.append(f"\n── SETUP FEE ──")
    lines.append(f"  Recommended: ${SETUP_FEE_RANGE[0]:,} – ${SETUP_FEE_RANGE[1]:,} one-time")

    lines.append(f"\n{sep}")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("  AI VOICE RECEPTIONIST — PRICING CALCULATOR")
    print("=" * 60)
    print("\nAnswer the following to generate a cost + pricing quote.\n")

    params = {}

    # Call direction
    params["direction"] = prompt_choice(
        "Call direction:",
        [("inbound", "Inbound only (patients call you)"),
         ("outbound", "Outbound only (you call patients)"),
         ("both", "Both inbound and outbound")],
        default="inbound",
    )

    # Outbound destination (if applicable)
    if params["direction"] in ("outbound", "both"):
        params["outbound_dest"] = prompt_choice(
            "Outbound call destination:",
            [("outbound_us", "US domestic"),
             ("outbound_pa_land", "Panama landline"),
             ("outbound_pa_mob", "Panama mobile")],
            default="outbound_pa_land",
        )
    else:
        params["outbound_dest"] = None

    # Call volume
    params["calls_per_day"] = prompt_number("\nEstimated calls per day", default=30)
    params["avg_call_duration"] = prompt_number("Average call duration (minutes)", default=2, allow_float=True)
    params["biz_days"] = prompt_number("Business days per month", default=22)

    # After-hours
    params["after_hours"] = prompt_yes_no("\nAfter-hours coverage (24/7)?", default=False)

    # Features
    print("\n── Features ──")
    params["knowledge_base"] = prompt_yes_no("Knowledge base (FAQ, insurance info, etc.)?", default=True)
    params["sms"] = prompt_yes_no("SMS follow-ups (booking confirmations, etc.)?", default=False)
    params["denoising"] = prompt_yes_no("Advanced denoising (noisy clinic environments)?", default=False)

    # LLM choice
    params["llm"] = prompt_choice(
        "LLM (brain of the agent):",
        [("gemini_flash", "Gemini 2.0 Flash — $0.006/min (cheapest)"),
         ("claude_haiku", "Claude Haiku — $0.02/min (balanced)"),
         ("gpt4o", "GPT-4o — $0.05/min (most expensive)")],
        default="gemini_flash",
    )

    # Phone number type
    params["phone_type"] = prompt_choice(
        "Phone number type:",
        [("us", "US number ($2/mo)"),
         ("panama", "Panama local number ($8/mo)")],
        default="panama",
    )

    # --- Calculate ---
    results = calculate_pricing(params)
    report = format_report(params, results)

    print("\n")
    print(report)

    # Save to .tmp
    tmp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    out_path = os.path.join(tmp_dir, "last_pricing_quote.txt")
    with open(out_path, "w") as f:
        f.write(report)
    print(f"\nQuote saved to: {out_path}")


if __name__ == "__main__":
    main()
