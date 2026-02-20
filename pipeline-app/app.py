#!/usr/bin/env python3
"""TedCA Pipeline Web App — entry point."""

import os
import sys

# Ensure pipeline-app is on the path
sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask

from config import SECRET_KEY
from blueprints.dashboard import dashboard_bp
from blueprints.leads import leads_bp
from blueprints.pipeline import pipeline_bp
from blueprints.sequences import sequences_bp
from blueprints.analytics import analytics_bp
from blueprints.settings import settings_bp
from blueprints.api import api_bp
from blueprints.inbox import inbox_bp
from blueprints.drafts import drafts_bp


def create_app():
    app = Flask(__name__,
                template_folder="templates",
                static_folder="static")
    app.secret_key = SECRET_KEY or os.urandom(24)

    # Register blueprints
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(leads_bp)
    app.register_blueprint(pipeline_bp)
    app.register_blueprint(sequences_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(inbox_bp)
    app.register_blueprint(drafts_bp)

    # Start background scheduler
    try:
        from services.sequence_scheduler import init_scheduler
        init_scheduler(app)
    except Exception as e:
        print(f"[Warning] Scheduler init failed: {e}")

    return app


if __name__ == "__main__":
    app = create_app()
    port = int(os.environ.get("PORT", 5050))
    print(f"\n  TedCA Pipeline Dashboard")
    print(f"  http://localhost:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False)
