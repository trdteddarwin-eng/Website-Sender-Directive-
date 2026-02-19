"""Inbox service — IMAP reading for tedca.online accounts via Titan."""

import imaplib
import email
import email.header
import email.utils
import json
import os
from datetime import datetime

# Path to smtp_accounts.json (workspace root / execution/)
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_PIPELINE_APP_DIR = os.path.dirname(_THIS_DIR)
_WORKSPACE_ROOT = os.path.dirname(_PIPELINE_APP_DIR)
SMTP_ACCOUNTS_PATH = os.path.join(_WORKSPACE_ROOT, "execution", "smtp_accounts.json")

IMAP_HOST = "mail.privateemail.com"
IMAP_PORT = 993

# In-memory tracking of last-known UNSEEN UIDs per account
_last_unseen = {}


def _load_accounts():
    """Load all accounts from smtp_accounts.json."""
    with open(SMTP_ACCOUNTS_PATH) as f:
        return json.load(f).get("accounts", [])


def get_tedca_accounts():
    """Return only @tedca.online accounts."""
    return [a for a in _load_accounts() if a["email"].endswith("@tedca.online")]


def _connect(account):
    """Open an IMAP4_SSL connection and login."""
    conn = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
    conn.login(account["username"], account["password"])
    return conn


def _decode_header(raw):
    """Decode an email header value into a string."""
    if not raw:
        return ""
    parts = email.header.decode_header(raw)
    decoded = []
    for data, charset in parts:
        if isinstance(data, bytes):
            decoded.append(data.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(data)
    return " ".join(decoded)


def _parse_date(raw):
    """Parse email date to ISO string."""
    if not raw:
        return ""
    try:
        parsed = email.utils.parsedate_to_datetime(raw)
        return parsed.isoformat()
    except Exception:
        return raw


def fetch_inbox(account, limit=50, offset=0):
    """Fetch email headers from INBOX. Returns list of message dicts."""
    conn = _connect(account)
    try:
        conn.select("INBOX", readonly=True)
        # Search all messages
        status, data = conn.search(None, "ALL")
        if status != "OK":
            return []

        uids = data[0].split()
        if not uids:
            return []

        # Reverse for newest-first, then apply offset/limit
        uids = list(reversed(uids))
        page = uids[offset:offset + limit]

        if not page:
            return []

        messages = []
        # Fetch headers in batch
        uid_range = b",".join(page)
        status, msg_data = conn.fetch(uid_range, "(UID FLAGS BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
        if status != "OK":
            return []

        # Parse response — comes in pairs: (metadata, header_bytes), close_paren
        i = 0
        while i < len(msg_data):
            if isinstance(msg_data[i], tuple):
                meta_line = msg_data[i][0].decode("utf-8", errors="replace")
                header_bytes = msg_data[i][1]

                # Extract UID from meta
                uid = ""
                for part in meta_line.split():
                    if part.startswith("(UID") or part.isdigit():
                        pass
                # More reliable UID extraction
                import re
                uid_match = re.search(r"UID (\d+)", meta_line)
                uid = uid_match.group(1) if uid_match else ""

                # Extract flags
                flags_match = re.search(r"FLAGS \(([^)]*)\)", meta_line)
                flags_str = flags_match.group(1) if flags_match else ""
                is_seen = "\\Seen" in flags_str

                # Parse headers
                msg = email.message_from_bytes(header_bytes)
                from_raw = _decode_header(msg.get("From", ""))
                subject = _decode_header(msg.get("Subject", "(no subject)"))
                date_str = _parse_date(msg.get("Date", ""))

                # Extract display name and email from From header
                from_name, from_addr = email.utils.parseaddr(from_raw)
                if not from_name:
                    from_name = from_addr

                messages.append({
                    "uid": uid,
                    "from_name": from_name,
                    "from_email": from_addr,
                    "subject": subject,
                    "date": date_str,
                    "seen": is_seen,
                })
            i += 1

        return messages
    finally:
        try:
            conn.close()
        except Exception:
            pass
        conn.logout()


def fetch_message_body(account, uid):
    """Fetch full message by UID. Returns dict with html, text, headers."""
    conn = _connect(account)
    try:
        conn.select("INBOX", readonly=True)
        status, data = conn.fetch(uid.encode(), "(UID FLAGS RFC822)")
        if status != "OK" or not data or not data[0]:
            return None

        raw = data[0][1] if isinstance(data[0], tuple) else None
        if not raw:
            return None

        msg = email.message_from_bytes(raw)

        from_raw = _decode_header(msg.get("From", ""))
        from_name, from_addr = email.utils.parseaddr(from_raw)
        to_raw = _decode_header(msg.get("To", ""))
        subject = _decode_header(msg.get("Subject", ""))
        date_str = _parse_date(msg.get("Date", ""))

        # Extract body
        html_body = ""
        text_body = ""

        if msg.is_multipart():
            for part in msg.walk():
                ct = part.get_content_type()
                disp = str(part.get("Content-Disposition", ""))
                if "attachment" in disp:
                    continue
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="replace")
                if ct == "text/html":
                    html_body = decoded
                elif ct == "text/plain":
                    text_body = decoded
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                decoded = payload.decode(charset, errors="replace")
                if msg.get_content_type() == "text/html":
                    html_body = decoded
                else:
                    text_body = decoded

        return {
            "uid": uid,
            "from_name": from_name or from_addr,
            "from_email": from_addr,
            "to": to_raw,
            "subject": subject,
            "date": date_str,
            "html": html_body,
            "text": text_body,
        }
    finally:
        try:
            conn.close()
        except Exception:
            pass
        conn.logout()


def mark_message(account, uid, action):
    """Mark a message read or unread. action = 'read' | 'unread'."""
    conn = _connect(account)
    try:
        conn.select("INBOX")
        if action == "read":
            conn.store(uid.encode(), "+FLAGS", "\\Seen")
        elif action == "unread":
            conn.store(uid.encode(), "-FLAGS", "\\Seen")
    finally:
        try:
            conn.close()
        except Exception:
            pass
        conn.logout()


def delete_message(account, uid):
    """Delete a message by moving to Trash."""
    conn = _connect(account)
    try:
        conn.select("INBOX")
        # Try MOVE to Trash (some servers support it)
        try:
            conn.copy(uid.encode(), "Trash")
            conn.store(uid.encode(), "+FLAGS", "\\Deleted")
            conn.expunge()
        except Exception:
            # Fallback: just flag as deleted
            conn.store(uid.encode(), "+FLAGS", "\\Deleted")
            conn.expunge()
    finally:
        try:
            conn.close()
        except Exception:
            pass
        conn.logout()


def get_unread_counts():
    """Return {email: unread_count} for all tedca.online accounts."""
    accounts = get_tedca_accounts()
    counts = {}
    for acc in accounts:
        try:
            conn = _connect(acc)
            conn.select("INBOX", readonly=True)
            status, data = conn.search(None, "UNSEEN")
            if status == "OK" and data[0]:
                counts[acc["email"]] = len(data[0].split())
            else:
                counts[acc["email"]] = 0
            try:
                conn.close()
            except Exception:
                pass
            conn.logout()
        except Exception as e:
            print(f"[Inbox] Error checking {acc['email']}: {e}")
            counts[acc["email"]] = 0
    return counts


def check_new_emails():
    """Check for new unseen emails across all accounts.
    Returns list of new email dicts (for SSE publishing).
    """
    global _last_unseen
    accounts = get_tedca_accounts()
    new_emails = []

    for acc in accounts:
        addr = acc["email"]
        try:
            conn = _connect(acc)
            conn.select("INBOX", readonly=True)
            status, data = conn.search(None, "UNSEEN")
            current_uids = set(data[0].split()) if status == "OK" and data[0] else set()

            prev_uids = _last_unseen.get(addr, None)
            if prev_uids is not None:
                new_uids = current_uids - prev_uids
                if new_uids:
                    # Fetch headers for new messages
                    for uid in list(new_uids)[:5]:  # Cap at 5 per check
                        try:
                            status2, msg_data = conn.fetch(uid, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
                            if status2 == "OK" and msg_data and isinstance(msg_data[0], tuple):
                                msg = email.message_from_bytes(msg_data[0][1])
                                from_raw = _decode_header(msg.get("From", ""))
                                from_name, from_addr = email.utils.parseaddr(from_raw)
                                subject = _decode_header(msg.get("Subject", ""))
                                new_emails.append({
                                    "account": addr,
                                    "uid": uid.decode() if isinstance(uid, bytes) else uid,
                                    "from_name": from_name or from_addr,
                                    "from_email": from_addr,
                                    "subject": subject,
                                })
                        except Exception:
                            pass

            _last_unseen[addr] = current_uids
            try:
                conn.close()
            except Exception:
                pass
            conn.logout()
        except Exception as e:
            print(f"[Inbox] Poll error for {addr}: {e}")

    return new_emails
