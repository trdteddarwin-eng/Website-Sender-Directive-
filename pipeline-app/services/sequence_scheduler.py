"""APScheduler: checks replies every 5 min, checks due follow-ups every hour."""

import os
import sys
from datetime import date, datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services import supabase_client as db
from services.reply_checker import check_for_replies
from services.sse_manager import sse

_scheduler = None


def init_scheduler(app):
    """Initialize APScheduler with reply checking and follow-up jobs."""
    global _scheduler
    from apscheduler.schedulers.background import BackgroundScheduler

    _scheduler = BackgroundScheduler()

    @_scheduler.scheduled_job("interval", minutes=5, id="check_replies")
    def _check_replies():
        with app.app_context():
            try:
                new_replies = check_for_replies()
                for reply in new_replies:
                    sse.publish("reply_detected", {
                        "lead_id": reply.get("lead_id"),
                        "from": reply.get("from_email"),
                        "sentiment": reply.get("sentiment"),
                        "preview": reply.get("body_preview", "")[:100],
                    })
            except Exception as e:
                print(f"[Scheduler] Reply check error: {e}")

    @_scheduler.scheduled_job("interval", hours=1, id="check_followups")
    def _check_followups():
        with app.app_context():
            try:
                due = db.get_due_sequences(date.today().isoformat())
                if due:
                    sse.publish("followups_due", {
                        "count": len(due),
                        "slugs": [s.get("slug") for s in due],
                    })
            except Exception as e:
                print(f"[Scheduler] Follow-up check error: {e}")

    @_scheduler.scheduled_job("interval", seconds=30, id="check_inbox")
    def _check_inbox():
        with app.app_context():
            try:
                from services.inbox_service import check_new_emails
                new_emails = check_new_emails()
                for em in new_emails:
                    sse.publish("new_email", {
                        "account": em.get("account"),
                        "uid": em.get("uid"),
                        "from_name": em.get("from_name"),
                        "from_email": em.get("from_email"),
                        "subject": em.get("subject"),
                    })

                    # Auto-reply processing
                    try:
                        from services.auto_reply_service import process_new_email
                        result = process_new_email(
                            account_email=em.get("account"),
                            uid=em.get("uid"),
                            from_email=em.get("from_email"),
                            subject=em.get("subject"),
                        )
                        if result:
                            action = result.get("action", "")
                            if action == "sent":
                                sse.publish("auto_reply_sent", {
                                    "slug": result.get("slug", ""),
                                    "from_email": result.get("from_email", ""),
                                    "sentiment": result.get("sentiment", ""),
                                })
                            elif action == "draft":
                                sse.publish("auto_reply_drafted", {
                                    "slug": result.get("slug", ""),
                                    "from_email": result.get("from_email", ""),
                                    "sentiment": result.get("sentiment", ""),
                                })
                    except Exception as ae:
                        print(f"[Scheduler] Auto-reply error for {em.get('from_email')}: {ae}")
            except Exception as e:
                print(f"[Scheduler] Inbox check error: {e}")

    @_scheduler.scheduled_job("cron", hour=8, minute=0, id="generate_daily_queue")
    def _generate_daily_queue():
        with app.app_context():
            try:
                from services.daily_queue_service import generate_daily_queue
                items = generate_daily_queue(count=6)
                if items:
                    sse.publish("daily_queue_ready", {
                        "count": len(items),
                        "slugs": [i.get("slug") for i in items],
                    })
                    print(f"[Scheduler] Daily queue generated: {len(items)} leads")
            except Exception as e:
                print(f"[Scheduler] Daily queue generation error: {e}")

    _scheduler.start()
    print("[Scheduler] Started — reply check every 5min, follow-up check every 1hr, inbox check every 30s, daily queue at 8am")


def stop_scheduler():
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        print("[Scheduler] Stopped")
