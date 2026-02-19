// Pipeline page — SSE live monitor

let sseSource = null;
const agentTimers = {};

document.addEventListener('DOMContentLoaded', function() {
  connectSSE();
  // Update timers every second
  setInterval(updateTimers, 1000);
});

function connectSSE() {
  if (sseSource) sseSource.close();
  sseSource = new EventSource('/api/pipeline/stream');

  sseSource.addEventListener('agent_update', function(e) {
    const data = JSON.parse(e.data);
    updateAgentCard(data.agent, data);
  });

  sseSource.addEventListener('pipeline_log', function(e) {
    const data = JSON.parse(e.data);
    addLogEntry(data);
  });

  sseSource.addEventListener('pipeline_started', function(e) {
    const data = JSON.parse(e.data);
    showToast(`Pipeline started for ${data.slug}`, 'info');
    if (data.lead) {
      const el = document.getElementById('lead-company');
      if (el) el.textContent = data.lead.company_name || data.slug;
    }
  });

  sseSource.addEventListener('pipeline_completed', function(e) {
    showToast('Pipeline completed!', 'success');
  });

  sseSource.addEventListener('pipeline_failed', function(e) {
    const data = JSON.parse(e.data);
    showToast(`Pipeline failed: ${data.error}`, 'error');
  });

  sseSource.addEventListener('reply_detected', function(e) {
    const data = JSON.parse(e.data);
    showToast(`Reply detected: ${data.sentiment} from ${data.from}`, 'success');
  });

  sseSource.onerror = function() {
    setTimeout(connectSSE, 5000);
  };
}

function updateAgentCard(agent, data) {
  const card = document.getElementById(`card-${agent}`);
  if (!card) return;

  card.className = `agent-card ${data.status}`;

  const badge = card.querySelector('.badge');
  if (badge) {
    badge.className = `badge badge-${data.status}`;
    let label = data.status.charAt(0).toUpperCase() + data.status.slice(1);
    if (data.status === 'working') {
      badge.innerHTML = label + '<span class="dot-pulse"><span></span><span></span><span></span></span>';
    } else {
      badge.textContent = label;
    }
  }

  const task = card.querySelector('.agent-task');
  if (task) task.textContent = data.task || '\u2014';

  // Timer
  if (data.started_at) {
    agentTimers[agent] = { started_at: data.started_at, completed_at: data.completed_at || null };
  }

  // Completed tasks
  const cl = card.querySelector('.completed-list');
  if (cl && data.completed_tasks) {
    let html = '<div class="cl-label">Completed</div>';
    data.completed_tasks.forEach(t => {
      html += `<div class="completed-item">${t}</div>`;
    });
    cl.innerHTML = html;
  }
}

function updateTimers() {
  ['researcher', 'designer', 'judge', 'ops'].forEach(agent => {
    const timer = document.getElementById(`timer-${agent}`);
    if (!timer) return;
    const info = agentTimers[agent];
    if (!info || !info.started_at) {
      timer.textContent = '--:--';
      return;
    }
    const end = info.completed_at ? new Date(info.completed_at).getTime() : Date.now();
    const ms = end - new Date(info.started_at).getTime();
    const s = Math.floor(ms / 1000);
    const m = Math.floor(s / 60);
    timer.textContent = `${String(m).padStart(2, '0')}:${String(s % 60).padStart(2, '0')}`;
  });
}

function addLogEntry(entry) {
  const scroll = document.getElementById('log-scroll');
  if (!scroll) return;
  const div = document.createElement('div');
  div.className = 'log-entry';
  div.innerHTML = `<span class="log-time">${entry.time}</span><span class="log-agent ${entry.agent}">${entry.agent}</span><span class="log-msg">${entry.message}</span>`;
  scroll.appendChild(div);
  scroll.scrollTop = scroll.scrollHeight;
}

async function runNextLead() {
  const btn = document.getElementById('btn-run-next');
  if (btn) { btn.disabled = true; btn.textContent = 'Starting...'; }
  const data = await apiPost('/api/pipeline/run');
  if (data.ok) {
    showToast(`Pipeline started for ${data.slug}`, 'success');
    setTimeout(() => location.reload(), 1500);
  } else {
    showToast(data.error || 'Failed', 'error');
    if (btn) { btn.disabled = false; btn.textContent = 'Run Next Lead'; }
  }
}

async function runBatch() {
  const count = prompt('How many leads to process? (max 10)', '5');
  if (!count) return;
  const data = await apiPost('/api/pipeline/run-batch', { count: parseInt(count) });
  if (data.ok) {
    showToast(`Started ${data.started} pipeline runs`, 'success');
    setTimeout(() => location.reload(), 1500);
  } else {
    showToast(data.error || 'Failed', 'error');
  }
}
