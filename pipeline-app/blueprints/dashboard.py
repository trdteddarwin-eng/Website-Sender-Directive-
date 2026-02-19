"""Dashboard blueprint — GET /"""

from flask import Blueprint, render_template
from services import supabase_client as db

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
def index():
    try:
        counts = db.get_lead_counts()
        email_stats = db.get_email_stats()
        recent_activity = db.get_recent_activity(limit=20)
        due_sequences = db.get_due_sequences()
        throughput = db.get_pipeline_throughput(days=30)
    except Exception as e:
        counts = {"total": 0, "hot": 0, "warm": 0, "cold": 0, "pending": 0, "completed": 0, "processing": 0, "failed": 0}
        email_stats = {"total": 0, "sent": 0, "opened": 0, "replied": 0, "bounced": 0, "open_rate": 0, "reply_rate": 0, "bounce_rate": 0}
        recent_activity = []
        due_sequences = []
        throughput = {}

    return render_template("dashboard.html",
                           counts=counts,
                           email_stats=email_stats,
                           activity=recent_activity,
                           due_sequences=due_sequences,
                           throughput=throughput)
