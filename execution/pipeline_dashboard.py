#!/usr/bin/env python3
"""Live pipeline dashboard server — serves at http://localhost:3000"""

import http.server
import json
import os
import socketserver

PORT = 3000
BASE_DIR = os.path.join(os.path.dirname(__file__), "..")
STATUS_FILE = os.path.join(BASE_DIR, ".tmp", "pipeline-status.json")
TMP_DIR = os.path.join(BASE_DIR, ".tmp")

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TedCA Pipeline Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{--bg:#0a0e1a;--card:#111827;--card-border:#1e293b;--text:#e2e8f0;--text-dim:#64748b;--accent:#d4922a;--accent-dim:#d4922a33;--blue:#3b82f6;--green:#22c55e;--red:#ef4444;--orange:#f59e0b;--navy:#0b1d3a}
body{font-family:'Inter',sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.container{max-width:1400px;margin:0 auto;padding:24px}
header{display:flex;align-items:center;justify-content:space-between;margin-bottom:32px;padding-bottom:16px;border-bottom:1px solid var(--card-border)}
.logo{display:flex;align-items:center;gap:12px}
.logo h1{font-size:20px;font-weight:700;color:var(--accent)}
.logo span{font-size:13px;color:var(--text-dim);font-weight:400}
.lead-info{text-align:right}
.lead-info .company{font-size:18px;font-weight:600}
.lead-info .contact{font-size:13px;color:var(--text-dim)}
.progress-bar-container{margin-bottom:28px}
.progress-label{display:flex;justify-content:space-between;margin-bottom:8px;font-size:13px;color:var(--text-dim)}
.progress-bar{height:6px;background:var(--card-border);border-radius:3px;overflow:hidden}
.progress-fill{height:100%;background:linear-gradient(90deg,var(--accent),var(--orange));border-radius:3px;transition:width .6s ease}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:28px}
@media(max-width:900px){.grid{grid-template-columns:1fr}}
.agent-card{background:var(--card);border:1px solid var(--card-border);border-radius:12px;padding:20px;position:relative;overflow:hidden}
.agent-card::before{content:'';position:absolute;top:0;left:0;right:0;height:3px}
.agent-card.waiting::before{background:var(--text-dim)}
.agent-card.working::before{background:var(--blue);animation:pulse 2s infinite}
.agent-card.done::before{background:var(--green)}
.agent-card.error::before{background:var(--red)}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
.agent-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}
.agent-name{font-size:15px;font-weight:600;text-transform:uppercase;letter-spacing:.5px}
.status-badge{font-size:11px;font-weight:600;padding:3px 10px;border-radius:20px;text-transform:uppercase;letter-spacing:.5px}
.status-badge.waiting{background:#64748b22;color:#94a3b8}
.status-badge.working{background:#3b82f622;color:#60a5fa}
.status-badge.done{background:#22c55e22;color:#4ade80}
.status-badge.error{background:#ef444422;color:#f87171}
.agent-task{font-size:13px;color:var(--text);margin-bottom:10px;min-height:20px}
.agent-timer{font-family:'JetBrains Mono',monospace;font-size:22px;font-weight:500;color:var(--accent);margin-bottom:12px}
.completed-list{border-top:1px solid var(--card-border);padding-top:10px;margin-top:4px}
.completed-list .label{font-size:11px;color:var(--text-dim);text-transform:uppercase;letter-spacing:.5px;margin-bottom:6px}
.completed-item{font-size:12px;color:#94a3b8;padding:2px 0;display:flex;align-items:center;gap:6px}
.completed-item::before{content:'✓';color:var(--green);font-size:10px}
.bottom-grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}
@media(max-width:900px){.bottom-grid{grid-template-columns:1fr}}
.log-panel{background:var(--card);border:1px solid var(--card-border);border-radius:12px;padding:20px;max-height:360px;display:flex;flex-direction:column}
.panel-title{font-size:14px;font-weight:600;margin-bottom:12px;color:var(--accent)}
.log-scroll{flex:1;overflow-y:auto;font-family:'JetBrains Mono',monospace;font-size:12px}
.log-entry{padding:4px 0;display:flex;gap:10px;border-bottom:1px solid #1e293b22}
.log-time{color:var(--text-dim);white-space:nowrap}
.log-agent{font-weight:600;min-width:80px}
.log-agent.researcher{color:#a78bfa}
.log-agent.designer{color:#f472b6}
.log-agent.judge{color:#fbbf24}
.log-agent.ops{color:#34d399}
.log-msg{color:#cbd5e1}
.preview-panel{background:var(--card);border:1px solid var(--card-border);border-radius:12px;padding:20px;display:flex;flex-direction:column}
.preview-iframe{flex:1;border:1px solid var(--card-border);border-radius:8px;background:#fff;min-height:280px}
.preview-placeholder{flex:1;display:flex;align-items:center;justify-content:center;color:var(--text-dim);font-size:14px;border:1px dashed var(--card-border);border-radius:8px;min-height:280px}
.dot-pulse{display:inline-flex;gap:4px;margin-left:8px}
.dot-pulse span{width:6px;height:6px;border-radius:50%;background:var(--blue);animation:dotPulse 1.4s infinite}
.dot-pulse span:nth-child(2){animation-delay:.2s}
.dot-pulse span:nth-child(3){animation-delay:.4s}
@keyframes dotPulse{0%,80%,100%{opacity:.3;transform:scale(.8)}40%{opacity:1;transform:scale(1)}}
</style>
</head>
<body>
<div class="container">
  <header>
    <div class="logo">
      <h1>TedCA Pipeline</h1>
      <span>Live Agent Dashboard</span>
    </div>
    <div class="lead-info">
      <div class="company" id="lead-company">Loading...</div>
      <div class="contact" id="lead-contact"></div>
    </div>
  </header>
  <div class="progress-bar-container">
    <div class="progress-label">
      <span>Pipeline Progress</span>
      <span id="progress-text">0 / 4 agents complete</span>
    </div>
    <div class="progress-bar"><div class="progress-fill" id="progress-fill" style="width:0%"></div></div>
  </div>
  <div class="grid" id="agents-grid"></div>
  <div class="bottom-grid">
    <div class="log-panel">
      <div class="panel-title">Activity Log</div>
      <div class="log-scroll" id="log-scroll"></div>
    </div>
    <div class="preview-panel">
      <div class="panel-title">Spec Site Preview</div>
      <div id="preview-container"><div class="preview-placeholder">Waiting for Designer to build spec site...</div></div>
    </div>
  </div>
</div>
<script>
const AGENTS = ['researcher','designer','judge','ops'];
const AGENT_ICONS = {researcher:'🔍',designer:'🎨',judge:'⚖️',ops:'🚀'};
const POLL_MS = 2000;
let timers = {};
let prevLog = 0;

function formatElapsed(startISO) {
  if (!startISO) return '--:--';
  const ms = Date.now() - new Date(startISO).getTime();
  const s = Math.floor(ms/1000);
  const m = Math.floor(s/60);
  const sec = s%60;
  return `${String(m).padStart(2,'0')}:${String(sec).padStart(2,'0')}`;
}

function buildCards() {
  const grid = document.getElementById('agents-grid');
  grid.innerHTML = '';
  AGENTS.forEach(name => {
    grid.innerHTML += `
      <div class="agent-card waiting" id="card-${name}">
        <div class="agent-header">
          <div class="agent-name">${AGENT_ICONS[name]} ${name}</div>
          <div class="status-badge waiting" id="badge-${name}">Waiting</div>
        </div>
        <div class="agent-task" id="task-${name}">—</div>
        <div class="agent-timer" id="timer-${name}">--:--</div>
        <div class="completed-list" id="completed-${name}">
          <div class="label">Completed</div>
        </div>
      </div>`;
  });
}

function updateUI(data) {
  // Lead info
  if (data.lead) {
    document.getElementById('lead-company').textContent = data.lead.company || 'Unknown';
    document.getElementById('lead-contact').textContent = (data.lead.contact||'') + (data.lead.slug ? ` • ${data.lead.slug}` : '');
  }
  // Agents
  let doneCount = 0;
  AGENTS.forEach(name => {
    const a = data.agents?.[name] || {status:'waiting'};
    const card = document.getElementById('card-'+name);
    const badge = document.getElementById('badge-'+name);
    const taskEl = document.getElementById('task-'+name);
    const timerEl = document.getElementById('timer-'+name);
    const compEl = document.getElementById('completed-'+name);
    card.className = 'agent-card ' + a.status;
    badge.className = 'status-badge ' + a.status;
    badge.textContent = a.status.charAt(0).toUpperCase()+a.status.slice(1);
    if (a.status === 'working') {
      badge.innerHTML = a.status.charAt(0).toUpperCase()+a.status.slice(1) + '<span class="dot-pulse"><span></span><span></span><span></span></span>';
    }
    taskEl.textContent = a.task || '—';
    // Timer
    if (a.status === 'done' && a.started_at && a.completed_at) {
      timerEl.textContent = formatElapsed(a.started_at).replace(/.*/, () => {
        const ms = new Date(a.completed_at).getTime() - new Date(a.started_at).getTime();
        const s = Math.floor(ms/1000); const m = Math.floor(s/60);
        return `${String(m).padStart(2,'0')}:${String(s%60).padStart(2,'0')}`;
      });
      doneCount++;
    } else if (a.status === 'working' && a.started_at) {
      timerEl.textContent = formatElapsed(a.started_at);
    } else {
      timerEl.textContent = '--:--';
    }
    // Completed tasks
    const tasks = a.completed_tasks || [];
    let compHTML = '<div class="label">Completed</div>';
    tasks.forEach(t => { compHTML += `<div class="completed-item">${t}</div>`; });
    compEl.innerHTML = compHTML;
  });
  // Progress
  const pct = Math.round((doneCount/4)*100);
  document.getElementById('progress-fill').style.width = pct+'%';
  document.getElementById('progress-text').textContent = `${doneCount} / 4 agents complete`;
  // Log
  const logEl = document.getElementById('log-scroll');
  const entries = data.log || [];
  if (entries.length > prevLog) {
    entries.slice(prevLog).forEach(e => {
      const div = document.createElement('div');
      div.className = 'log-entry';
      div.innerHTML = `<span class="log-time">${e.time}</span><span class="log-agent ${e.agent}">${e.agent}</span><span class="log-msg">${e.message}</span>`;
      logEl.appendChild(div);
    });
    logEl.scrollTop = logEl.scrollHeight;
    prevLog = entries.length;
  }
  // Preview
  const slug = data.lead?.slug;
  if (slug) {
    const container = document.getElementById('preview-container');
    const exists = container.querySelector('iframe');
    if (!exists) {
      // Check if index.html is ready by looking at designer status
      const designer = data.agents?.designer;
      if (designer && (designer.status === 'done' || (designer.completed_tasks||[]).length > 0)) {
        container.innerHTML = `<iframe class="preview-iframe" src="/preview/${slug}/index.html" style="width:100%;border:none"></iframe>`;
      }
    }
  }
}

function tick() {
  const data = window._lastData;
  if (!data) return;
  AGENTS.forEach(name => {
    const a = data.agents?.[name];
    if (a && a.status === 'working' && a.started_at) {
      const el = document.getElementById('timer-'+name);
      if (el) el.textContent = formatElapsed(a.started_at);
    }
  });
}

async function poll() {
  try {
    const res = await fetch('/api/status');
    if (res.ok) {
      const data = await res.json();
      window._lastData = data;
      updateUI(data);
    }
  } catch(e) {}
}

buildCards();
poll();
setInterval(poll, POLL_MS);
setInterval(tick, 1000);
</script>
</body>
</html>"""


class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(DASHBOARD_HTML.encode())
        elif self.path == "/api/status":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                with open(STATUS_FILE) as f:
                    data = f.read()
            except FileNotFoundError:
                data = json.dumps({"lead": {}, "agents": {}, "log": []})
            self.wfile.write(data.encode())
        elif self.path.startswith("/preview/"):
            # Serve files from .tmp/ for preview
            rel = self.path.replace("/preview/", "", 1)
            fpath = os.path.join(TMP_DIR, rel)
            if os.path.isfile(fpath):
                self.send_response(200)
                if fpath.endswith(".html"):
                    self.send_header("Content-Type", "text/html; charset=utf-8")
                elif fpath.endswith(".png"):
                    self.send_header("Content-Type", "image/png")
                elif fpath.endswith(".json"):
                    self.send_header("Content-Type", "application/json")
                else:
                    self.send_header("Content-Type", "application/octet-stream")
                self.end_headers()
                with open(fpath, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404)
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        pass  # Suppress request logs


def main():
    with socketserver.TCPServer(("", PORT), DashboardHandler) as httpd:
        print(f"Dashboard running at http://localhost:{PORT}")
        print(f"Reading status from {STATUS_FILE}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down dashboard.")


if __name__ == "__main__":
    main()
