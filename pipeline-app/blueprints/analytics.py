"""Analytics blueprint — GET /analytics."""

from flask import Blueprint, render_template
from services import supabase_client as db

analytics_bp = Blueprint("analytics", __name__)


@analytics_bp.route("/analytics")
def analytics_page():
    try:
        counts = db.get_lead_counts()
        email_stats = db.get_email_stats()
        reply_stats = db.get_reply_stats()
        throughput = db.get_pipeline_throughput(days=30)

        # Pipeline speed: average time from start to complete
        runs = db.get_recent_pipeline_runs(limit=100)
        completed_runs = [r for r in runs if r.get("status") == "completed" and r.get("started_at") and r.get("completed_at")]
        avg_minutes = 0
        if completed_runs:
            from datetime import datetime
            total_secs = 0
            for r in completed_runs:
                start = datetime.fromisoformat(r["started_at"].replace("Z", "+00:00"))
                end = datetime.fromisoformat(r["completed_at"].replace("Z", "+00:00"))
                total_secs += (end - start).total_seconds()
            avg_minutes = round(total_secs / len(completed_runs) / 60, 1)

    except Exception:
        counts = {"total": 0, "hot": 0, "warm": 0, "cold": 0, "pending": 0, "completed": 0, "processing": 0, "failed": 0}
        email_stats = {"total": 0, "sent": 0, "opened": 0, "replied": 0, "bounced": 0, "open_rate": 0, "reply_rate": 0, "bounce_rate": 0}
        reply_stats = {"total": 0, "positive": 0, "negative": 0, "neutral": 0, "out_of_office": 0}
        throughput = {}
        avg_minutes = 0

    return render_template("analytics.html",
                           counts=counts,
                           email_stats=email_stats,
                           reply_stats=reply_stats,
                           throughput=throughput,
                           avg_minutes=avg_minutes)
