"""Pipeline runner — orchestrates execution scripts via subprocess."""

import os
import sys
import json
import subprocess
import threading
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config import WORKSPACE_ROOT, TMP_DIR, EXECUTION_DIR, PALETTES, HERO_STYLES, OPENROUTER_API_KEY
from services import supabase_client as db
from services.sse_manager import sse


class PipelineRunner:
    """Runs the full spec site pipeline for a single lead."""

    def __init__(self, lead, palette_index, hero_style_index, run_id):
        self.lead = lead
        self.slug = lead["slug"]
        self.palette_index = palette_index
        self.hero_style_index = hero_style_index
        self.run_id = run_id
        self.work_dir = os.path.join(TMP_DIR, self.slug)
        self._log_entries = []

    def _run_script(self, script_name, args, timeout=120):
        """Run an execution script and return (success, stdout, stderr)."""
        cmd = [sys.executable, os.path.join(EXECUTION_DIR, script_name)] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=timeout,
                cwd=WORKSPACE_ROOT,
                env={**os.environ, "PYTHONPATH": WORKSPACE_ROOT},
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", f"Timeout after {timeout}s"
        except Exception as e:
            return False, "", str(e)

    def _log(self, agent, message):
        """Log an activity entry and broadcast via SSE."""
        entry = {
            "time": datetime.utcnow().strftime("%H:%M:%S"),
            "agent": agent,
            "message": message,
        }
        self._log_entries.append(entry)
        sse.publish("pipeline_log", entry)

        # Also log to Supabase activity_log
        db.log_activity(
            lead_id=self.lead["id"], slug=self.slug,
            event_type="pipeline_step", agent=agent, message=message,
        )

    def _update_agent(self, agent, status, task="", completed_task=None):
        """Update agent status in the pipeline run and broadcast."""
        run = db.get_pipeline_run(self.run_id)
        if not run:
            return
        agents = run.get("agents", {})
        agent_data = agents.get(agent, {})
        agent_data["status"] = status
        agent_data["task"] = task
        if status == "working" and "started_at" not in agent_data:
            agent_data["started_at"] = datetime.utcnow().isoformat()
        if status == "done":
            agent_data["completed_at"] = datetime.utcnow().isoformat()
        if completed_task:
            tasks = agent_data.get("completed_tasks", [])
            tasks.append(completed_task)
            agent_data["completed_tasks"] = tasks
        agents[agent] = agent_data

        db.update_pipeline_run(self.run_id, {
            "agents": agents,
            "log": self._log_entries,
        })

        sse.publish("agent_update", {
            "agent": agent, "status": status, "task": task,
            "slug": self.slug, **agent_data,
        })

    def run(self):
        """Execute the full pipeline. Call from a background thread."""
        os.makedirs(self.work_dir, exist_ok=True)

        # Update lead status
        db.update_lead(self.slug, {"pipeline_status": "researching"})
        sse.publish("pipeline_started", {"slug": self.slug, "lead": self.lead})

        try:
            self._run_researcher()
            self._run_designer()
            self._run_judge()
            self._run_ops()

            db.update_pipeline_run(self.run_id, {
                "status": "completed",
                "completed_at": datetime.utcnow().isoformat(),
            })
            db.update_lead(self.slug, {"pipeline_status": "completed", "processed_at": datetime.utcnow().isoformat()})
            self._log("system", "Pipeline complete!")
            sse.publish("pipeline_completed", {"slug": self.slug})

        except Exception as e:
            db.update_pipeline_run(self.run_id, {"status": "failed"})
            db.update_lead(self.slug, {"pipeline_status": "failed"})
            self._log("system", f"Pipeline failed: {str(e)}")
            sse.publish("pipeline_failed", {"slug": self.slug, "error": str(e)})

    def _run_researcher(self):
        """Step 1: Research — scrape website, reviews, analyze, combine, screenshot."""
        self._update_agent("researcher", "working", "Scraping website")
        self._log("researcher", f"Starting research for {self.lead.get('company_name')}")

        website = self.lead.get("website", "")
        company = self.lead.get("company_name", "")
        city = self.lead.get("city", "")
        state = self.lead.get("state", "")

        # 1a: Scrape website
        website_out = os.path.join(self.work_dir, "website_data.json")
        if not os.path.exists(website_out) and website:
            ok, out, err = self._run_script("scrape_website_content.py", [
                "--url", website, "--max_pages", "5", "--output", website_out
            ], timeout=90)
            if ok:
                self._log("researcher", "Website scraped")
            else:
                self._log("researcher", f"Website scrape failed (using fallback): {err[:100]}")
                # Create fallback
                with open(website_out, "w") as f:
                    json.dump({"pages_scraped": 0, "url": website, "content": self.lead.get("company_description", "")}, f)
        self._update_agent("researcher", "working", "Scraping Google reviews", completed_task="Website scraped")

        # 1b: Scrape reviews
        reviews_out = os.path.join(self.work_dir, "reviews_data.json")
        if not os.path.exists(reviews_out):
            ok, out, err = self._run_script("scrape_google_reviews.py", [
                "--business_name", company, "--location", f"{city}, {state}",
                "--max_reviews", "10", "--output", reviews_out
            ], timeout=90)
            if ok:
                self._log("researcher", "Reviews scraped")
            else:
                self._log("researcher", f"Reviews scrape failed: {err[:100]}")
                with open(reviews_out, "w") as f:
                    json.dump({"reviews": [], "count": 0}, f)
        self._update_agent("researcher", "working", "Running AI analysis", completed_task="Reviews scraped")

        # 1c: AI analysis
        analysis_out = os.path.join(self.work_dir, "analysis.json")
        if not os.path.exists(analysis_out):
            ok, out, err = self._run_script("analyze_lead_for_roi.py", [
                "--website_data", website_out,
                "--reviews_data", reviews_out,
                "--company_name", company,
                "--output", analysis_out,
            ], timeout=60)
            if not ok:
                self._log("researcher", "AI analysis failed, creating fallback")
                with open(analysis_out, "w") as f:
                    json.dump({"pain_points": [], "roi_estimate": "", "needs_manual_analysis": True}, f)
        self._update_agent("researcher", "working", "Combining research", completed_task="Analysis complete")

        # 1d: Combine research
        research_out = os.path.join(self.work_dir, "research.json")
        if not os.path.exists(research_out):
            lead_json = json.dumps(self.lead)
            ok, out, err = self._run_script("combine_research.py", [
                "--lead_json", lead_json,
                "--website", website_out,
                "--reviews", reviews_out,
                "--analysis", analysis_out,
                "--output", research_out,
            ], timeout=30)
            if ok:
                self._log("researcher", "Research combined")
            else:
                self._log("researcher", f"Combine failed: {err[:100]}")
        self._update_agent("researcher", "working", "Screenshotting old site", completed_task="Research combined")

        # 1e: Screenshot old site
        old_screenshot = os.path.join(self.work_dir, "old-site.png")
        if not os.path.exists(old_screenshot) and website:
            ok, out, err = self._run_script("screenshot_website.py", [
                "--url", website, "--output", old_screenshot, "--compress"
            ], timeout=60)
            if ok:
                self._log("researcher", "Old site screenshot captured")
            else:
                self._log("researcher", "Old site screenshot failed (site may be down)")

        db.update_pipeline_run(self.run_id, {"research_path": research_out, "old_screenshot_path": old_screenshot})
        self._update_agent("researcher", "done", "", completed_task="Old site screenshot")
        self._log("researcher", "Research phase complete")

    def _run_designer(self):
        """Step 2: Generate spec site HTML via OpenRouter."""
        self._update_agent("designer", "working", "Generating spec site HTML")
        self._log("designer", "Starting spec site generation")
        db.update_lead(self.slug, {"pipeline_status": "designing"})

        html_out = os.path.join(self.work_dir, "index.html")
        research_path = os.path.join(self.work_dir, "research.json")

        if not os.path.exists(html_out):
            ok, out, err = self._run_script("generate_spec_site.py", [
                "--research", research_path,
                "--palette_index", str(self.palette_index),
                "--hero_style_index", str(self.hero_style_index),
                "--output", html_out,
            ], timeout=120)
            if ok:
                self._log("designer", "Spec site HTML generated")
            else:
                self._log("designer", f"Generation failed: {err[:200]}")
                raise RuntimeError(f"Spec site generation failed: {err[:200]}")

        db.update_pipeline_run(self.run_id, {"html_path": html_out})
        self._update_agent("designer", "done", "", completed_task="Spec site generated")
        self._log("designer", "Design phase complete")

    def _run_judge(self):
        """Step 3: Screenshot new site + programmatic check + Kimi K2.5 visual review."""
        self._update_agent("judge", "working", "Screenshotting new site")
        self._log("judge", "Starting evaluation")
        db.update_lead(self.slug, {"pipeline_status": "reviewing"})

        html_path = os.path.join(self.work_dir, "index.html")
        new_screenshot = os.path.join(self.work_dir, "new-site.png")
        research_path = os.path.join(self.work_dir, "research.json")

        # Screenshot the spec site
        if not os.path.exists(new_screenshot):
            file_url = f"file://{os.path.abspath(html_path)}"
            ok, out, err = self._run_script("screenshot_website.py", [
                "--url", file_url, "--output", new_screenshot, "--compress"
            ], timeout=60)
            if ok:
                self._log("judge", "New site screenshot captured")
            else:
                self._log("judge", f"Screenshot failed: {err[:100]}")
        self._update_agent("judge", "working", "Running programmatic checks", completed_task="Screenshot captured")

        # Programmatic quality check (structure)
        struct_score = self._quality_check(html_path)
        self._log("judge", f"Structure score: {struct_score}/100")
        self._update_agent("judge", "working", "Running K2.5 visual review", completed_task=f"Structure: {struct_score}/100")

        # Kimi K2.5 visual review (design quality)
        visual_score = -1
        visual_recommendation = "skipped"
        visual_review_path = os.path.join(self.work_dir, "visual-review.json")
        if os.path.exists(new_screenshot) and os.path.exists(research_path):
            ok, out, err = self._run_script("judge_visual_review.py", [
                "--screenshot", new_screenshot,
                "--research", research_path,
                "--output", visual_review_path,
            ], timeout=120)
            if ok and os.path.exists(visual_review_path):
                try:
                    with open(visual_review_path) as f:
                        vr = json.load(f)
                    visual_score = vr.get("visual_score", -1)
                    visual_recommendation = vr.get("recommendation", "unknown")
                    strengths = vr.get("strengths", [])
                    issues = vr.get("issues", [])
                    impression = vr.get("overall_impression", "")
                    self._log("judge", f"Visual score: {visual_score}/100 — {visual_recommendation}")
                    if impression:
                        self._log("judge", f"K2.5: {impression}")
                    for s in strengths[:2]:
                        self._log("judge", f"  + {s}")
                    for i in issues[:2]:
                        self._log("judge", f"  - {i}")
                except Exception as e:
                    self._log("judge", f"Visual review parse error: {e}")
            else:
                self._log("judge", f"Visual review failed: {err[:100] if err else 'unknown error'}")
        else:
            self._log("judge", "Skipped visual review (missing screenshot or research)")

        # Combined score: 40% structure + 60% visual (if available)
        if visual_score >= 0:
            combined_score = int(struct_score * 0.4 + visual_score * 0.6)
        else:
            combined_score = struct_score

        db.update_pipeline_run(self.run_id, {
            "judge_score": combined_score,
            "judge_struct_score": struct_score,
            "judge_visual_score": visual_score,
            "judge_visual_recommendation": visual_recommendation,
            "new_screenshot_path": new_screenshot,
        })
        self._log("judge", f"Combined score: {combined_score}/100 (struct={struct_score}, visual={visual_score})")

        self._update_agent("judge", "done", "", completed_task=f"Score: {combined_score}/100 ({visual_recommendation})")
        self._log("judge", "Evaluation complete")

    def _quality_check(self, html_path):
        """Programmatic HTML quality check. Returns score 0-100."""
        try:
            with open(html_path, "r") as f:
                html = f.read()
        except Exception:
            return 0

        score = 0
        checks = [
            (len(html) > 5000, 10, "File size > 5KB"),
            ("<meta name=\"viewport\"" in html, 10, "Responsive meta tag"),
            ("tel:" in html, 10, "Click-to-call phone link"),
            ("<nav" in html.lower(), 5, "Navigation element"),
            ("<footer" in html.lower(), 5, "Footer element"),
            ("@media" in html, 10, "Media queries (responsive)"),
            ("<script" in html.lower(), 5, "JavaScript (menu toggle)"),
            (html.lower().count("review") >= 2, 10, "Reviews section"),
            (html.lower().count("service") >= 2, 10, "Services section"),
            (self.lead.get("phone", "555") in html if self.lead.get("phone") else True, 10, "Correct phone number"),
            ("google" in html.lower() and "font" in html.lower(), 5, "Google Fonts"),
            ("emergency" in html.lower() or "24/7" in html.lower() or "call now" in html.lower(), 10, "Emergency CTA"),
        ]
        for check, points, label in checks:
            if check:
                score += points
        return min(score, 100)

    def _run_ops(self):
        """Step 4: Deploy, generate email, create drafts."""
        self._update_agent("ops", "working", "Deploying to Netlify")
        self._log("ops", "Starting ops phase")
        db.update_lead(self.slug, {"pipeline_status": "deploying"})

        html_path = os.path.join(self.work_dir, "index.html")
        research_path = os.path.join(self.work_dir, "research.json")
        deploy_info_path = os.path.join(self.work_dir, "deploy-info.json")

        # 4a: Deploy to Netlify
        deploy_url = ""
        if not os.path.exists(deploy_info_path):
            ok, out, err = self._run_script("deploy_spec_site.py", [
                "--html", html_path, "--slug", self.slug,
                "--output", deploy_info_path,
            ], timeout=60)
            if ok:
                self._log("ops", "Deployed to Netlify")
                try:
                    with open(deploy_info_path) as f:
                        deploy_info = json.load(f)
                    deploy_url = deploy_info.get("deploy_url", "")
                except Exception:
                    pass
            else:
                self._log("ops", f"Deploy failed: {err[:100]}")
        else:
            with open(deploy_info_path) as f:
                deploy_url = json.load(f).get("deploy_url", "")
        self._update_agent("ops", "working", "Generating outreach email", completed_task="Deployed to Netlify")

        # Save spec site to Supabase
        if deploy_url:
            db.create_spec_site({
                "lead_id": self.lead["id"],
                "slug": self.slug,
                "deploy_url": deploy_url,
                "judge_score": db.get_pipeline_run(self.run_id).get("judge_score"),
                "palette_index": self.palette_index,
                "hero_style": HERO_STYLES[self.hero_style_index],
                "html_path": html_path,
                "screenshot_path": os.path.join(self.work_dir, "new-site.png"),
            })

        db.update_lead(self.slug, {"pipeline_status": "emailing"})

        # 4b: Generate outreach email
        # Use compressed JPEG if available, fall back to PNG
        old_screenshot = os.path.join(self.work_dir, "old-site.jpg")
        if not os.path.exists(old_screenshot):
            old_screenshot = os.path.join(self.work_dir, "old-site.png")
        new_screenshot = os.path.join(self.work_dir, "new-site.jpg")
        if not os.path.exists(new_screenshot):
            new_screenshot = os.path.join(self.work_dir, "new-site.png")

        # Check if old screenshot is usable (not maintenance/error/login page)
        old_screenshot_usable = True
        old_meta_path = os.path.join(self.work_dir, "old-site.meta.json")
        if os.path.exists(old_meta_path):
            try:
                with open(old_meta_path) as f:
                    old_meta = json.load(f)
                old_screenshot_usable = old_meta.get("usable", True)
                if not old_screenshot_usable:
                    self._log("ops", f"Old site screenshot unusable ({old_meta.get('reason', 'unknown')}), skipping from email")
            except Exception:
                pass

        ok, out, err = self._run_script("generate_outreach_email.py", [
            "--company_data", research_path,
            "--old_screenshot", old_screenshot if old_screenshot_usable else "",
            "--new_screenshot", new_screenshot,
            "--output_dir", self.work_dir,
        ], timeout=60)
        if ok:
            self._log("ops", "Outreach email generated")
        else:
            self._log("ops", f"Email generation failed: {err[:100]}")
        self._update_agent("ops", "working", "Creating Gmail draft", completed_task="Email generated")

        # 4c: Create Gmail draft
        email_meta_path = os.path.join(self.work_dir, "email-meta.json")
        email_html_path = os.path.join(self.work_dir, "outreach-email.html")
        draft_id = ""
        thread_id = ""

        if os.path.exists(email_meta_path):
            with open(email_meta_path) as f:
                meta = json.load(f)

            to_email = meta.get("to", self.lead.get("email", ""))
            subject = meta.get("subject", "")

            if to_email and subject:
                attach_args = []
                if os.path.exists(old_screenshot) and old_screenshot_usable:
                    attach_args += ["--attach", f"{old_screenshot}:old-site-screenshot"]
                if os.path.exists(new_screenshot):
                    attach_args += ["--attach", f"{new_screenshot}:new-site-screenshot"]

                ok, out, err = self._run_script("create_gmail_draft.py", [
                    "--to", to_email, "--subject", subject,
                    "--html_file", email_html_path,
                ] + attach_args, timeout=30)
                if ok:
                    self._log("ops", f"Gmail draft created for {to_email}")
                    # Try to parse draft ID from output
                    for line in out.split("\n"):
                        if "Draft ID:" in line:
                            draft_id = line.split("Draft ID:")[-1].strip()
                else:
                    self._log("ops", f"Gmail draft failed: {err[:100]}")

                # Save email to Supabase
                html_content = ""
                if os.path.exists(email_html_path):
                    with open(email_html_path) as f:
                        html_content = f.read()

                db.create_email({
                    "lead_id": self.lead["id"],
                    "slug": self.slug,
                    "touchpoint": 1,
                    "subject": subject,
                    "html_content": html_content,
                    "html_path": email_html_path,
                    "status": "draft",
                    "gmail_draft_id": draft_id,
                })
        self._update_agent("ops", "working", "Generating follow-ups", completed_task="Gmail draft created")

        # 4d: Generate follow-up emails
        if deploy_url:
            ok, out, err = self._run_script("generate_followup_email.py", [
                "--research", research_path, "--all",
                "--spec_url", deploy_url,
                "--output_dir", self.work_dir,
            ], timeout=60)
            if ok:
                self._log("ops", "Follow-up emails generated")
                # Create email records for follow-ups
                for touch in [2, 3, 4]:
                    meta_path = os.path.join(self.work_dir, f"followup-touch{touch}-meta.json")
                    html_path_fu = os.path.join(self.work_dir, f"followup-touch{touch}.html")
                    if os.path.exists(meta_path):
                        with open(meta_path) as f:
                            fu_meta = json.load(f)
                        fu_html = ""
                        if os.path.exists(html_path_fu):
                            with open(html_path_fu) as f:
                                fu_html = f.read()
                        # Calculate send date
                        from datetime import timedelta
                        days_offset = {2: 3, 3: 7, 4: 14}[touch]
                        send_date = (datetime.utcnow() + timedelta(days=days_offset)).strftime("%Y-%m-%d")
                        db.create_email({
                            "lead_id": self.lead["id"],
                            "slug": self.slug,
                            "touchpoint": touch,
                            "subject": fu_meta.get("subject", ""),
                            "html_content": fu_html,
                            "html_path": html_path_fu,
                            "status": "draft",
                            "scheduled_send_date": send_date,
                        })
            else:
                self._log("ops", f"Follow-up generation failed: {err[:100]}")

        # Create email sequence
        from datetime import timedelta
        db.create_sequence({
            "lead_id": self.lead["id"],
            "slug": self.slug,
            "status": "active",
            "current_touchpoint": 1,
            "next_send_date": datetime.utcnow().strftime("%Y-%m-%d"),
            "spec_site_url": deploy_url,
        })

        self._update_agent("ops", "done", "", completed_task="Follow-ups created")
        self._log("ops", "Ops phase complete")


def start_pipeline(lead, palette_index=None, hero_style_index=None):
    """Start the pipeline for a lead in a background thread.

    Returns the pipeline_run dict.
    """
    # Calculate palette/hero if not provided
    completed_count = len(db.get_recent_pipeline_runs(limit=1000))
    if palette_index is None:
        palette_index = completed_count % len(PALETTES)
    if hero_style_index is None:
        hero_style_index = completed_count % len(HERO_STYLES)

    run = db.create_pipeline_run(lead["id"], lead["slug"], palette_index, hero_style_index)
    if not run:
        raise RuntimeError("Failed to create pipeline run")

    runner = PipelineRunner(lead, palette_index, hero_style_index, run["id"])

    thread = threading.Thread(target=runner.run, daemon=True)
    thread.start()

    return run
