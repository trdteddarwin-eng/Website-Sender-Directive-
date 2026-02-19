"""Inbox blueprint — GET /inbox, SSE stream for live email updates."""

from flask import Blueprint, render_template, Response
from services.sse_manager import sse
from services.inbox_service import get_tedca_accounts, get_unread_counts

inbox_bp = Blueprint("inbox", __name__)


@inbox_bp.route("/inbox")
def inbox_page():
    accounts = get_tedca_accounts()
    try:
        counts = get_unread_counts()
    except Exception:
        counts = {}
    return render_template("inbox.html", accounts=accounts, unread_counts=counts)


@inbox_bp.route("/inbox/stream")
def inbox_stream():
    q = sse.subscribe()
    return Response(sse.stream(q), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
