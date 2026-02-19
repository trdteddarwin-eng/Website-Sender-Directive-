---
description: Auto-respond to Google reviews for Viva la Pizza
---

## Tool
**Script:** `execution/vlp_fetch_reviews.py`
**Webhook slug:** `vlp-review-responder`

## Available Tools
- **google_reviews_api** - Fetch and reply to Google reviews via Google Business Profile API
- **read_sheet** - Read review log from Google Sheet
- **update_sheet** - Log reviews and responses to Google Sheet
- **send_email** - Send escalation emails for negative reviews

## Goal

Auto-respond to Google reviews across all 4 Viva la Pizza locations in Panama:
- **San Francisco**
- **Condado del Rey**
- **Clayton**
- **Via Argentina**

## Tone Guidelines

All responses must follow these rules:
- **Language:** Spanish by default. If a review is clearly written in English, respond in English instead.
- **Warmth:** Warm, genuine, and professional. NOT corporate or templated. Write like a real person who cares.
- **Brand name:** Always mention "Viva la Pizza" by name at least once in the response.
- **Sign-off:** Always sign off as **"El equipo de Viva la Pizza"**.
- Example: "Hola [nombre]! Muchas gracias por tu visita a Viva la Pizza y por tomarte el tiempo de dejarnos tu opinion. Nos alegra mucho que hayas disfrutado [cosa especifica]. Te esperamos pronto de vuelta! — El equipo de Viva la Pizza"

## Process

1. **Fetch New Reviews**
   - Run `execution/vlp_fetch_reviews.py` to pull reviews from all 4 locations via the Google Business Profile API
   - Use `read_sheet` to check the Review Log and filter out reviews that have already been processed
   - Collect all new, unresponded reviews into a working list with: reviewer_name, rating, text, location, review_id, create_time

2. **Respond to 4-5 Star Reviews**
   - For each review with a rating of 4 or 5 stars:
     - Generate a personalized response **in Spanish** (see Tone Guidelines above)
     - Thank the customer by name
     - Reference specific things they praised in their review (e.g., if they mention the pepperoni pizza, mention it back)
     - Invite them to visit Viva la Pizza again
     - Sign off as "El equipo de Viva la Pizza"
     - Use `google_reviews_api` with action `reply` to post the response

3. **Respond to 3 Star Reviews**
   - For each review with a rating of 3 stars:
     - Generate a thoughtful response **in Spanish** (see Tone Guidelines above)
     - Acknowledge their feedback without being defensive
     - Apologize for falling short of what they expected
     - If they mention specific issues, address them respectfully
     - Invite them to give Viva la Pizza another chance — mention a special offer or simply that you'd love the opportunity to show them a better experience
     - Sign off as "El equipo de Viva la Pizza"
     - Use `google_reviews_api` with action `reply` to post the response

4. **Escalate 1-2 Star Reviews (DO NOT Auto-Respond)**
   - For each review with a rating of 1 or 2 stars:
     - Do **NOT** auto-respond. These require human attention.
     - Use `send_email` to send an escalation email to `info@vivalapizza.net`
     - Email subject: "Resena negativa - [Location] - [Rating] estrellas"
     - Email body should include:
       - Reviewer name
       - Rating
       - Full review text
       - Location name
       - Review date
       - Direct link to the review if available

5. **Log All Reviews**
   - Use `update_sheet` to append every processed review to the Review Log Google Sheet
   - Each row should contain:
     - Date processed
     - Location
     - Reviewer name
     - Rating
     - Review text (truncated if very long)
     - Response sent (or "ESCALATED" for 1-2 star reviews)
     - Status (replied / escalated / error)

6. **Post Activity Summary to Slack**
   - After all reviews are processed, post a summary including:
     - Total reviews processed
     - Breakdown by rating (how many 5-star, 4-star, etc.)
     - Number of auto-replies sent
     - Number of escalations
     - Any errors encountered

## Edge Cases

- **Empty review text:** Some reviews are rating-only with no text. For 4-5 star ratings, respond with a generic but warm thank-you in Spanish. For 3 stars, respond with a short invitation to return. For 1-2 stars, still escalate via email.
- **Duplicate reviews:** Check the Review Log sheet before responding to avoid double-replying.
- **API rate limits:** If the Google Business Profile API returns rate limit errors, wait and retry with exponential backoff.
- **Already-replied reviews:** Skip any review that already has an owner reply (the API returns this info).
- **Non-Spanish reviews:** If a review is clearly written in English, respond in English instead. Match the reviewer's language.
