"""Leads blueprint — GET /leads, GET /leads/<slug>"""

from flask import Blueprint, render_template, request
from services import supabase_client as db

leads_bp = Blueprint("leads", __name__)


@leads_bp.route("/leads")
def leads_list():
    tier = request.args.get("tier", "")
    status = request.args.get("status", "")
    search = request.args.get("search", "")
    sort_by = request.args.get("sort", "lead_score")
    sort_dir = request.args.get("dir", "desc")
    page = int(request.args.get("page", 1))

    try:
        leads, total = db.get_leads(
            tier=tier or None,
            status=status or None,
            search=search or None,
            sort_by=sort_by,
            sort_dir=sort_dir,
            page=page,
            per_page=50,
        )
    except Exception:
        leads, total = [], 0

    total_pages = max(1, (total + 49) // 50) if total else 1

    return render_template("leads.html",
                           leads=leads,
                           total=total,
                           page=page,
                           total_pages=total_pages,
                           tier=tier,
                           status=status,
                           search=search,
                           sort=sort_by,
                           dir=sort_dir)


@leads_bp.route("/leads/<slug>")
def lead_detail(slug):
    try:
        lead = db.get_lead_by_slug(slug)
        if not lead:
            return render_template("lead_detail.html", lead=None, error="Lead not found")

        emails = db.get_emails_for_lead(lead["id"])
        replies = db.get_replies_for_lead(lead["id"])
        spec_site = db.get_spec_site_by_lead(lead["id"])
        activity = db.get_activity_for_slug(slug, limit=50)
    except Exception as e:
        return render_template("lead_detail.html", lead=None, error=str(e))

    return render_template("lead_detail.html",
                           lead=lead,
                           emails=emails,
                           replies=replies,
                           spec_site=spec_site,
                           activity=activity,
                           error=None)
