// TedCA Pipeline — Core JS

// Toast notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toasts');
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 5000);
}

// Modal
function openModal(html) {
  const overlay = document.getElementById('modal-overlay');
  const content = document.getElementById('modal-content');
  content.innerHTML = html;
  overlay.classList.add('active');
}

function closeModal() {
  document.getElementById('modal-overlay').classList.remove('active');
}

document.getElementById('modal-overlay')?.addEventListener('click', function(e) {
  if (e.target === this) closeModal();
});

// API helpers
async function apiPost(url, data = {}) {
  const resp = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return resp.json();
}

async function apiGet(url) {
  const resp = await fetch(url);
  return resp.json();
}

// Email actions (used across multiple pages)
async function previewEmail(emailId) {
  const data = await apiGet(`/api/emails/${emailId}/preview`);
  if (data.error) { showToast(data.error, 'error'); return; }
  openModal(`
    <div class="modal-title">
      <span>Touch ${data.touchpoint}: ${data.subject}</span>
      <button class="modal-close" onclick="closeModal()">&times;</button>
    </div>
    <div style="background: #fff; border-radius: 8px; padding: 16px; color: #1a1a1a; max-height: 60vh; overflow-y: auto;">
      ${data.html || '<p>No content</p>'}
    </div>
    <div style="margin-top: 16px; display: flex; gap: 8px; justify-content: flex-end;">
      <button class="btn btn-ghost" onclick="closeModal()">Close</button>
      ${data.status === 'draft' || data.status === 'ready' ? `<button class="btn btn-primary" onclick="sendEmail('${emailId}')">Send</button>` : ''}
    </div>
  `);
}

async function sendEmail(emailId) {
  if (!confirm('Send this email now?')) return;
  const data = await apiPost(`/api/emails/${emailId}/send`);
  if (data.ok) {
    showToast('Email sent!', 'success');
    closeModal();
    setTimeout(() => location.reload(), 1000);
  } else {
    showToast(data.error || 'Send failed', 'error');
  }
}

// Format relative time
function timeAgo(dateStr) {
  if (!dateStr) return '';
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return 'just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}
