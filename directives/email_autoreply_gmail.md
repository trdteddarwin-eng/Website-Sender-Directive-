# Gmail Email Monitor & Auto-Reply

## Purpose
Monitor ted@tedca.com for incoming emails, categorize them using Claude, auto-reply to non-bounces, and send notification emails. Runs as an N8N workflow.

## Infrastructure

### Google Sheet (Tracking)
- **Name**: `Email Monitor - ted@tedca.com`
- **ID**: `1oLq0oWV10F3iVg7osCevNBSHNDKzgLaElwc82RePvrc`
- **URL**: https://docs.google.com/spreadsheets/d/1oLq0oWV10F3iVg7osCevNBSHNDKzgLaElwc82RePvrc

**Columns:**
| Column | Description |
|--------|-------------|
| email_id | Gmail message ID (unique identifier) |
| received_at | When email was received |
| processed_at | When we processed it |
| sender_email | From address |
| sender_name | Sender's display name |
| subject | Email subject |
| body_preview | First 200 chars of body |
| category | INTERESTED / NOT_INTERESTED / QUESTION / BOUNCE |
| reply_sent | true/false |
| reply_preview | First 200 chars of reply |
| notification_sent | true/false |
| error_message | Any errors during processing |

### Gmail Label
- **Label Name**: `auto-processed`
- **Purpose**: Marks emails as processed to prevent re-processing
- **Creation**: Must be created manually in Gmail settings

### N8N Workflow
- **Location**: N8N instance at `n8n.srv1080136.hstgr.cloud`
- **Workflow JSON**: `n8n_email_monitor_workflow.json`
- **Schedule**: Every 5 minutes

## Workflow Flow

```
Schedule Trigger (every 5 min)
    ↓
Gmail: Get unread emails (filter: is:unread -label:auto-processed)
    ↓
IF (Has Emails)
    ↓
Google Sheets: Check if email_id already processed
    ↓
IF (Not Processed)
    ↓
Code: Filter spam/newsletters
    ↓
HTTP Request: Claude Categorization
    ↓
IF (category != BOUNCE)
    ├── TRUE: Generate Reply → Send → Notify → Log → Label
    └── FALSE: Log as bounce → Label
```

## Categorization

Claude categorizes emails into ONE of:

| Category | Description | Action |
|----------|-------------|--------|
| INTERESTED | Wants call, more info, positive interest | Generate & send reply |
| NOT_INTERESTED | Declines but not unsubscribe request | Generate & send reply |
| QUESTION | Asks questions, unclear intent | Generate & send reply |
| BOUNCE | Auto-reply, unsubscribe, out-of-office, delivery failure | Log only, no reply |

### Categorization Prompt
```
Categorize this email into ONE category:

INTERESTED - Wants call, more info, shows positive interest
NOT_INTERESTED - Declines, says no, but not asking to unsubscribe
QUESTION - Asks questions without clear interest/disinterest
BOUNCE - Auto-reply, unsubscribe, out-of-office, delivery failure

From: {from}
Subject: {subject}
Body: {body}

ONE WORD ANSWER:
```

## Reply Generation

### Reply Prompt
```
Write a short reply email (3-8 sentences).

THEIR EMAIL:
From: {from}
Subject: {subject}
Body: {body}

CATEGORY: {category}

RULES:
- Friendly, concise, non-corporate tone
- For INTERESTED: Propose a call/meeting
- For NOT_INTERESTED: Be gracious, keep door open
- For QUESTION: Answer directly then guide to next step
- Return ONLY the word SKIP if they said 'unsubscribe' or 'remove me'
- Use plain text format
- Sign off as 'Ted'

REPLY:
```

### Skip Conditions
Claude returns "SKIP" (no reply sent) when:
- Email contains "unsubscribe" or "remove me"
- Conversation is clearly finished

## Spam Filter

The Code node filters out emails from:
- noreply / no-reply addresses
- mailer-daemon
- newsletter / marketing addresses
- notifications@ / notification@
- automated / donotreply / do-not-reply
- Auto-replies (subject contains "automatic reply", "auto-reply", "out of office")

## Credentials Required in N8N

1. **Gmail OAuth** (`Gmail - ted@tedca.com`)
   - Account: ted@tedca.com
   - Scopes: gmail.readonly, gmail.modify, gmail.send

2. **Google Sheets OAuth** (`Google Sheets`)
   - Scopes: spreadsheets, drive

3. **Anthropic API** (`Anthropic API`)
   - Header: `x-api-key`
   - Value: Your Anthropic API key

4. **SMTP** (`SMTP`) - For notifications
   - Configure based on your email provider

## Setup Steps

1. **Create Gmail Label**
   - Go to Gmail settings > Labels
   - Create new label: `auto-processed`

2. **Import Workflow**
   - Go to N8N
   - Import `n8n_email_monitor_workflow.json`
   - Replace credential placeholders with actual credential IDs

3. **Configure Credentials**
   - Set up Gmail OAuth for ted@tedca.com
   - Set up Google Sheets OAuth
   - Add Anthropic API key as HTTP Header Auth
   - Configure SMTP for notifications

4. **Test**
   - Send test email to ted@tedca.com
   - Manually trigger workflow
   - Verify: categorization, reply, notification, sheet logging, label added

5. **Activate**
   - Enable the workflow
   - Monitor for first few runs

## Safeguards

- **Duplicate Check**: email_id lookup in sheet before processing
- **Spam Filter**: Code node filters noise emails
- **Label**: `auto-processed` prevents re-processing
- **Skip Check**: Empty or "SKIP" replies not sent
- **Rate Limiting**: 5-minute interval between runs
- **Logging**: All actions logged to tracking sheet

## Troubleshooting

### Emails Not Being Processed
1. Check Gmail label exists
2. Verify OAuth scopes include gmail.readonly
3. Check N8N workflow is active

### Duplicate Processing
1. Verify sheet lookup is working
2. Check email_id column matches Gmail message IDs
3. Ensure label is being added after processing

### Claude API Errors
1. Verify API key is correct
2. Check anthropic-version header is set
3. Review rate limits

### Replies Not Sending
1. Check Gmail send permissions
2. Verify thread ID is correct
3. Check reply content is not "SKIP"

## Files

| File | Purpose |
|------|---------|
| `execution/setup_email_monitor.py` | Creates tracking sheet and Gmail label |
| `n8n_email_monitor_workflow.json` | N8N workflow to import |
| `directives/email_autoreply_gmail.md` | This documentation |

## Related

- `directives/instantly_autoreply.md` - Similar system for Instantly.ai
- `execution/instantly_autoreply.py` - Python version for Instantly
