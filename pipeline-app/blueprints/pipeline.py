"""Pipeline blueprint — GET /pipeline, live agent monitor."""

from flask import Blueprint, render_template, Response
from services import supabase_client as db
from services.sse_manager import sse

pipeline_bp = Blueprint("pipeline", __name__)


@pipeline_bp.route("/pipeline")
def pipeline_page():
    try:
        active_run = db.get_active_pipeline_run()
        recent_runs = db.get_recent_pipeline_runs(limit=5)
        next_lead = db.get_next_unprocessed_lead()
        queue_leads, _ = db.get_leads(tier="hot", status="pending", sort_by="lead_score", sort_dir="desc", page=1, per_page=5)
    except Exception:
        active_run = None
        recent_runs = []
        next_lead = None
        queue_leads = []

    return render_template("pipeline.html",
                           active_run=active_run,
                           recent_runs=recent_runs,
                           next_lead=next_lead,
                           queue_leads=queue_leads)


@pipeline_bp.route("/api/pipeline/stream")
def pipeline_stream():
    """SSE endpoint for live pipeline updates."""
    client_queue = sse.subscribe()

    def generate():
        yield from sse.stream(client_queue)

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
